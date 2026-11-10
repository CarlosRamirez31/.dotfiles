"""Shared Kitty launcher: display sizing and exact child argv preservation."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]


class Terminal(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="kitty launcher ñ ")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.commands = self.root / 'bin'
        self.commands.mkdir()
        self.env = dict(os.environ, PATH=str(self.commands) + os.pathsep + os.environ['PATH'],
                        TEST_ARGV=str(self.root / 'argv'))
        self.env.pop('DOTFILES_FONT_SIZE', None)
        self.command('kitty', '#!/usr/bin/python\nimport json, os, sys\n'
                     'open(os.environ["TEST_ARGV"], "w").write(json.dumps(sys.argv[1:]))\n')
        self.command('dotfiles-display', '#!/bin/sh\nprintf "10\\n"\n')

    def command(self, name, text):
        p = self.commands / name
        p.write_text(text)
        p.chmod(0o755)

    def launch(self, *args):
        p = subprocess.run([str(REPO / 'bin/dotfiles-terminal'), *args], env=self.env,
                           capture_output=True, text=True, timeout=5)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads((self.root / 'argv').read_text())

    def test_display_setting_keeps_calibrated_size(self):
        self.assertEqual(self.launch(), ['--override', 'font_size=15'])
        self.command('dotfiles-display', '#!/bin/sh\nprintf "12\\n"\n')
        self.assertEqual(self.launch(), ['--override', 'font_size=18'])

    def test_explicit_btop_size_and_native_child_arguments(self):
        self.env['DOTFILES_FONT_SIZE'] = '9'
        args = ['--directory', '/ruta con espacios 日本語', '--class', 'DotfilesBackup',
                '--override', 'initial_window_width=64c', '--', 'program',
                '$(touch unexpected)', '; exit 99', '--title=child option']
        self.assertEqual(self.launch(*args), ['--override', 'font_size=13.5', *args])
        self.assertFalse((self.root / 'unexpected').exists())

    def test_invalid_or_extreme_font_values_fall_back_without_execution(self):
        for value in ('7', '33', '1e2', '-1', 'NaN', '10; exit 99', '$(exit 99)'):
            with self.subTest(value=value):
                self.env['DOTFILES_FONT_SIZE'] = value
                self.assertEqual(self.launch('--', 'yazi'),
                                 ['--override', 'font_size=15', '--', 'yazi'])

    def test_display_failure_falls_back(self):
        self.command('dotfiles-display', '#!/bin/sh\nexit 1\n')
        self.assertEqual(self.launch(), ['--override', 'font_size=15'])


if __name__ == '__main__':
    unittest.main()
