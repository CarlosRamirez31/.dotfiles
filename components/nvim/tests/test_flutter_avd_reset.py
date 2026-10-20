import contextlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HELPER = Path(__file__).resolve().parents[1] / 'dotfiles/.config/nvim/lua/util/flutter-avd-reset.py'
spec = importlib.util.spec_from_file_location('avd_reset', HELPER)
reset = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reset)


class ResetAVD(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.avd = self.root / 'Test.avd'
        self.avd.mkdir()
        (self.root / 'Test.ini').write_text('path=' + str(self.avd) + '\n')
        (self.avd / 'config.ini').write_text('disk.dataPartition.path=<temp>\n')
        self.environment = patch.dict(os.environ, ANDROID_AVD_HOME=str(self.root))
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_reset_preserves_definition_and_sd_card(self):
        for name in ('userdata-qemu.img', 'userdata-qemu.img.qcow2', 'encryptionkey.img', 'cache.img', 'sdcard.img'):
            (self.avd / name).write_text('state')
        snapshots = self.avd / 'snapshots/default_boot'
        snapshots.mkdir(parents=True)
        (snapshots / 'ram.bin').write_text('old RAM')
        with contextlib.redirect_stdout(io.StringIO()):
            reset.reset('Test')
        self.assertTrue((self.avd / 'config.ini').is_file())
        self.assertTrue((self.root / 'Test.ini').is_file())
        self.assertTrue((self.avd / 'sdcard.img').is_file())
        self.assertFalse((self.avd / 'userdata-qemu.img').exists())
        self.assertFalse((self.avd / 'userdata-qemu.img.qcow2').exists())
        self.assertFalse((self.avd / 'snapshots').exists())

    @unittest.skipIf(os.name == 'nt', 'POSIX lock test')
    def test_locked_avd_is_not_erased(self):
        import fcntl
        data = self.avd / 'userdata-qemu.img'
        data.write_text('keep')
        with (self.avd / 'multiinstance.lock').open('a+b') as lock:
            fcntl.lockf(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = subprocess.run([sys.executable, str(HELPER), 'Test'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('sigue en uso', result.stderr)
        self.assertEqual(data.read_text(), 'keep')

    def test_symlink_does_not_erase_external_files(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (outside / 'keep').write_text('keep')
        (self.avd / 'snapshots').symlink_to(outside, target_is_directory=True)
        with contextlib.redirect_stdout(io.StringIO()):
            reset.reset('Test')
        self.assertEqual((outside / 'keep').read_text(), 'keep')

    def test_custom_disk_is_rejected_before_deleting_anything(self):
        (self.avd / 'config.ini').write_text('disk.dataPartition.path=../userdata-qemu.img\n')
        data = self.avd / 'userdata-qemu.img'
        data.write_text('keep')
        with self.assertRaises(ValueError):
            reset.reset('Test')
        self.assertEqual(data.read_text(), 'keep')

    def test_invalid_names_are_rejected(self):
        for name in ('..', '../Test', '/', ''):
            with self.assertRaises(ValueError):
                reset.avd_directory(name)


if __name__ == '__main__':
    unittest.main()
