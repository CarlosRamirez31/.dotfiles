import importlib.machinery
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
COMPONENT = REPO / "setup/modules/voice-isolation"
loader = importlib.machinery.SourceFileLoader('voice_isolation', str(REPO / 'libexec/dotfiles-voice-isolation'))
spec = importlib.util.spec_from_loader(loader.name, loader)
module = importlib.util.module_from_spec(spec)
loader.exec_module(module)


def physical(name):
    return {'name': name, 'properties': {'device.api': 'alsa'}}


class VoiceIsolation(unittest.TestCase):
    def test_filter_keeps_native_protocol_and_single_module_list(self):
        base = 'context.modules = [ { name = libpipewire-module-protocol-native } ]\n'
        rendered = module.append_filter(base, {'name': 'libpipewire-module-filter-chain'})
        self.assertEqual(rendered.count('context.modules'), 1)
        self.assertIn('libpipewire-module-protocol-native', rendered)
        self.assertIn('libpipewire-module-filter-chain', rendered)
        with self.assertRaises(ValueError):
            module.append_filter('invalid base config', {})

    def test_component_is_optional(self):
        def selected(*args):
            return subprocess.check_output([str(REPO / 'install.sh'), '--dry-run', *args], text=True).split(': ', 1)[1].split()
        self.assertNotIn('voice-isolation', selected())
        self.assertNotIn('voice-isolation', selected('all'))
        self.assertEqual(selected('voice-isolation'), ['voice-isolation'])

    def test_selection_skips_monitors_and_virtual_sources(self):
        sources = [physical('speakers.monitor'),
                   {'name': module.SOURCE, 'properties': {'device.api': 'alsa', 'node.virtual': True}},
                   physical('usb-microphone'), physical('laptop-microphone')]
        self.assertEqual(module.select_source(sources, 'laptop-microphone'), 'laptop-microphone')
        self.assertEqual(module.select_source(sources, module.SOURCE), 'usb-microphone')
        self.assertEqual(module.select_source(sources, module.SOURCE, 'laptop-microphone'), 'laptop-microphone')
        with self.assertRaises(ValueError):
            module.select_source(sources, module.SOURCE, 'speakers.monitor')
        with self.assertRaises(ValueError):
            module.select_source([], module.SOURCE)

    def test_activation_preserves_hardware_volume_by_default(self):
        calls = []
        def fake(*args):
            calls.append(args)
            if args[:3] == ('-f', 'json', 'list'):
                return json.dumps([{'name': module.SOURCE}])
            return ''
        with tempfile.TemporaryDirectory() as directory, patch.dict(module.os.environ, {}, clear=True), patch.object(module, 'pactl', fake):
            runtime = Path(directory)
            (runtime / 'source').write_text('laptop-microphone')
            module.activate(runtime)
            self.assertFalse(any(c[:2] == ('set-source-volume', 'laptop-microphone') for c in calls))
            with patch.dict(module.os.environ, {'VOICE_ISOLATION_INPUT_VOLUME': '25%'}):
                module.activate(runtime)
            self.assertIn(('set-source-volume', 'laptop-microphone', '25%'), calls)

    def test_volume_validation(self):
        for value in ('25%', '80%', '0%', '100%'):
            self.assertEqual(module.volume(value), value)
        for value in ('101%', '-5%', '100.1%', '1;echo secret', 'bad'):
            with self.assertRaises(ValueError):
                module.volume(value)


if __name__ == '__main__':
    unittest.main()
