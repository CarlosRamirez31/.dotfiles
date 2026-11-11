"""Exercise the brightness command boundary without changing real hardware."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class BrightnessControlTest(unittest.TestCase):
    def test_rejects_invalid_percentages_before_accessing_hardware(self):
        for value in ('-1', '101', '1000', '1.5', '1;touch /tmp/unwanted', ''):
            with self.subTest(value=value):
                result = subprocess.run([str(ROOT / 'bin/dotfiles-polybar'), '--brightness', 'set', value],
                                        capture_output=True, timeout=3)
                self.assertEqual(result.returncode, 2)

    def test_percentage_clamp_and_logind_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            card = base / 'test_backlight'
            card.mkdir()
            (card / 'brightness').write_text('500')
            (card / 'max_brightness').write_text('1000')
            programs = {
                'find': '#!/bin/sh\nprintf "%s\\n" "$TEST_CARD"\n',
                'brightnessctl': '#!/bin/sh\nprintf "%s\\n" "$*" >> "$TEST_LOG"\nexit 1\n',
                'busctl': '#!/bin/sh\nprintf "%s\\n" "$*" >> "$TEST_LOG"\n',
            }
            for name, text in programs.items():
                path = base / name
                path.write_text(text)
                path.chmod(0o755)
            log = base / 'actions'
            env = {**os.environ, 'PATH': f'{base}:/usr/bin:/bin',
                   'TEST_CARD': str(card), 'TEST_LOG': str(log)}
            for value, expected in (('0', '50'), ('040', '400'), ('100', '1000')):
                with self.subTest(value=value):
                    log.write_text('')
                    subprocess.run([str(ROOT / 'bin/dotfiles-polybar'), '--brightness', 'set', value],
                                   env=env, check=True, capture_output=True, timeout=3)
                    lines = log.read_text().splitlines()
                    self.assertEqual(lines[0], f'--device=test_backlight --quiet set {expected}')
                    self.assertTrue(lines[1].endswith(f'SetBrightness ssu backlight test_backlight {expected}'))
