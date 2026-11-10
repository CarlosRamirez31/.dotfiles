"""Portal isolation, cancellation and untrusted file-path boundaries."""
import os
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
PICKER = runpy.run_path(str(ROOT / 'bin/dotfiles-filechooser'))


class FileChooser(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="selector ñ ' ")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = self.root / 'config'
        self.config.mkdir()
        (self.config / 'plugins').mkdir()
        (self.config / 'keymap.toml').write_text('[[mgr.prepend_keymap]]\non="r"\nrun="rename"\n')
        self.result = self.root / 'respuesta'
        self.env = patch.dict(os.environ, {'YAZI_CONFIG_HOME': str(self.config)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def run_picker(self, paths, flags=('0', '0', '0'), suggested=None):
        def terminal(argv, env):
            self.assertEqual(argv[:2], ['terminal-test', 'yazi'])
            self.session = Path(env['YAZI_CONFIG_HOME'])
            self.assertNotEqual(self.session, self.config)
            self.assertEqual(self.session.stat().st_mode & 0o777, 0o700)
            self.assertTrue((self.session / 'plugins').is_symlink())
            self.assertIn('plugin portal-picker confirm', (self.session / 'keymap.toml').read_text())
            self.assertIn('run="rename"', (self.session / 'keymap.toml').read_text())
            self.mode = env['DOTFILES_PICKER_MODE']
            self.name = env['DOTFILES_PICKER_NAME']
            if paths is not None:
                Path(env['DOTFILES_PICKER_RESULT']).write_text(''.join(str(p) + '\n' for p in paths))
            return subprocess.CompletedProcess(argv, 0)
        with patch.object(subprocess, 'run', terminal):
            return PICKER['run_picker']([*flags, str(suggested or self.root), str(self.result), '0', 'terminal-test'])

    def test_save_keeps_literal_name_and_creates_no_placeholder(self):
        target = self.root / "nombre ñ ' ; $(touch no).pdf"
        escaped = str(target).replace("'", "'\\''")
        self.assertEqual(self.run_picker([target], ('0', '0', '1'), escaped), 0)
        self.assertEqual(self.name, target.name)
        self.assertEqual(self.mode, 'save')
        self.assertEqual(self.result.read_text(), str(target) + '\n')
        self.assertFalse(target.exists())
        self.assertFalse(self.session.exists())

    def test_cancel_returns_empty_result_without_touching_files(self):
        existing = self.root / 'archivo.txt'
        existing.write_text('preserve')
        self.assertEqual(self.run_picker(None, ('0', '0', '1'), existing), 0)
        self.assertEqual(self.result.read_text(), '')
        self.assertEqual(existing.read_text(), 'preserve')
        self.assertFalse(self.session.exists())

    def test_multiple_files_and_single_file_limit(self):
        files = [self.root / name for name in ('uno.txt', 'dos con espacios.txt')]
        for f in files:
            f.touch()
        self.assertEqual(self.run_picker(files, ('1', '0', '0')), 0)
        self.assertEqual(self.result.read_text().splitlines(), [str(f) for f in files])
        with self.assertRaises(ValueError):
            self.run_picker(files)

    def test_directory_selection_and_invalid_file(self):
        self.assertEqual(self.run_picker([self.root], ('0', '1', '0')), 0)
        self.assertEqual(self.mode, 'directory')
        wrong = self.root / 'file'; wrong.touch()
        with self.assertRaises(ValueError):
            self.run_picker([wrong], ('0', '1', '0'))

    def test_result_symlink_and_hardlink_never_truncate_the_target(self):
        victim = self.root / 'victim'; victim.write_text('preserve')
        self.result.symlink_to(victim)
        with self.assertRaises(OSError):
            PICKER['write_result'](self.result, 'replacement')
        self.result.unlink()
        os.link(victim, self.result)
        with self.assertRaises(ValueError):
            PICKER['write_result'](self.result, 'replacement')
        self.assertEqual(victim.read_text(), 'preserve')

    def test_relative_results_and_invalid_flags_are_rejected(self):
        with self.assertRaises(ValueError):
            self.run_picker([Path('relative')], ('0', '0', '1'))
        with self.assertRaises(ValueError):
            PICKER['run_picker'](['invalid', '0', '1', str(self.root), str(self.result), '0'])


if __name__ == '__main__':
    unittest.main()
