#!/usr/bin/env python3
"""Offline checks for explicit installation and launcher cwd/argument handling."""
import ctypes
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
COMPONENT = REPO / "setup/modules/rider"


class OptionalRider(unittest.TestCase):
    def selected(self, *args):
        result = subprocess.check_output([str(REPO / 'install.sh'), '--dry-run', *args], text=True)
        return result.strip().split(': ', 1)[1].split()

    def test_explicit_only(self):
        default = self.selected()
        self.assertNotIn('rider', default)
        self.assertEqual(default, self.selected('all'))
        self.assertEqual(['rider'], self.selected('rider'))
        self.assertEqual(default + ['rider'], self.selected('rider', 'all', 'rider'))
        self.assertEqual(['workbench', 'rider'], self.selected('rider', 'workbench'))

    def test_setup_refuses_host(self):
        result = subprocess.run(
            ['bash', str(REPO / 'setup/modules/rider/setup-container.sh')],
            env=dict(os.environ, CONTAINER_ID=''), capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn('requiere Distrobox dev', result.stderr)

    @classmethod
    def setUpClass(cls):
        # Act as PID 1 for these test children, and reap them explicitly.
        if sys.platform.startswith('linux'):
            assert ctypes.CDLL(None).prctl(36, 1, 0, 0, 0) == 0

    @classmethod
    def tearDownClass(cls):
        if sys.platform.startswith('linux'):
            ctypes.CDLL(None).prctl(36, 0, 0, 0, 0)

    def fixture(self, root):
        binary = root / 'fake-rider'
        binary.write_text('''#!/usr/bin/env python3
import json, os, pathlib, sys, time
pathlib.Path(os.environ['RIDER_TEST_RESULT']).write_text(json.dumps([os.getcwd(), sys.argv[1:], os.getpid()]))
stop = os.environ.get('RIDER_TEST_STOP')
while stop and not pathlib.Path(stop).exists():
    time.sleep(0.01)
''')
        binary.chmod(0o755)
        launcher = root / 'rider'
        launcher.write_text((REPO / 'bin/rider').read_text().replace('/opt/rider/current/bin/rider', str(binary)))
        launcher.chmod(0o755)
        distrobox = root / 'dotfiles-dev-exec'
        distrobox.write_text('''#!/bin/sh
[ "$1" = rider ] || exit 99
shift
export CONTAINER_ID=dev
exec "$(dirname -- "$0")/rider" "$@"
''')
        distrobox.chmod(0o755)
        return launcher

    def report(self, path):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                return json.loads(path.read_text())
            except (FileNotFoundError, json.JSONDecodeError):
                time.sleep(0.01)
        self.fail('Detached Rider did not start')

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Linux launcher uses setsid')
    def test_launcher_preserves_cwd_and_arguments_inside_and_outside_dev(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / 'project with spaces'
            project.mkdir()
            launcher = self.fixture(root)
            for container in ('', 'dev'):
                arguments = ['.', 'solution with spaces.sln', '--line', '17']
                report = root / ('report-' + (container or 'host'))
                result = subprocess.run(
                    [str(launcher), *arguments], cwd=project,
                    env=dict(os.environ, CONTAINER_ID=container, PATH=str(root) + os.pathsep + os.environ['PATH'],
                             XDG_CACHE_HOME=str(root / 'cache'), RIDER_TEST_RESULT=str(report)),
                    capture_output=True, text=True, timeout=3, check=True,
                )
                self.assertEqual(result.stdout, '')
                data = self.report(report)
                self.assertEqual(data[:2], [str(project), arguments])
                os.waitpid(data[2], 0)

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Linux process lifecycle test')
    def test_detached_rider_survives_hangup_and_exits_without_supervisor_or_zombie(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            launcher = self.fixture(root)
            report, stop = root / 'report', root / 'stop'
            env = dict(os.environ, CONTAINER_ID='dev', XDG_CACHE_HOME=str(root / 'cache'),
                       RIDER_TEST_RESULT=str(report), RIDER_TEST_STOP=str(stop))
            subprocess.run([str(launcher), '.'], env=env, capture_output=True, timeout=3, check=True)
            pid = self.report(report)[2]
            try:
                self.assertEqual(os.getsid(pid), pid, 'GUI must have its own session')
                status = Path('/proc', str(pid), 'status').read_text()
                self.assertIn('PPid:\t' + str(os.getpid()), status, 'no launcher or supervisor may remain')
                os.kill(pid, signal.SIGHUP)
                time.sleep(0.05)
                os.kill(pid, 0)
            finally:
                stop.touch()
                os.waitpid(pid, 0)
            self.assertFalse(Path('/proc', str(pid)).exists(), 'init must be able to reap the exited GUI')


if __name__ == '__main__':
    unittest.main()
