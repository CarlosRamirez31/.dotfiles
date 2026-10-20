import array
import importlib.machinery
import importlib.util
import io
import json
from types import SimpleNamespace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

COMPONENT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('microphone', str(COMPONENT / 'dotfiles/.local/bin/dotfiles-microphone'))
spec = importlib.util.spec_from_loader(loader.name, loader)
m = importlib.util.module_from_spec(spec)
loader.exec_module(m)


def mic(name):
    return {'name': name, 'description': name, 'properties': {'device.api': 'alsa'},
            'active_port': 'internal', 'ports': [
                {'name': 'internal', 'description': 'Micrófono interno'},
                {'name': 'headset', 'availability': 'not available'}]}


class Microphone(unittest.TestCase):
    def test_indicator_excludes_desktop_and_filter_streams_and_groups_apps(self):
        items = [dict(mic('laptop'), index=1), {'name': 'speakers.monitor', 'index': 2}, {'name': m.SOURCE, 'index': 3}]
        streams = [
            {'index': 10, 'source': 1, 'properties': {'node.name': 'dotfiles_voice_capture'}},
            {'index': 11, 'source': 3, 'properties': {'application.name': 'dotfiles-microphone'}},
            {'index': 12, 'source': 2, 'properties': {'application.name': 'OBS'}},
            {'index': 13, 'source': 3, 'mute': False, 'properties': {'application.name': 'OBS', 'application.process.id': '42'}},
            {'index': 14, 'source': 3, 'mute': True, 'properties': {'application.name': 'OBS', 'application.process.id': '42'}},
            {'index': 15, 'source': 1, 'corked': True, 'properties': {'application.name': 'Firefox'}},
        ]
        self.assertEqual(m.recording_apps(items, streams), [{'name': 'OBS', 'streams': [13, 14], 'muted': False}])

    def test_global_mute_covers_physical_and_processed_sources_only(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(m, 'CONFIG', Path(directory)), patch.object(m, 'sources', return_value=[mic('laptop'), {'name': m.SOURCE}, {'name': 'speakers.monitor'}]), patch.object(m, 'pactl') as ctl:
            m.microphone_switch('off')
            self.assertTrue(m.settings()['muted'])
            self.assertEqual(ctl.call_args_list[0].args, ('set-source-mute', 'laptop', '1'))
            self.assertEqual(ctl.call_args_list[1].args, ('set-source-mute', m.SOURCE, '1'))
            self.assertEqual(ctl.call_count, 2)

    def test_explicit_disconnected_mic_does_not_fall_back(self):
        with self.assertRaises(ValueError):
            m.choose([mic('laptop')], 'missing-usb', 'laptop')
        with self.assertRaises(ValueError):
            m.check_port(mic('laptop'), 'headset')
        self.assertIn('Micrófono interno', m.source_label(mic('laptop')))

    def test_virtual_sources_and_monitors_cannot_feed_back(self):
        items = [mic('speaker.monitor'), mic('laptop'),
                 {'name': 'filtered', 'properties': {'device.api': 'alsa', 'node.virtual': True}}]
        self.assertEqual([s['name'] for s in m.physical(items)], ['laptop'])

    def test_personal_switch_does_not_control_rnnoise_or_default_source(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(m, 'CONFIG', Path(directory)), patch.object(m, 'DATA', Path(directory)), patch.object(m, 'model_ready', return_value=True), patch.object(m, 'sources', return_value=[{'name': m.FILTER}]), patch.object(m, 'cleanup_legacy_endpoint') as cleanup, patch.object(m, 'run', return_value='') as run:
            (Path(directory) / 'my-voice.npy').touch()
            m.save({'noise': True, 'personal': False, 'source': 'laptop'})
            m.change('personal', True)
            self.assertTrue(m.settings()['noise'])
            self.assertTrue(m.settings()['personal'])
            m.change('personal', False)
            self.assertTrue(m.settings()['noise'])
            self.assertFalse(m.settings()['personal'])
            self.assertEqual([call.args for call in run.call_args_list], [
                ('systemctl', '--user', 'disable', '--now', 'dotfiles-microphone.service'),
                ('systemctl', '--user', 'daemon-reload'),
                ('systemctl', '--user', 'restart', 'dotfiles-microphone.service'),
                ('systemctl', '--user', 'stop', 'dotfiles-microphone.service')])
            cleanup.assert_called_once()

    def test_experiment_requires_existing_filter_and_preserves_settings_on_failure(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(m, 'CONFIG', Path(directory)), patch.object(m, 'DATA', Path(directory)), patch.object(m, 'model_ready', return_value=True), patch.object(m, 'sources', return_value=[]), patch.object(m, 'run') as run:
            (Path(directory) / 'my-voice.npy').touch()
            m.save({'noise': True, 'personal': False})
            with self.assertRaises(ValueError):
                m.change('personal', True)
            run.assert_not_called()
            self.assertFalse(m.settings()['personal'])
            with patch.object(m, 'sources', return_value=[{'name': m.FILTER}]):
                run.side_effect = RuntimeError('start failed')
                with self.assertRaises(RuntimeError):
                    m.change('personal', True)
            self.assertFalse(m.settings()['personal'])
            self.assertTrue(m.settings()['noise'])

    def test_endpoint_does_not_select_default_or_change_physical_gain(self):
        with patch.object(m, 'sources', return_value=[mic('laptop'), {'name': m.FILTER}]), patch.object(m, 'pactl', return_value='[]') as ctl:
            m.ensure_endpoint()
            calls = [call.args for call in ctl.call_args_list]
            self.assertFalse(any(call[0] in ('set-default-source', 'set-source-port') for call in calls))
            self.assertEqual([call for call in calls if call[0] == 'set-source-volume'], [('set-source-volume', m.SOURCE, '100%')])
            self.assertTrue(any('priority.session=0' in ' '.join(call) for call in calls))

    def test_pipeline_failure_leaves_normal_filter_and_hardware_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            (data / 'my-voice.npy').touch()
            capture = Mock(stdout=io.BytesIO(b''))
            playback = Mock()
            with patch.object(m, 'settings', return_value={'personal': True, 'noise': True}), patch.object(m, 'DATA', data), patch.object(m, 'model_ready', return_value=True), patch.object(m.sys, 'prefix', str(data / 'venv')), patch.object(m, 'sources', return_value=[{'name': m.FILTER}]), patch.dict(m.sys.modules, {'numpy': SimpleNamespace(load=lambda *a, **k: [])}), patch.object(m, 'load_model', return_value=(Mock(), Mock())), patch.object(m, 'ensure_endpoint'), patch.object(m, 'cleanup_endpoint') as cleanup, patch.object(m, 'set_status'), patch.object(m.signal, 'signal'), patch.object(m.subprocess, 'Popen', side_effect=[capture, playback]) as popen, patch.object(m, 'pactl') as ctl, patch.object(m, 'run') as run:
                with self.assertRaises(RuntimeError):
                    m.serve()
                self.assertIn('--device=' + m.FILTER, popen.call_args_list[0].args[0])
                self.assertEqual([call.args for call in ctl.call_args_list], [('set-source-mute', m.SOURCE, '0')])
                run.assert_not_called()
                capture.terminate.assert_called_once()
                playback.terminate.assert_called_once()
                cleanup.assert_called_once()

    def test_cleanup_removes_only_experiment_modules(self):
        modules = [
            {'index': 1, 'name': 'module-remap-source', 'argument': 'source_name=' + m.SOURCE},
            {'index': 2, 'name': 'module-null-sink', 'argument': 'sink_name=' + m.BUS},
            {'index': 3, 'name': 'module-null-sink', 'argument': 'sink_name=other'},
            {'index': 4, 'name': 'module-filter-chain', 'argument': 'source_name=' + m.FILTER}]
        with patch.object(m, 'pactl', return_value=json.dumps(modules)) as ctl:
            m.cleanup_endpoint()
            self.assertEqual([call.args for call in ctl.call_args_list if call.args[0] == 'unload-module'], [('unload-module', '1'), ('unload-module', '2')])

    def test_legacy_cleanup_migrates_only_old_bridge_consumers(self):
        def control(*args):
            if args[-1] == 'source-outputs':
                return json.dumps([{'index': 10, 'source': 1}, {'index': 11, 'source': 2}])
            if args[-1] == 'modules':
                return json.dumps([{'index': 20, 'name': 'module-remap-source', 'argument': 'source_name=dotfiles_microphone'}, {'index': 21, 'name': 'module-null-sink', 'argument': 'sink_name=headset'}])
            if args[0] == 'get-default-source':
                return m.FILTER
            return ''
        with patch.object(m, 'sources', return_value=[{'name': m.FILTER, 'index': 3}, {'name': 'dotfiles_microphone', 'index': 1}]), patch.object(m, 'pactl', side_effect=control) as ctl:
            m.cleanup_legacy_endpoint()
            calls = [call.args for call in ctl.call_args_list]
            self.assertIn(('move-source-output', '10', m.FILTER), calls)
            self.assertNotIn(('move-source-output', '11', m.FILTER), calls)
            self.assertIn(('unload-module', '20'), calls)
            self.assertNotIn(('unload-module', '21'), calls)
            self.assertFalse(any(call[0] == 'set-default-source' for call in calls))

    def test_gate_silences_rejected_voice_and_fades_transitions(self):
        gate = m.VoiceGate()
        samples = array.array('h', [10000] * 2560)
        self.assertEqual(m.VoiceGate().process(samples, 0.1), bytes(5120))
        passed = array.array('h', gate.process(samples, 0.9))
        self.assertEqual(passed[0], 0)
        self.assertEqual(passed[-1], 10000)
        self.assertEqual(gate.process(samples, 0.8), bytes(5120))
        self.assertEqual(gate.process(samples, 0.1), bytes(5120))
        self.assertEqual(gate.process(samples, float('nan')), bytes(5120))

    def test_changing_mic_preserves_unrelated_filter_preferences(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(m, 'CONFIG', Path(directory)):
            env = Path(directory) / 'environment'
            env.write_text('VOICE_ISOLATION_THRESHOLD=65\nVOICE_ISOLATION_INPUT_VOLUME=25%\n')
            m.set_filter_source('usb-microphone')
            text = env.read_text()
            self.assertIn('VOICE_ISOLATION_THRESHOLD=65', text)
            self.assertIn('VOICE_ISOLATION_INPUT_VOLUME=keep', text)
            self.assertNotIn('25%', text)


if __name__ == '__main__':
    unittest.main()
