import importlib.machinery
import importlib.util
import io
import array
import json
from pathlib import Path
import statistics
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


def load(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


c = load('voice_compare', REPO / 'libexec/dotfiles-voice-compare')
m = load('compare_microphone', REPO / 'bin/dotfiles-microphone')


class VoiceComparison(unittest.TestCase):
    def test_live_levels_detect_silence_signal_and_clipping(self):
        silence = c.pcm_levels(bytes(c.CAPTURE_SECOND_BYTES))
        voice = c.pcm_levels(array.array('f', [0.03] * 16000).tobytes())
        clipped = c.pcm_levels(array.array('f', [1.0] * 16000).tobytes())
        self.assertEqual(silence['rms'], 0)
        self.assertGreater(voice['rms'], 0.002)
        self.assertEqual(voice['over_range_fraction'], 0)
        self.assertEqual(clipped['flat_peak_fraction'], 1)

    def test_each_phase_has_a_continuous_distinct_reading_passage(self):
        passages = list(c.READING_TEXT.values())
        self.assertEqual(len(passages), 3)
        self.assertEqual(len(set(passages)), 3)
        self.assertTrue(all(isinstance(passage, str) and len(passage.split()) > 40 for passage in passages))

    def test_capture_prints_one_passage_and_measured_levels_each_second(self):
        raw = array.array('f', [0.03] * 32000).tobytes()
        processes = [Mock(stdout=io.BytesIO(raw)), Mock(stdout=io.BytesIO(raw))]
        with patch.object(c.subprocess, 'Popen', side_effect=processes), patch.object(c, 'print') as output:
            c.capture_pair(m, {c.Route.ORIGINAL: 'physical', c.Route.FILTERED: m.FILTER},
                           2, 'test', 'Un texto continuo para leer con tranquilidad.')
        lines = [call.args[0] for call in output.call_args_list]
        self.assertEqual(sum('Un texto continuo' in line for line in lines), 1)
        self.assertTrue(any('01/2 s · Audio captado' in line for line in lines))
        self.assertTrue(any('02/2 s · Audio captado' in line for line in lines))
        measured = [line for line in lines if 'Audio captado' in line]
        self.assertEqual(len(measured), 2)
        self.assertTrue(all('original: SEÑAL' in line and 'filtered: SEÑAL' in line for line in measured))

    @unittest.skipIf(np is None, 'Requires the private voice runtime numpy')
    def test_enrollment_quality_distinguishes_quiet_and_clipped_routes(self):
        silence = c.enrollment_quality(np, np.zeros(16000, dtype=np.float32))
        clipped = c.enrollment_quality(np, np.ones(16000, dtype=np.float32))
        self.assertEqual(silence['quality'], c.Quality.QUIET)
        self.assertEqual(clipped['quality'], c.Quality.CLIPPED)
        self.assertIn('muy poco audio', c.quality_message(c.Route.ORIGINAL, silence))
        self.assertIn('saturación', c.quality_message(c.Route.FILTERED, clipped))

    @unittest.skipIf(np is None, 'Requires the private voice runtime numpy')
    def test_float_capture_preserves_overrange_and_scales_without_clipping(self):
        samples = np.linspace(-1.8, 1.8, 16000, dtype=np.float32)
        raw = np.tile(samples, 4).astype('<f4').tobytes()
        decoded = c.decode(np, raw)
        self.assertGreater(float(np.max(decoded)), 1.0)
        normalized, metrics = c.prepare_enrollment(np, decoded)
        self.assertEqual(metrics['quality'], c.Quality.OK)
        self.assertLess(metrics['gain'], 1.0)
        self.assertGreater(metrics['input_over_range_fraction'], 0.01)
        self.assertLessEqual(float(np.max(np.abs(normalized))), 0.900001)
        probe = c.decode(np, raw, metrics['gain'])
        np.testing.assert_allclose(probe, normalized)

    @unittest.skipIf(np is None, 'Requires the private voice runtime numpy')
    def test_scaling_does_not_accept_already_flattened_peaks(self):
        samples = np.linspace(-1.8, 1.8, 16000, dtype=np.float32)
        samples = np.clip(samples, -1.0, 1.0)
        _, metrics = c.prepare_enrollment(np, samples)
        self.assertEqual(metrics['quality'], c.Quality.CLIPPED)
        self.assertGreater(metrics['flat_peak_fraction'], 0.01)
        self.assertLess(metrics['gain'], 1.0)

    @unittest.skipIf(np is None, 'Requires the private voice runtime numpy')
    def test_invalid_registration_stops_before_remaining_phases_and_saves_metrics(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(c, 'microphone_module', return_value=m), \
                patch.object(m, 'CONFIG', Path(directory)), \
                patch.object(m, 'settings', return_value={'source': 'physical'}), \
                patch.object(m, 'sources', return_value=[{'name': 'physical', 'properties': {'device.api': 'alsa'}}, {'name': m.FILTER}]), \
                patch.object(m, 'pactl', return_value='physical'), \
                patch.object(m, 'load_model', return_value=(Mock(), Mock())), \
                patch.object(c, 'capture_pair', return_value={route: bytes(15 * c.CAPTURE_SECOND_BYTES) for route in c.Route}) as capture, \
                patch.object(c.time, 'sleep'), patch.object(c, 'print'):
            with self.assertRaisesRegex(RuntimeError, 'Registro incompleto'):
                c.main()
            self.assertEqual(capture.call_count, 1)
            report = json.loads((Path(directory) / 'voice-comparison.json').read_text())
            self.assertEqual(report['state'], 'error')
            self.assertEqual(report['phase'], 'enroll')
            self.assertEqual(report['enrollment_levels']['original']['quality'], 'too_quiet')
            self.assertIn('rms', report['enrollment_levels']['filtered'])

    def test_capture_keeps_routes_separate_and_closes_only_its_own_processes(self):
        raw = array.array('f', [0.01] * 16000).tobytes()
        filtered = array.array('f', [0.02] * 16000).tobytes()
        processes = [Mock(stdout=io.BytesIO(raw)), Mock(stdout=io.BytesIO(filtered))]
        devices = {c.Route.ORIGINAL: 'physical', c.Route.FILTERED: m.FILTER}
        with patch.object(c.subprocess, 'Popen', side_effect=processes) as spawn, \
                patch.object(c, 'print'):
            result = c.capture_pair(m, devices, 1, 'test')
        self.assertEqual(result, {c.Route.ORIGINAL: raw, c.Route.FILTERED: filtered})
        self.assertIn('--device=physical', spawn.call_args_list[0].args[0])
        self.assertIn('--device=' + m.FILTER, spawn.call_args_list[1].args[0])
        self.assertTrue(all('--format=float32le' in call.args[0] for call in spawn.call_args_list))
        for process in processes:
            process.terminate.assert_called_once()
            process.wait.assert_called_once()
            self.assertTrue(process.stdout.closed)

    def test_broken_route_fails_comparison_instead_of_scoring_truncated_audio(self):
        processes = [Mock(stdout=io.BytesIO(b'')), Mock(stdout=io.BytesIO(bytes(c.CAPTURE_SECOND_BYTES)))]
        with patch.object(c.subprocess, 'Popen', side_effect=processes), patch.object(c, 'print'):
            with self.assertRaisesRegex(RuntimeError, 'dejó de recibir'):
                c.capture_pair(m, {c.Route.ORIGINAL: 'physical', c.Route.FILTERED: m.FILTER}, 1, 'test')
        for process in processes:
            process.terminate.assert_called_once()

    def test_report_distinguishes_owner_and_other_using_actual_gate(self):
        np = SimpleNamespace(mean=statistics.mean, median=statistics.median,
                             percentile=lambda values, _: max(values))
        samples = [0.0] * 2560 * 20
        owner = SimpleNamespace(process_chunk=lambda _: 0.9)
        other = SimpleNamespace(process_chunk=lambda _: 0.2)
        accepted = c.score(m, np, owner, samples)
        rejected = c.score(m, np, other, samples)
        self.assertEqual(accepted['steady_pass_fraction'], 1.0)
        self.assertEqual(rejected['steady_pass_fraction'], 0.0)
        self.assertEqual(accepted['steady_blocks'], 5)
        self.assertEqual(accepted['opening_threshold'], m.VOICE_THRESHOLD)

    def test_invalid_model_response_is_not_reported_as_success(self):
        session = SimpleNamespace(process_chunk=lambda _: float('nan'))
        with self.assertRaisesRegex(RuntimeError, 'inválida'):
            c.score(m, None, session, [0.0] * 2560 * 20)

    def test_report_serializes_phase_and_route_identifiers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.json'
            c.write_report(path, {'state': c.ReportState.COMPLETE,
                                 'results': {c.Route.ORIGINAL: {c.Phase.OWNER: {'score_max': 0.9}}}})
            result = json.loads(path.read_text())
            self.assertEqual(result['state'], 'complete')
            self.assertEqual(result['results']['original']['owner']['score_max'], 0.9)


if __name__ == '__main__':
    unittest.main()
