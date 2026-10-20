#!/usr/bin/env python3
"""Offline checks for explicit selection and container-only Flutter tools."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

COMPONENT = Path(__file__).resolve().parents[1]
REPO = COMPONENT.parents[1]


class OptionalFlutter(unittest.TestCase):
    def test_keyboard_setting_preserves_other_avd_settings_and_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / 'config.ini'
            userdata = root / 'userdata.img'
            userdata.write_bytes(b'existing Android data')
            original = b'hw.keyboard=no\r\nhw.keyboard.lid=yes\r\nhw.ramSize=2048\r\n'
            config.write_bytes(original)
            def configure(value):
                subprocess.check_call(['python3', str(COMPONENT / 'configure-avd.py'), str(config), value])
            configure('yes')
            self.assertEqual(config.read_bytes(), original.replace(b'hw.keyboard=no', b'hw.keyboard=yes'))
            configure('keep')
            self.assertIn(b'hw.keyboard=yes', config.read_bytes())
            configure('no')
            self.assertEqual(config.read_bytes(), original)
            config.write_bytes(b'hw.ramSize=2048')
            configure('yes')
            self.assertEqual(config.read_bytes(), b'hw.ramSize=2048\nhw.keyboard=yes\n')
            self.assertEqual(userdata.read_bytes(), b'existing Android data')

    def selected(self, *args):
        output = subprocess.check_output(
            [str(REPO / 'install.sh'), '--dry-run', *args], text=True
        )
        return output.strip().split(': ', 1)[1].split()

    def test_requires_explicit_selection(self):
        default = self.selected()
        self.assertNotIn('flutter', default)
        self.assertEqual(default, self.selected('all'))
        self.assertEqual(['flutter'], self.selected('flutter'))
        self.assertEqual(default + ['flutter'], self.selected('flutter', 'all', 'flutter'))
        self.assertEqual(['workbench', 'flutter'], self.selected('flutter', 'workbench'))
        self.assertEqual(default + ['hermes', 'flutter'], self.selected('all', 'flutter', 'hermes'))

    def test_setup_refuses_host_before_downloads(self):
        env = dict(os.environ, CONTAINER_ID='')
        result = subprocess.run(
            ['bash', str(COMPONENT / 'setup-container.sh')], env=env,
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn('requiere Distrobox dev', result.stderr)
        self.assertNotIn('Consultando', result.stdout)

    def test_environment_only_activates_in_dev(self):
        envfile = COMPONENT / 'dotfiles/.config/flutter/env.zsh'
        for container in ('', 'other', 'dev'):
            env = dict(os.environ, CONTAINER_ID=container)
            env.pop('FLUTTER_HOME', None)
            result = subprocess.check_output(
                ['zsh', '-f', '-c', 'unset FLUTTER_HOME; source "$1"; print -r -- "${FLUTTER_HOME:-}"', 'check', str(envfile)],
                env=env, text=True
            ).strip()
            self.assertEqual(bool(result), container == 'dev')

    def test_launcher_keeps_name_and_uses_no_skin(self):
        with tempfile.TemporaryDirectory() as directory:
            emulator = Path(directory) / 'android-sdk/emulator/emulator'
            emulator.parent.mkdir(parents=True)
            emulator.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
            emulator.chmod(0o755)
            config = Path(directory) / 'config'
            (config / 'flutter').mkdir(parents=True)
            (config / 'flutter/env.zsh').write_text(
                (COMPONENT / 'dotfiles/.config/flutter/env.zsh').read_text()
            )
            env = dict(os.environ, CONTAINER_ID='dev', FLUTTER_DEV_HOME=directory, XDG_CONFIG_HOME=str(config))
            result = subprocess.check_output(
                ['zsh', str(COMPONENT / 'dotfiles/.local/bin/flutter-emulator'), 'Existing_AVD', '-no-snapshot-load'],
                env=env, text=True
            )
            self.assertEqual(result.splitlines(), ['-avd', 'Existing_AVD', '-no-skin', '-no-snapshot-load'])


if __name__ == '__main__':
    unittest.main()
