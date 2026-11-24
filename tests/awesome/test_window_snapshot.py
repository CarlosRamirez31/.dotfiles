import os
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

app = runpy.run_path(str(Path(__file__).resolve().parents[2] / 'bin/dotfiles-window-snapshot'))
capture = app['capture']


class WindowSnapshotTest(unittest.TestCase):
    def setUp(self):
        self.runtime = tempfile.TemporaryDirectory()
        self.addCleanup(self.runtime.cleanup)
        self.env = patch.dict(os.environ, XDG_RUNTIME_DIR=self.runtime.name)
        self.env.start()
        self.addCleanup(self.env.stop)
        directory = Path(self.runtime.name) / 'dotfiles-window-previews'
        directory.mkdir()
        self.output = directory / 'test.png'

    def test_rejects_invalid_xid_and_destination_before_spawning(self):
        with patch('subprocess.Popen') as spawn:
            for xid, output in [('0', self.output), ('-1', self.output),
                                ('1; echo unsafe', self.output), ('4294967296', self.output),
                                ('1', Path(self.runtime.name) / 'outside.png')]:
                with self.subTest(xid=xid, output=output), self.assertRaises(ValueError):
                    capture(xid, str(output))
            spawn.assert_not_called()

    def test_closed_window_discards_partial_png(self):
        self.output.write_bytes(b'partial')
        process = Mock()
        process.wait.return_value = 1
        with patch('subprocess.Popen', return_value=process), patch('subprocess.run', return_value=Mock(returncode=0)):
            self.assertEqual(capture('123', str(self.output)), 1)
        self.assertFalse(self.output.exists())

    def test_timeout_stops_capture_and_discards_partial_png(self):
        self.output.write_bytes(b'partial')
        process = Mock()
        with patch('subprocess.Popen', return_value=process), patch('subprocess.run', side_effect=subprocess.TimeoutExpired('magick', 5)):
            with self.assertRaises(subprocess.TimeoutExpired):
                capture('123', str(self.output))
        process.kill.assert_called_once()
        process.wait.assert_called_once()
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
