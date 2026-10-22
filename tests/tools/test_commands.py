"""Boundary checks for commands that otherwise operate on real user data."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest

REPO = Path(__file__).resolve().parents[2]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


copy_module = load('copy_component', 'setup/copy-component.py')
integrate = load('integrate_dev', 'environments/workbench/podman/integrate_dev.py')


class Commands(unittest.TestCase):
    def fixture(self, root):
        commands = root / 'commands'; commands.mkdir()
        env = dict(os.environ, HOME=str(root / 'home'), XDG_RUNTIME_DIR=str(root / 'runtime'),
                   PATH=str(commands) + os.pathsep + os.environ['PATH'], TEST_ARGS=str(root / 'arguments'))
        Path(env['HOME']).mkdir(); Path(env['XDG_RUNTIME_DIR']).mkdir()
        return commands, env

    def command(self, directory, name, body):
        path = directory / name
        path.write_text('#!/bin/sh\n' + body + '\n'); path.chmod(0o755)

    def test_firewall_rejects_out_of_range_and_uses_decimal_ports(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); commands, env = self.fixture(root)
            self.command(commands, 'sudo', 'printf "%s\\n" "$@" > "$TEST_ARGS"')
            for value in ('0', '65536', '9999999999999999999999999', 'x', '1;echo invalid'):
                result = subprocess.run([str(REPO / 'bin/dotfiles-firewall'), 'lab-open', 'tcp', value], env=env, capture_output=True)
                self.assertEqual(result.returncode, 2, value)
                self.assertFalse((root / 'arguments').exists())
            subprocess.run([str(REPO / 'bin/dotfiles-firewall'), 'lab-open', 'tcp', '08'], env=env, check=True, capture_output=True)
            self.assertIn('{ 8 }', (root / 'arguments').read_text())

    def test_backup_restore_rejects_home_ancestors_and_nonempty_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); _, env = self.fixture(root)
            filled = root / 'filled'; filled.mkdir(); (filled / 'keep').write_text('keep')
            for target in (Path(env['HOME']), root, Path('/'), filled):
                result = subprocess.run([str(REPO / 'bin/dotfiles-backup'), 'restore', 'latest', str(target)], env=env, capture_output=True)
                self.assertEqual(result.returncode, 2, target)
            self.assertEqual((filled / 'keep').read_text(), 'keep')

    def test_full_recording_uses_all_monitors_and_pads_odd_regions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); commands, env = self.fixture(root)
            self.command(commands, 'xrandr', "printf 'Screen 0: minimum 8 x 8, current 3840 x 1080, maximum 32767 x 32767\\nHDMI-1 connected\\n   1920x1080 60.00*\\n'")
            self.command(commands, 'xdg-user-dir', 'printf "%s\\n" "$HOME/Videos"')
            self.command(commands, 'notify-send', 'exit 0')
            self.command(commands, 'ffmpeg', 'printf "%s\\n" "$@" > "$TEST_ARGS"')
            result = subprocess.run([str(REPO / 'bin/dotfiles-record'), 'full'], env=dict(env, DISPLAY=':99'), capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            for _ in range(100):
                if (root / 'arguments').exists(): break
                time.sleep(.01)
            args = (root / 'arguments').read_text().splitlines()
            self.assertEqual(args[args.index('-video_size') + 1], '3840x1080')
            self.assertIn('pad=ceil(iw/2)*2:ceil(ih/2)*2', args)

    def test_vpn_off_never_signals_a_reused_unrelated_pid(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); commands, env = self.fixture(root)
            (Path(env['XDG_RUNTIME_DIR']) / 'dotfiles-openvpn.pid').write_text('12345\n')
            self.command(commands, 'ps', 'printf "unrelated-editor\\n"')
            self.command(commands, 'sudo', 'printf "called\\n" > "$TEST_ARGS"')
            result = subprocess.run(['zsh', '-f', '-c', 'source "$1"; vpn-off', 'test', str(REPO / 'config/zsh/functions.zsh')], env=env, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertFalse((root / 'arguments').exists())

    def test_copy_materializes_optional_files_and_preserves_external_source(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / 'home'; home.mkdir()
            external = Path(directory) / 'external'; external.write_text('personal source')
            target = home / '.config/flutter/env.zsh'; target.parent.mkdir(parents=True)
            target.symlink_to(external)
            copy_module.copy_components(REPO, home, {'flutter'})
            self.assertFalse(target.is_symlink())
            self.assertEqual(target.read_bytes(), (REPO / 'config/flutter/env.zsh').read_bytes())
            self.assertEqual(external.read_text(), 'personal source')
            self.assertTrue((home / '.local/bin/flutter-emulator').is_file())
            self.assertFalse((home / '.local/bin/hermes').exists())
            copy_module.copy_components(REPO, home, {'flutter'})
            self.assertEqual(len(list(target.parent.glob('*.backup.*'))), 1)

    def test_copy_refuses_parent_links_outside_the_private_home(self):
        with tempfile.TemporaryDirectory() as directory:
            home, external = Path(directory) / 'home', Path(directory) / 'external'
            home.mkdir(); external.mkdir(); (home / '.config').symlink_to(external)
            with self.assertRaises(ValueError):
                copy_module.copy_components(REPO, home, {'flutter'})
            self.assertEqual(list(external.iterdir()), [])

    def test_dev_appearance_integration_does_not_require_hermes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); home, host = root / 'home', root / 'host'
            home.mkdir(); host.mkdir()
            integrate.configure(home, host, root / 'missing-presentation')
            self.assertFalse((root / 'missing-presentation').exists())
            self.assertTrue((home / '.Xresources').is_file())

    def test_login_profile_restores_tools_after_system_profile_resets_path(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory); (home / '.local/bin').mkdir(parents=True)
            (home / '.zshenv').write_bytes((REPO / 'home/.zshenv').read_bytes())
            program = home / '.local/bin/audit-user-tool'
            program.write_text('#!/bin/sh\nexit 0\n'); program.chmod(0o755)
            result = subprocess.run(['zsh', '-f', '-c', 'path=(/usr/bin /bin); source "$1"; command -v audit-user-tool',
                                     'test', str(REPO / 'home/.zprofile')], env=dict(os.environ, HOME=str(home)),
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), str(program))

    def test_backup_setup_without_a_terminal_preserves_existing_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); _, env = self.fixture(root)
            config = root / 'home/.config/dotfiles/backup.conf'
            config.parent.mkdir(parents=True); config.write_text('previous private destination')
            # Avoid a pre-existing XDG_CONFIG_HOME from the launching session.
            env['XDG_CONFIG_HOME'] = str(root / 'home/.config')
            result = subprocess.run([str(REPO / 'bin/dotfiles-backup'), 'setup', '/new/repository'],
                                    env=env, stdin=subprocess.DEVNULL, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(config.read_text(), 'previous private destination')

    def test_locker_falls_back_when_background_generation_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); commands, env = self.fixture(root)
            env['XDG_CACHE_HOME'] = str(root / 'cache')
            self.command(commands, 'pgrep', 'exit 1')
            self.command(commands, 'betterlockscreen', 'exit 1')
            self.command(commands, 'bc', 'exit 0')
            self.command(commands, 'xdpyinfo', 'exit 0')
            self.command(commands, 'xsecurelock', 'printf "fallback\n" > "$TEST_ARGS"')
            result = subprocess.run([str(REPO / 'bin/dotfiles-lock')], env=env, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((root / 'arguments').read_text().strip(), 'fallback')


if __name__ == '__main__':
    unittest.main()
