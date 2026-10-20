import errno
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

BACKEND = Path(__file__).resolve().parents[1] / 'dotfiles/.config/nvim/lua/util/nvim-trash.py'
spec = importlib.util.spec_from_file_location('nvim_trash', BACKEND)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TrashTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.work = self.root / 'work'
        self.work.mkdir()
        self.trash = module.Trash(self.root / 'trash')
        self.trash.items.mkdir(parents=True)

    def put(self, path, now=1000):
        result = self.trash.put([str(path)], now=now)
        self.assertEqual(result['errors'], [])
        return result['entries'][0]

    def test_file_restores_exact_path_and_contents(self):
        path = self.work / 'hello world.txt'
        path.write_text('important')
        path.chmod(0o640)
        entry = self.put(path)
        self.assertFalse(path.exists())
        self.assertEqual(len(self.trash.entries()), 1)
        self.trash.restore(entry['id'], now=1001)
        self.assertEqual(path.read_text(), 'important')
        self.assertEqual(path.stat().st_mode & 0o777, 0o640)
        self.assertEqual(self.trash.entries(), [])

    def test_directory_is_one_entry_with_all_children(self):
        directory = self.work / 'project'
        (directory / 'nested').mkdir(parents=True)
        (directory / 'nested/file.txt').write_text('nested')
        (directory / '.hidden').write_text('hidden')
        result = self.trash.put([str(directory / 'nested/file.txt'), str(directory)], now=1000)
        self.assertEqual(result['errors'], [])
        self.assertEqual(len(result['entries']), 1)
        self.assertEqual(result['entries'][0]['kind'], 'directory')
        self.assertEqual(len(self.trash.entries()), 1)
        self.trash.restore(result['entries'][0]['id'], now=1001)
        self.assertEqual((directory / 'nested/file.txt').read_text(), 'nested')
        self.assertEqual((directory / '.hidden').read_text(), 'hidden')

    def test_expiration_exactly_five_hours_not_file_mtime(self):
        path = self.work / 'old.txt'
        path.write_text('old')
        os.utime(path, (0, 0))
        entry = self.put(path)
        deadline = 1000 + 5 * 60 * 60
        self.assertEqual(entry['expires_at'], deadline)
        self.assertEqual(self.trash.purge(now=deadline - 1), [])
        with self.assertRaises(ValueError):
            self.trash.restore(entry['id'], now=deadline)
        self.assertEqual(self.trash.purge(now=deadline), [entry['id']])
        self.assertFalse((self.trash.items / entry['id']).exists())

    def test_restore_never_overwrites_existing_file(self):
        path = self.work / 'same.txt'
        path.write_text('original')
        entry = self.put(path)
        path.write_text('new')
        with self.assertRaises(ValueError):
            self.trash.restore(entry['id'], now=1001)
        self.assertEqual(path.read_text(), 'new')
        self.assertEqual((self.trash.items / entry['id'] / 'payload').read_text(), 'original')

    def test_same_names_do_not_collide(self):
        path = self.work / 'same.txt'
        path.write_text('one')
        first = self.put(path)
        path.write_text('two')
        second = self.put(path)
        self.assertNotEqual(first['id'], second['id'])
        self.assertEqual(len(self.trash.entries()), 2)

    def test_broken_symlink_preserved_without_following(self):
        path = self.work / 'broken'
        path.symlink_to('missing-target')
        entry = self.put(path)
        self.trash.restore(entry['id'], now=1001)
        self.assertTrue(path.is_symlink())
        self.assertEqual(os.readlink(path), 'missing-target')

    def test_purge_directory_symlink_does_not_touch_target(self):
        outside = self.work / 'outside'
        outside.mkdir()
        (outside / 'keep').write_text('keep')
        directory = self.work / 'project'
        directory.mkdir()
        (directory / 'link').symlink_to(outside, target_is_directory=True)
        self.put(directory)
        self.trash.purge(now=1000 + module.RETENTION)
        self.assertEqual((outside / 'keep').read_text(), 'keep')

    def test_missing_original_parent_is_recreated(self):
        parent = self.work / 'parent'
        parent.mkdir()
        path = parent / 'file'
        path.write_text('data')
        entry = self.put(path)
        parent.rmdir()
        self.trash.restore(entry['id'], now=1001)
        self.assertEqual(path.read_text(), 'data')

    def test_failed_move_leaves_original_intact(self):
        path = self.work / 'file'
        path.write_text('keep')
        with patch.object(module.shutil, 'move', side_effect=OSError('disk full')):
            result = self.trash.put([str(path)], now=1000)
        self.assertEqual(path.read_text(), 'keep')
        self.assertEqual(result['entries'], [])
        self.assertEqual(len(result['errors']), 1)

    def test_cross_filesystem_restore(self):
        for directory in (False, True):
            path = self.work / ('folder' if directory else 'file')
            if directory:
                path.mkdir()
                (path / 'nested').write_text('data')
            else:
                path.write_text('data')
            entry = self.put(path)
            with patch.object(module.os, 'replace', side_effect=OSError(errno.EXDEV, 'different device')):
                self.trash.restore(entry['id'], now=1001)
            self.assertEqual((path / 'nested' if directory else path).read_text(), 'data')

    def test_trash_cannot_trash_itself_or_its_ancestors(self):
        for path in (self.trash.root, self.root, self.trash.items):
            result = self.trash.put([str(path)])
            self.assertEqual(result['entries'], [])
            self.assertEqual(len(result['errors']), 1)
            self.assertTrue(path.exists())

    def test_corrupt_metadata_is_not_automatically_destroyed(self):
        folder = self.trash.items / ('a' * 32)
        folder.mkdir()
        (folder / 'payload').write_text('keep')
        (folder / 'info.json').write_text('{"expires_at": 0}')
        self.assertEqual(self.trash.purge(now=100000), [])
        self.assertEqual((folder / 'payload').read_text(), 'keep')

    def test_cli_put_list_restore_json(self):
        path = self.work / '-á file.txt'
        path.write_text('data')
        def cli(*args):
            output = subprocess.check_output([sys.executable, str(BACKEND), '--root', str(self.trash.root), *args], text=True)
            return json.loads(output)
        entry = cli('put', '--', str(path))['entries'][0]
        self.assertEqual(len(cli('list')['entries']), 1)
        self.assertEqual(cli('restore', entry['id'])['restored']['original'], str(path))
        self.assertEqual(path.read_text(), 'data')

    def test_two_sessions_cannot_lose_the_same_deleted_file(self):
        path = self.work / 'shared.txt'
        path.write_text('only copy')
        command = [sys.executable, str(BACKEND), '--root', str(self.trash.root), 'put', '--', str(path)]
        processes = [subprocess.Popen(command, stdout=subprocess.PIPE, text=True) for _ in range(2)]
        results = [json.loads(process.communicate(timeout=10)[0]) for process in processes]
        self.assertEqual(sum(len(result['entries']) for result in results), 1)
        entries = self.trash.entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual((self.trash.items / entries[0]['id'] / 'payload').read_text(), 'only copy')


if __name__ == '__main__':
    unittest.main()
