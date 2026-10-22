import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / 'dotfiles/.local/bin/dotfiles-clipboard-menu'
loader = importlib.machinery.SourceFileLoader('clipboard_menu', str(SOURCE))
spec = importlib.util.spec_from_loader(loader.name, loader)
menu = importlib.util.module_from_spec(spec)
loader.exec_module(menu)


class ClipboardMenuTests(unittest.TestCase):
    def test_open_pin_and_paste_without_conflicting_rofi_bindings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env = {'CM_DIR': str(root), 'XDG_STATE_HOME': str(root), 'USER': 'test'}
            cache = root / 'clipmenu.6.test'
            cache.mkdir()
            label = 'Texto de prueba'
            text = label + '\nsegunda línea\n'
            (cache / menu.checksum(label)).write_text(text)
            (cache / 'line_cache').write_text('123 ' + label + '\n')
            original_run = subprocess.run
            actions = iter([10, 0])
            pasted = []

            def run(args, **kwargs):
                if args[0] == 'rofi':
                    # Rofi rejects assigning Ctrl+P to both row-up and custom-1.
                    self.assertEqual(args[args.index('-kb-row-up') + 1], 'Up')
                    self.assertEqual(args[args.index('-kb-custom-1') + 1], 'Control+p')
                    self.assertNotIn('capture_output', kwargs)
                    self.assertNotIn('stderr', kwargs)
                    return subprocess.CompletedProcess(args, next(actions), stdout='0\n')
                if args[0] == 'xsel':
                    pasted.append(kwargs['input'])
                    return subprocess.CompletedProcess(args, 0)
                return original_run(args, **kwargs)

            with patch.dict(os.environ, env), patch.object(menu.subprocess, 'run', run), patch('sys.argv', ['menu']):
                self.assertEqual(menu.menu(), 0)
            self.assertEqual(pasted, [text.encode(), text.encode()])
            self.assertEqual(json.loads((root / 'dotfiles/clipboard/pins.json').read_text()), [text])


if __name__ == '__main__':
    unittest.main()
