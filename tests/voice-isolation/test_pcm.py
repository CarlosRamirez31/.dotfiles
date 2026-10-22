"""Exercise real producer/consumer boundaries without opening an audio device."""
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import threading
import time
import unittest
from unittest.mock import patch

path = Path(__file__).resolve().parents[2] / 'bin/dotfiles-microphone'
loader = importlib.machinery.SourceFileLoader('pcm_microphone', str(path))
spec = importlib.util.spec_from_loader(loader.name, loader)
m = importlib.util.module_from_spec(spec)
loader.exec_module(m)


class PcmTransport(unittest.TestCase):
    def test_native_output_keeps_frame_duration_and_gate_decisions(self):
        import array
        with patch.object(m.PcmOutput, '_write'):
            playback = m.PcmOutput(None, rate=48000)
            playback.thread.join(timeout=2)
        gate = m.VoiceGate(rate=48000)
        samples = array.array('h', [1000] * 7680)
        raw = gate.process(samples, 0.9)
        captured = time.monotonic()
        playback.write_block(captured, raw)
        frames = list(playback.frames.queue)
        self.assertEqual(len(frames), 16)
        self.assertTrue(all(len(frame[2]) == 960 for frame in frames))
        self.assertAlmostEqual(frames[-1][1] - frames[0][1], 0.15)
        self.assertEqual(b''.join(frame[2] for frame in frames), raw)
        self.assertEqual(gate.process(samples, 0.1), bytes(15360))

    def test_underrun_silence_and_speech_share_one_realtime_clock(self):
        class Writer:
            count = 0
            def write(self, raw):
                self.count += len(raw)
                return len(raw)
        writer = Writer()
        started = time.monotonic()
        playback = m.PcmOutput(writer)
        try:
            for _ in range(3):
                playback.write_block(time.monotonic(), bytes(5120))
                time.sleep(0.16)
        finally:
            playback.stopped.set()
            playback.thread.join(timeout=2)
        elapsed = time.monotonic() - started
        self.assertIsNone(playback.error)
        self.assertLessEqual(writer.count / (m.PCM_RATE * 2), elapsed + 0.03)

    def input_pipe(self):
        read_fd, write_fd = os.pipe()
        source = os.fdopen(read_fd, 'rb', buffering=0)
        writer = os.fdopen(write_fd, 'wb', buffering=0)
        capture = m.PcmInput(source)
        def cleanup():
            capture.stopped.set()
            writer.close()
            capture.thread.join(timeout=2)
            source.close()
            self.assertFalse(capture.thread.is_alive())
        self.addCleanup(cleanup)
        return capture, writer

    def test_fragmented_reads_preserve_frame_order_and_matching_block(self):
        capture, writer = self.input_pipe()
        block = b''.join(bytes([i]) * m.PCM_FRAME_BYTES for i in range(16))
        for offset in range(0, len(block), 53):
            m.write_exact(writer, block[offset:offset + 53])
        sequence, captured, actual = capture.read_block()
        self.assertEqual(sequence, 0)
        self.assertEqual(actual, block)
        self.assertLess(time.monotonic() - captured, m.PCM_MAX_AGE_SECONDS)

    def test_capture_overflow_stops_instead_of_replaying_queued_audio(self):
        capture, writer = self.input_pipe()
        # A small capacity guarantees overflow without filling the OS pipe.
        capture.frames = m.queue.Queue(maxsize=2)
        m.write_exact(writer, bytes(m.PCM_FRAME_BYTES * 4))
        capture.thread.join(timeout=2)
        self.assertFalse(capture.thread.is_alive())
        with self.assertRaisesRegex(RuntimeError, 'acumuló'):
            capture.read_block()
        self.assertEqual(capture.frames.qsize(), 2)

    def test_output_preserves_audio_and_silences_underrun(self):
        written = []
        delivered = threading.Event()
        silent = threading.Event()
        block = b'\x01\x02' * (m.PCM_FRAME_BYTES // 2)
        class Writer:
            def write(self, raw):
                raw = bytes(raw)
                written.append(raw)
                if raw == block:
                    delivered.set()
                elif raw == bytes(m.PCM_FRAME_BYTES):
                    silent.set()
                return len(raw)
        playback = m.PcmOutput(Writer())
        try:
            playback.write_block(time.monotonic(), block)
            self.assertTrue(delivered.wait(timeout=2))
            self.assertTrue(silent.wait(timeout=2))
            self.assertEqual([part for part in written if any(part)], [block])
            self.assertIsNone(playback.error)
        finally:
            playback.stopped.set()
            playback.thread.join(timeout=2)

    def test_late_result_is_never_enqueued(self):
        # Hold the consumer before it can remove queued frames.
        with patch.object(m.PcmOutput, '_write'):
            playback = m.PcmOutput(None)
            playback.thread.join(timeout=2)
        with self.assertRaisesRegex(RuntimeError, 'atrasada'):
            playback.write_block(time.monotonic() - 1, bytes(5120))
        self.assertTrue(playback.frames.empty())

    def test_output_overflow_is_bounded(self):
        with patch.object(m.PcmOutput, '_write'):
            playback = m.PcmOutput(None)
            playback.thread.join(timeout=2)
        now = time.monotonic()
        playback.write_block(now, bytes(5120))
        playback.write_block(now, bytes(5120))
        with self.assertRaisesRegex(RuntimeError, 'saturada'):
            playback.write_block(now, bytes(5120))
        self.assertEqual(playback.frames.qsize(), m.PCM_QUEUE_FRAMES)

    def test_late_pending_audio_is_replaced_with_silence(self):
        with patch.object(m.PcmOutput, '_write'):
            playback = m.PcmOutput(None)
            playback.thread.join(timeout=2)
        written = []
        class Writer:
            def write(self, raw):
                written.append(bytes(raw))
                return len(raw)
        playback.stream = Writer()
        playback.frames.put((playback.generation, time.monotonic() - 1, b'\x01\x02' * 160))
        playback._write()
        self.assertIsInstance(playback.error, RuntimeError)
        self.assertEqual(written, [bytes(m.PCM_FRAME_BYTES)])

    def test_changing_profile_invalidates_pending_generation(self):
        with patch.object(m.PcmOutput, '_write'):
            playback = m.PcmOutput(None)
            playback.thread.join(timeout=2)
        playback.write_block(time.monotonic(), b'\x01\x02' * 2560)
        old_generation = playback.generation
        playback.reset()
        self.assertTrue(playback.frames.empty())
        self.assertNotEqual(old_generation, playback.generation)
        written = []
        class Writer:
            def write(self, raw):
                written.append(bytes(raw))
                playback.stopped.set()
                return len(raw)
        playback.stream = Writer()
        # A frame already removed by the writer before reset also becomes invalid.
        playback.frames.put((old_generation, time.monotonic(), b'\x01\x02' * 160))
        playback._write()
        self.assertEqual(written, [bytes(m.PCM_FRAME_BYTES)])


if __name__ == '__main__':
    unittest.main()
