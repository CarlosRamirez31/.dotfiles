"""Verify selective installation, backups and managed destinations."""
import csv
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]


class Structure(unittest.TestCase):
    def rows(self):
        with (REPO / 'setup/links.tsv').open() as stream:
            return [row for row in csv.reader(stream, delimiter='\t') if row and not row[0].startswith('#')]

    def link(self, home, *modules, repo=REPO):
        subprocess.run(['bash', '-c', 'set -euo pipefail; source "$1/setup/lib.sh"; shift; for module in "$@"; do link_component "$module"; done',
                        'test', str(repo), *modules], env=dict(os.environ, HOME=str(home)), check=True,
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


    def test_source_directory_link_never_moves_or_backs_up_the_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / 'repo'; (repo / 'setup').mkdir(parents=True)
            (repo / 'setup/lib.sh').write_text((REPO / 'setup/lib.sh').read_text())
            source = repo / 'share/policy/apply'
            source.parent.mkdir(parents=True); source.write_text('policy source')
            (repo / 'setup/links.tsv').write_text('session\tshare/policy/apply\t.local/share/policy/apply\n')
            home = root / 'home'; target = home / '.local/share/policy'
            target.parent.mkdir(parents=True); target.symlink_to(source.parent)
            self.link(home, 'session', repo=repo)
            self.assertEqual(source.read_text(), 'policy source')
            self.assertEqual(list(source.parent.iterdir()), [source])
            self.assertTrue(target.is_symlink())


if __name__ == '__main__':
    unittest.main()
