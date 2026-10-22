"""Verify selective installation and safe migration using disposable homes."""
import csv
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('migrate_links', REPO / 'setup/migrate-links.py')
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)


class Structure(unittest.TestCase):
    def rows(self):
        with (REPO / 'setup/links.tsv').open() as stream:
            return [row for row in csv.reader(stream, delimiter='\t') if row and not row[0].startswith('#')]

    def link(self, home, *modules):
        subprocess.run(['bash', '-c', 'set -euo pipefail; source "$1/setup/lib.sh"; shift; for module in "$@"; do link_component "$module"; done',
                        'test', str(REPO), *modules], env=dict(os.environ, HOME=str(home)), check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def test_manifest_is_complete_and_destinations_are_unique(self):
        rows = self.rows()
        self.assertEqual(len(rows), len({row[2] for row in rows}))
        for module, source, target in rows:
            self.assertTrue((REPO / source).is_file(), source)
            self.assertFalse(Path(target).is_absolute())
            self.assertNotIn('..', Path(target).parts)
            self.assertTrue((REPO / f'setup/modules/{module}.sh').is_file() or
                            (REPO / f'setup/modules/{module}/install.sh').is_file(), module)
        sources = {source for _, source, _ in rows}
        for folder in ('config', 'home', 'bin', 'libexec', 'share', 'assets'):
            actual = {str(p.relative_to(REPO)) for p in (REPO / folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
            self.assertFalse(actual - sources, actual - sources)

    def test_shared_directory_does_not_enable_optional_modules(self):
        with tempfile.TemporaryDirectory(prefix='dotfiles home ') as directory:
            home = Path(directory)
            self.link(home, 'rofi')
            self.assertTrue((home / '.config/rofi/config.rasi').is_file())
            self.assertFalse((home / '.config/rofi/wallpaper.rasi').exists())
            self.assertFalse((home / '.config/flutter/env.zsh').exists())
            self.link(home, 'wallpaper')
            self.assertTrue((home / '.config/rofi/wallpaper.rasi').is_file())

    def test_foreign_file_is_backed_up_once_and_private_settings_survive(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            target = home / '.config/alacritty/alacritty.toml'
            target.parent.mkdir(parents=True)
            target.write_text('personal terminal settings')
            private = home / '.config/dotfiles/backup.conf'
            private.parent.mkdir(parents=True)
            private.write_text('private backup settings')
            self.link(home, 'alacritty', 'backup')
            self.link(home, 'alacritty', 'backup')
            backups = list(target.parent.glob('*.backup.*'))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(), 'personal terminal settings')
            self.assertEqual(private.read_text(), 'private backup settings')
            self.assertEqual(target.resolve(), REPO / 'config/alacritty/alacritty.toml')

    def test_all_managed_files_link_without_packages_or_services(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            self.link(home, *sorted({row[0] for row in self.rows()}))
            for _, source, target in self.rows():
                self.assertEqual((home / target).resolve(), REPO / source)

    def test_migration_handles_directory_units_and_preserves_foreign_links(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / 'home'; home.mkdir()
            repo = home / '.dotfiles'; repo.mkdir()
            battery = home / '.local/share/battery-conservation'
            battery.parent.mkdir(parents=True)
            battery.symlink_to(repo / 'components/session/dotfiles/.local/share/battery-conservation')
            unit = home / '.config/systemd/user/timers.target.wants/dotfiles-backup.timer'
            unit.parent.mkdir(parents=True)
            unit.symlink_to(repo / 'components/backup/dotfiles/.config/systemd/user/dotfiles-backup.timer')
            foreign = home / '.zshrc'; foreign.symlink_to('/some/other/config')
            changes = migration.plan(home, repo, REPO)
            self.assertEqual(len(changes), 2)
            self.assertIn('components/', os.readlink(battery))
            migration.apply(changes)
            self.assertEqual(os.readlink(battery), str(repo / 'share/battery-conservation'))
            self.assertEqual(os.readlink(unit), str(repo / 'system/systemd/user/dotfiles-backup.timer'))
            self.assertEqual(os.readlink(foreign), '/some/other/config')
            self.assertEqual(migration.plan(home, repo, REPO), [])

    def test_migration_rolls_back_if_a_destination_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            a, b = Path(directory) / 'a', Path(directory) / 'b'
            a.symlink_to('old-a'); b.write_text('personal file')
            changes = [{'target': str(a), 'before': 'old-a', 'after': 'new-a'},
                       {'target': str(b), 'before': 'old-b', 'after': 'new-b'}]
            with self.assertRaises(RuntimeError):
                migration.apply(changes)
            self.assertEqual(os.readlink(a), 'old-a')
            self.assertEqual(b.read_text(), 'personal file')


if __name__ == '__main__':
    unittest.main()
