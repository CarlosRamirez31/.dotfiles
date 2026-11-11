import importlib.machinery
import importlib.util
from pathlib import Path
import tempfile
import unittest

loader = importlib.machinery.SourceFileLoader('file_tray', str(Path(__file__).resolve().parents[2] / 'bin/dotfiles-file-tray'))
spec = importlib.util.spec_from_loader(loader.name, loader)
tray = importlib.util.module_from_spec(spec)
loader.exec_module(tray)


class FileTrayTest(unittest.TestCase):
    def test_paste_reads_copy_and_cut_without_treating_text_as_files(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'file ñ.txt'
            path.write_text('content')
            for cut in (False, True):
                payload = tray.clipboard_payload([str(path)], cut)
                self.assertEqual(tray.parse_file_clipboard(payload['x-special/gnome-copied-files']), ([str(path)], cut))
                self.assertEqual(tray.parse_file_clipboard(payload['text/uri-list'], native=False, kde_cut=cut), ([str(path)], cut))
            for data in (b'copy\nhttps://example.com/file', b'cut\nfile://server/file', b'/tmp/file', b'unknown\nfile:///tmp/file'):
                with self.subTest(data=data), self.assertRaises(ValueError):
                    tray.parse_file_clipboard(data)

    def test_multiple_files_have_native_copy_and_cut_targets(self):
        paths = ['/tmp/a ñ %.txt', '/tmp/line\nbreak.txt']
        payload = tray.clipboard_payload(paths)
        self.assertEqual(payload['text/uri-list'].count(b'\r\n'), 2)
        self.assertIn(b'%C3%B1%20%25', payload['text/uri-list'])
        self.assertIn(b'line%0Abreak', payload['text/uri-list'])
        self.assertTrue(payload['x-special/gnome-copied-files'].startswith(b'copy\n'))
        self.assertTrue(tray.clipboard_payload(paths, True)['x-special/gnome-copied-files'].startswith(b'cut\n'))
        self.assertEqual(tray.clipboard_payload(paths, True)['application/x-kde-cutselection'], b'1')

    def test_references_preserve_symlinks_and_deduplicate(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'literal $(do not run); ñ.txt'
            path.write_text('unchanged')
            link = Path(folder) / 'link'
            link.symlink_to(path)
            self.assertEqual(tray.local_paths([str(path), path.as_uri(), str(link)]), [str(path), str(link)])
            self.assertEqual(path.read_text(), 'unchanged')

    def test_remote_missing_and_relative_paths_are_rejected(self):
        for value in ('file://server/share/file', 'file:///tmp/a?query=1', '/missing/dotfiles-test-file', 'relative'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                tray.local_paths([value])
