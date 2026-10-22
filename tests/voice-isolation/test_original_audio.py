import importlib.util
from collections import deque
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

try:
    import numpy as np
except ModuleNotFoundError:
    np = None

REPO = Path(__file__).resolve().parents[2]
COMPONENT = REPO / "setup/modules/voice-isolation"
if np is not None:
    spec = importlib.util.spec_from_file_location('original_audio', REPO / 'libexec/dotfiles-personal-audio.py')
    a = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(a)

import importlib.machinery
loader = importlib.machinery.SourceFileLoader('original_microphone', str(REPO / 'bin/dotfiles-microphone'))
spec = importlib.util.spec_from_loader(loader.name, loader)
m = importlib.util.module_from_spec(spec)
loader.exec_module(m)


@unittest.skipIf(np is None, 'Requires numpy in the private voice runtime')
class OriginalAudio(unittest.TestCase):
    def test_native_denoiser_does_not_flatten_float_headroom(self):
        received = []
        def process(state, output, samples):
            values = np.ctypeslib.as_array(samples, shape=(480,))
            received.append(values.copy())
            np.ctypeslib.as_array(output, shape=(480,))[:] = values * 0.5
            return 0.9
        reducer = object.__new__(a.NoiseReducer)
        reducer.state = 1
        reducer.library = SimpleNamespace(rnnoise_process_frame=process)
        samples = np.linspace(-1.6, 1.6, 480, dtype=np.float32)
        result = reducer.process(samples)
        self.assertGreater(float(np.max(received[0])), 32768)
        np.testing.assert_array_equal(result, samples * 0.5)

    def test_profile_gain_changes_recognition_but_not_native_noise_processing(self):
        class NonlinearNoise:
            delay_samples = 480
            def process(self, values):
                return (values * values * values).astype(np.float32)
            def close(self):
                pass
        first = a.PersonalAudio(0.5, 0.8, NonlinearNoise(), fullband=True)
        second = a.PersonalAudio(0.25, 0.8, NonlinearNoise(), fullband=True)
        values = np.linspace(-1.2, 1.2, 960, dtype='<f4')
        left, right = [], []
        for offset in range(0, len(values), 480):
            raw = values[offset:offset + 480].tobytes()
            left.append(first.process(raw))
            right.append(second.process(raw))
        left = np.frombuffer(b''.join(left), dtype='<f4').reshape(-1, 4)
        right = np.frombuffer(b''.join(right), dtype='<f4').reshape(-1, 4)
        np.testing.assert_array_equal(left[:, 1:], right[:, 1:])
        np.testing.assert_allclose(left[:, 0], right[:, 0] * 2, atol=1e-7)
        np.testing.assert_allclose(left[:, 1:].reshape(-1), values ** 3 * 0.8, atol=1e-7)
        self.assertGreater(first.levels['input_peak'], 1)
        self.assertGreater(first.levels['output_over_range_samples'], 0)
        self.assertEqual(first.levels['output_samples'], 960)
        first.close()
        second.close()

    def test_fullband_output_preserves_native_samples_and_recognition(self):
        class DelayedNoise:
            delay_samples = 480
            def __init__(self):
                self.previous = np.zeros(480, dtype=np.float32)
            def process(self, values):
                result, self.previous = self.previous, values.copy()
                return result
            def close(self):
                pass
        t = np.arange(4800) / 48000
        values = (0.1 * np.sin(2 * np.pi * 700 * t) +
                  0.2 * np.sin(2 * np.pi * 12000 * t)).astype('<f4')
        legacy = a.PersonalAudio(0.5, 0.25, DelayedNoise())
        fullband = a.PersonalAudio(0.5, 0.25, DelayedNoise(), fullband=True)
        old, new = [], []
        for offset in range(0, len(values), 480):
            raw = values[offset:offset + 480].tobytes()
            old.append(legacy.process(raw))
            new.append(fullband.process(raw))
        old = np.frombuffer(b''.join(old), dtype='<f4').reshape(-1, 2)
        new = np.frombuffer(b''.join(new), dtype='<f4').reshape(-1, 4)
        np.testing.assert_array_equal(new[:, 0], old[:, 0])
        output = new[:, 1:].reshape(-1)
        self.assertEqual(len(output), len(values))
        np.testing.assert_allclose(output, np.concatenate((np.zeros(480), values[:-480])) * 0.25,
                                   rtol=1e-6, atol=1e-8)
        legacy.close()
        fullband.close()

    def test_original_and_cleaned_columns_are_paired_after_frame_delay(self):
        class DelayedNoise:
            def __init__(self, frames):
                self.delay_samples = 480 * frames
                self.previous = deque(np.zeros(480, dtype=np.float32) for _ in range(frames))
            def process(self, values):
                result = self.previous.popleft()
                self.previous.append(values.copy())
                return result
            def close(self):
                pass
        values = (1.6 * np.sin(np.arange(4800) * 2 * np.pi * 700 / 48000)).astype('<f4')
        for frames in (1, 2):
            with self.subTest(delay_frames=frames):
                processor = a.PersonalAudio(0.5, 0.25, DelayedNoise(frames))
                blocks = [processor.process(values[offset:offset + 480].tobytes()) for offset in range(0, len(values), 480)]
                pair = np.frombuffer(b''.join(blocks), dtype='<f4').reshape(-1, 2)
                self.assertEqual(pair.shape, (1600, 2))
                self.assertEqual(processor.delay_seconds, frames * 0.01)
                np.testing.assert_allclose(pair[:, 1], pair[:, 0] * (0.25 / 0.5), rtol=1e-6, atol=1e-7)
                self.assertGreater(float(np.max(np.abs(pair[:, 0]))), 0.7)
                self.assertLess(float(np.max(np.abs(pair[:, 0]))), 0.9)
                processor.close()

    def test_resampling_removes_aliasing_and_keeps_state_between_frames(self):
        t = np.arange(4800) / 48000
        def resample(values):
            downsample = a.Downsample()
            return np.concatenate([downsample.process(values[start:start + 480]) for start in range(0, len(values), 480)])[160:]
        low = resample(np.sin(2 * np.pi * 1000 * t))
        high = resample(np.sin(2 * np.pi * 12000 * t))
        self.assertGreater(float(np.sqrt(np.mean(low ** 2))), 0.6)
        self.assertLess(float(np.sqrt(np.mean(high ** 2))), 0.02)
        constant = resample(np.full(4800, 0.03, dtype=np.float32))
        np.testing.assert_allclose(constant, 0.03, atol=1e-6)

    def test_enrollment_preserves_float_headroom_and_rejects_flattened_audio(self):
        values = np.linspace(-1.6, 1.6, 240000, dtype=np.float32)
        normalized, gain = a.prepare_enrollment(values)
        self.assertLess(gain, 1)
        self.assertGreater(float(np.max(values)), 1)
        self.assertLessEqual(float(np.max(normalized)), 0.900001)
        with self.assertRaisesRegex(ValueError, 'picos recortados'):
            a.prepare_enrollment(np.clip(values, -1, 1))

    def test_bad_profile_gain_never_starts_noise_processing(self):
        with patch.object(a, 'NoiseReducer') as native:
            for gain in (None, 0, 2, float('nan'), True):
                with self.assertRaises(ValueError):
                    a.PersonalAudio(gain)
            native.assert_not_called()

    def test_native_noise_library_validates_input_and_closes_idempotently(self):
        try:
            path = a.rnnoise_path()
        except RuntimeError:
            self.skipTest('RNNoise library is not installed')
        noise = a.NoiseReducer(path)
        try:
            self.assertIn(noise.delay_samples, (480, 960, 1440))
            for _ in range(4):
                result = noise.process(np.zeros(480, dtype=np.float32))
                self.assertEqual(result.shape, (480,))
                self.assertTrue(np.isfinite(result).all())
                self.assertLess(float(np.max(np.abs(result))), 1e-7)
            with self.assertRaises(ValueError):
                noise.process(np.zeros(479, dtype=np.float32))
            with self.assertRaises(ValueError):
                noise.process(np.full(480, np.nan, dtype=np.float32))
        finally:
            noise.close()
            noise.close()

    def test_registering_original_profile_preserves_previous_embedding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / 'data'
            data.mkdir()
            old = data / 'old.npy'
            old.write_bytes(b'previous-profile-untouched')
            samples = (1.3 * np.sin(np.arange(240000) * 2 * np.pi * 180 / 16000)).astype('<f4')
            capture = Mock(stdout=io.BytesIO(samples.tobytes()))
            embedding = np.ones((1, 192), dtype=np.float32) / np.sqrt(192)
            model = SimpleNamespace(extract_emb=lambda _: SimpleNamespace(cpu=lambda: SimpleNamespace(numpy=lambda: embedding)))
            runtime = SimpleNamespace(NoiseReducer=Mock(return_value=Mock()), prepare_enrollment=a.prepare_enrollment)
            with patch.object(m, 'CONFIG', root / 'config'), patch.object(m, 'DATA', data), \
                    patch.object(m, 'model_ready', return_value=True), \
                    patch.object(m, 'personal_audio_module', return_value=runtime), \
                    patch.object(m, 'load_model', return_value=(model, None)), \
                    patch.object(m, 'sources', return_value=[{'name': 'physical', 'properties': {'device.api': 'alsa'}}, {'name': m.FILTER}]), \
                    patch.object(m, 'pactl', return_value=m.FILTER), \
                    patch.object(m.subprocess, 'Popen', return_value=capture) as spawn, \
                    patch.object(m.time, 'sleep'), patch('builtins.print'):
                m.save({'source': 'physical', 'personal': False, 'profiles': {'old': {'name': 'Old', 'file': 'old.npy'}}, 'profile': 'old'})
                m.enroll('Original')
                config = m.settings()
                profile = config['profiles'][config['profile']]
                self.assertEqual(profile['recognition_route'], 'original')
                self.assertEqual(profile['input'], 'physical')
                self.assertLess(profile['recognition_gain'], 1)
                self.assertIn('old', config['profiles'])
                self.assertEqual(old.read_bytes(), b'previous-profile-untouched')
                np.testing.assert_array_equal(np.load(m.profile_path(), allow_pickle=False), embedding)
                self.assertIn('--device=physical', spawn.call_args.args[0])
                self.assertIn('--format=float32le', spawn.call_args.args[0])

    def test_original_pipeline_failure_does_not_fall_back_or_touch_other_sources(self):
        try:
            a.rnnoise_path()
        except RuntimeError:
            self.skipTest('RNNoise library is not installed')
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            np.save(data / 'profile.npy', np.zeros((1, 192), dtype=np.float32))
            config = {'personal': True, 'noise': True, 'source': 'physical', 'profile': 'raw',
                      'profiles': {'raw': {'name': 'Raw', 'file': 'profile.npy',
                                          'recognition_route': 'original', 'recognition_gain': 0.6}}}
            capture, playback = Mock(stdout=io.BytesIO(b'')), Mock(stdin=io.BytesIO())
            with patch.object(m, 'settings', return_value=config), patch.object(m, 'DATA', data), \
                    patch.object(m, 'model_ready', return_value=True), \
                    patch.object(m.sys, 'prefix', str(data / 'venv')), \
                    patch.object(m, 'sources', return_value=[{'name': 'physical', 'properties': {'device.api': 'alsa'}}, {'name': m.FILTER}]), \
                    patch.object(m, 'load_model', return_value=(Mock(), Mock())), \
                    patch.object(m, 'personal_audio_module', return_value=a), \
                    patch.object(m, 'set_status'), patch.object(m.signal, 'signal'), \
                    patch.object(m.subprocess, 'Popen', side_effect=[capture, playback]) as spawn, \
                    patch.object(m, 'pactl', return_value=m.FILTER) as control:
                with self.assertRaises(RuntimeError):
                    m.process_voice()
                self.assertIn('--device=physical', spawn.call_args_list[0].args[0])
                self.assertIn('--format=float32le', spawn.call_args_list[0].args[0])
                self.assertIn('--rate=48000', spawn.call_args_list[0].args[0])
                self.assertIn('--rate=48000', spawn.call_args_list[1].args[0])
                self.assertEqual([call.args for call in control.call_args_list],
                                 [('get-default-source',), ('set-source-mute', m.SOURCE, '0')])
                capture.terminate.assert_called_once()
                playback.terminate.assert_called_once()


