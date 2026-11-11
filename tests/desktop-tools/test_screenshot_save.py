"""Capture into runtime storage; persistent saving is an explicit UI action."""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ScreenshotSaveTest(unittest.TestCase):
    def test_capture_is_temporary_and_card_gets_one_save_destination(self):
        for mode in ('full', 'area'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as folder:
                base = Path(folder)
                commands = base / 'bin'
                commands.mkdir()
                pictures = base / 'Pictures ñ %'
                runtime = base / 'runtime'
                runtime.mkdir()
                programs = {
                    'xdg-user-dir': '#!/bin/sh\nprintf "%s\\n" "$TEST_PICTURES"\n',
                    'slop': '#!/bin/sh\necho "1 2 100 80"\n',
                    'maim': '#!/bin/sh\nfor target do :; done\nprintf "image-data" > "$target"\n',
                    'xclip': '#!/bin/sh\ncat > "$TEST_BASE/clipboard"\n',
                    'awesome-client': '#!/bin/sh\ncat > "$TEST_BASE/card"\necho "boolean true"\n',
                }
                for name, content in programs.items():
                    path = commands / name
                    path.write_text(content)
                    path.chmod(0o755)
                env = {**os.environ, 'PATH': f'{commands}:/usr/bin:/bin', 'XDG_RUNTIME_DIR': str(runtime),
                       'TEST_BASE': str(base), 'TEST_PICTURES': str(pictures)}
                subprocess.run([str(ROOT / 'bin/dotfiles-screenshot'), mode], env=env, check=True, capture_output=True)
                self.assertEqual(list((pictures / 'Screenshots').iterdir()), [])
                captures = list((runtime / 'dotfiles-screenshots').glob('capture-*.png'))
                self.assertEqual(len(captures), 1)
                self.assertEqual(captures[0].read_bytes(), b'image-data')
                encoded = re.findall(r'"((?:\\\d{3})+)"', (base / 'card').read_text())
                decoded = [bytes(int(value, 10) for value in re.findall(r'\\(\d{3})', item)).decode() for item in encoded]
                self.assertEqual(decoded[0], str(captures[0]))
                self.assertTrue(decoded[1].startswith(str(pictures / 'Screenshots') + '/'))
                self.assertNotIn('-edited-', decoded[1])
