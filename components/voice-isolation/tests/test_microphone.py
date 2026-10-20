import array
import importlib.machinery
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

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

    def test_noise_and_personal_toggles_persist_independently(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(m, 'CONFIG', Path(directory)), patch.object(m, 'run', return_value=''):
            m.save({'noise': True, 'personal': True, 'source': 'laptop'})
            m.change('noise', False)
            self.assertEqual(m.settings(), {'noise': False, 'personal': True, 'source': 'laptop'})
            m.change('personal', False)
            self.assertFalse(m.settings()['noise'])
            self.assertFalse(m.settings()['personal'])

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
