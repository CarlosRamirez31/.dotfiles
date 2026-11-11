import importlib.machinery
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

loader = importlib.machinery.SourceFileLoader('audio_devices', str(Path(__file__).resolve().parents[2] / 'bin/dotfiles-audio-devices'))
spec = importlib.util.spec_from_loader(loader.name, loader)
audio = importlib.util.module_from_spec(spec)
loader.exec_module(audio)


class AudioDevicesTest(unittest.TestCase):
    def test_real_sink_port_array_is_supported(self):
        sink = {'index': 2, 'name': 'sink.two', 'description': 'Speakers', 'active_port': 'speaker',
                'ports': [{'name': 'speaker', 'description': 'Speaker', 'availability': 'availability unknown'},
                          {'name': 'headphones', 'description': 'Headphones', 'availability': 'not available'}]}
        with patch.object(audio, 'listing', side_effect=lambda kind: [sink] if kind == 'sinks' else []), patch.object(audio, 'pulse', return_value='sink.two'):
            self.assertEqual(audio.outputs(), [('sink', '2', '-', 1, 'Speakers'), ('port', '2', 'speaker', 1, 'Speaker')])

    def test_output_selection_moves_current_streams(self):
        def listing(kind):
            return {'sinks': [{'index': 2, 'name': 'sink.two'}], 'sink-inputs': [{'index': 9}, {'index': 12}]}[kind]
        with patch.object(audio, 'listing', side_effect=listing), patch.object(audio, 'pulse') as pulse:
            audio.apply('sink', '2', '-')
            self.assertEqual([call.args for call in pulse.call_args_list], [
                ('set-default-sink', 'sink.two'), ('move-sink-input', '9', 'sink.two'),
                ('move-sink-input', '12', 'sink.two')])

    def test_disconnected_output_and_unavailable_port_are_rejected(self):
        with patch.object(audio, 'listing', return_value=[{'index': 1, 'ports': {'headphones': {'availability': 'not available'}}}]), patch.object(audio, 'pulse') as pulse:
            for action in [('sink', '99', '-'), ('port', '1', 'headphones'), ('port', '1', 'untrusted;input')]:
                with self.subTest(action=action), self.assertRaises(ValueError):
                    audio.apply(*action)
            pulse.assert_not_called()

    def test_only_available_playback_profiles_can_be_applied(self):
        card = {'index': 3, 'name': 'card.three', 'profiles': {
            'duplex': {'sinks': 1, 'available': True}, 'input': {'sinks': 0, 'available': True},
            'off': {'sinks': 0, 'available': True}, 'missing-hdmi': {'sinks': 1, 'available': False}}}
        with patch.object(audio, 'listing', return_value=[card]), patch.object(audio, 'pulse') as pulse:
            for key in ('input', 'off', 'missing-hdmi'):
                with self.subTest(key=key), self.assertRaises(ValueError): audio.apply('profile', '3', key)
            pulse.assert_not_called()
            audio.apply('profile', '3', 'duplex')
            pulse.assert_called_once_with('set-card-profile', 'card.three', 'duplex')
