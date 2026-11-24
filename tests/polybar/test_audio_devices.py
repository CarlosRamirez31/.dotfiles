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
    def test_input_ports_do_not_duplicate_devices_or_mark_another_source(self):
        sources = [
            {'index': 4, 'name': 'mic.internal', 'description': 'Sound card',
             'active_port': 'internal', 'ports': [
                 {'name': 'internal', 'description': 'Internal Microphone'},
                 {'name': 'unplugged', 'description': 'Headset', 'availability': 'not available'}]},
            {'index': 5, 'name': 'filtered', 'description': 'Aislamiento de voz'},
        ]
        with patch.object(audio, 'listing', return_value=sources), patch.object(audio, 'pulse', return_value='filtered'):
            self.assertEqual(audio.inputs(), [
                ('source-port', '4', 'internal', 0, 'Internal Microphone'),
                ('source', '5', '-', 1, 'Aislamiento de voz')])
        with patch.object(audio, 'listing', return_value=sources), patch.object(audio, 'pulse', return_value='mic.internal'):
            self.assertEqual([row[3] for row in audio.inputs()], [1, 0])

    def test_input_selection_preserves_filter_connections(self):
        source = {'index': 4, 'name': 'dotfiles_voice_isolation'}
        streams = [
            {'index': 8, 'properties': {'application.name': 'Browser'}},
            {'index': 9, 'properties': {'node.name': 'dotfiles_voice_capture'}},
            {'index': 10, 'properties': {'node.virtual': 'true'}},
            {'index': 11, 'properties': {'application.name': 'dotfiles-microphone'}},
            {'index': 12, 'properties': {'node.name': 'input.dotfiles_personal_voice'}},
        ]
        with patch.object(audio, 'listing', side_effect=lambda kind: [source] if kind == 'sources' else streams), patch.object(audio, 'pulse') as pulse:
            audio.apply('source', '4', '-')
            self.assertEqual([call.args for call in pulse.call_args_list], [
                ('set-default-source', source['name']), ('move-source-output', '8', source['name'])])

    def test_output_selection_preserves_personal_voice_playback(self):
        data = {'sinks': [{'index': 2, 'name': 'speakers'}], 'sink-inputs': [
            {'index': 9, 'properties': {'application.name': 'dotfiles-microphone'}},
            {'index': 10, 'properties': {'target.object': 'dotfiles_personal_voice_bus'}},
            {'index': 11, 'properties': {'application.name': 'Browser'}}]}
        with patch.object(audio, 'listing', side_effect=data.__getitem__), patch.object(audio, 'pulse') as pulse:
            audio.apply('sink', '2', '-')
            self.assertEqual([call.args for call in pulse.call_args_list], [
                ('set-default-sink', 'speakers'), ('move-sink-input', '11', 'speakers')])

    def test_personal_voice_bus_is_not_a_playback_device(self):
        bus = {'index': 2, 'name': 'dotfiles_personal_voice_bus', 'description': 'Internal bus'}
        with patch.object(audio, 'listing', side_effect=lambda kind: [bus] if kind == 'sinks' else []), patch.object(audio, 'pulse', return_value='speakers') as pulse:
            self.assertEqual(audio.outputs(), [])
            pulse.reset_mock()
            with self.assertRaises(ValueError):
                audio.apply('sink', '2', '-')
            pulse.assert_not_called()

    def test_input_selection_moves_recording_streams(self):
        source = {'index': 4, 'name': 'mic.usb'}
        with patch.object(audio, 'listing', side_effect=lambda kind: [source] if kind == 'sources' else [{'index': 8}]), patch.object(audio, 'pulse') as pulse:
            audio.apply('source', '4', '-')
            self.assertEqual([call.args for call in pulse.call_args_list], [('set-default-source', 'mic.usb'), ('move-source-output', '8', 'mic.usb')])

    def test_input_list_excludes_playback_monitors(self):
        sources = [{'index': 4, 'name': 'mic.usb', 'description': 'USB microphone', 'monitor_of_sink': 4294967295},
                   {'index': 5, 'name': 'sink.monitor', 'description': 'Monitor', 'monitor_of_sink': 1}]
        with patch.object(audio, 'listing', return_value=sources), patch.object(audio, 'pulse', return_value='mic.usb'):
            self.assertEqual(audio.inputs(), [('source', '4', '-', 1, 'USB microphone')])

    def test_real_sink_port_array_is_supported(self):
        sink = {'index': 2, 'name': 'sink.two', 'description': 'Speakers', 'active_port': 'speaker',
                'ports': [{'name': 'speaker', 'description': 'Speaker', 'availability': 'availability unknown'},
                          {'name': 'headphones', 'description': 'Headphones', 'availability': 'not available'}]}
        with patch.object(audio, 'listing', side_effect=lambda kind: [sink] if kind == 'sinks' else []), patch.object(audio, 'pulse', return_value='sink.two'):
            self.assertEqual(audio.outputs(), [('port', '2', 'speaker', 1, 'Speakers · Speaker')])

    def test_outputs_mark_only_the_default_device_connector(self):
        sinks = [
            {'index': 2, 'name': 'speakers', 'description': 'Laptop', 'active_port': 'speaker',
             'ports': [{'name': 'speaker', 'description': 'Speakers'}]},
            {'index': 3, 'name': 'bluetooth', 'description': 'Hesh Evo', 'active_port': 'headphones',
             'ports': [{'name': 'headphones', 'description': 'Headphones'}]},
        ]
        with patch.object(audio, 'listing', side_effect=lambda kind: sinks if kind == 'sinks' else []), patch.object(audio, 'pulse', return_value='speakers'):
            self.assertEqual(audio.outputs(), [
                ('port', '2', 'speaker', 1, 'Laptop · Speakers'),
                ('port', '3', 'headphones', 0, 'Hesh Evo · Headphones')])

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