class ProfileCompatibility(unittest.TestCase):
    def test_old_profiles_keep_their_original_filtered_route(self):
        self.assertEqual(m.profile_route({'input': m.FILTER}), m.ProfileRoute.FILTERED)
        self.assertEqual(m.profile_route({'file': 'my-voice.npy'}), m.ProfileRoute.FILTERED)
        self.assertEqual(m.profile_route({'recognition_route': 'original'}), m.ProfileRoute.ORIGINAL)

    def test_switching_profile_restarts_worker_without_failure_backoff(self):
        process = Mock()
        process.poll.return_value = None
        with patch.object(m, 'selected_profile', return_value='old') as selected, \
                patch.object(m, 'set_status'), patch.object(m.subprocess, 'Popen', return_value=process) as spawn:
            monitor = m.PersonalVoiceMonitor()
            monitor.update(True)
            selected.return_value = 'original'
            monitor.update(True)
            self.assertEqual(spawn.call_count, 2)
            self.assertEqual(monitor.profile, 'original')
            self.assertEqual(monitor.failures, 0)
            self.assertEqual(monitor.retry_at, 0)
            process.terminate.assert_called_once()
            monitor.close()

    def test_idle_status_updates_to_new_selected_profile(self):
        with patch.object(m, 'selected_profile', return_value='old') as selected, patch.object(m, 'set_status') as status:
            monitor = m.PersonalVoiceMonitor()
            monitor.update(False)
            selected.return_value = 'original'
            monitor.update(False)
            self.assertEqual(status.call_args.kwargs['profile'], 'original')


if __name__ == '__main__':
    unittest.main()
