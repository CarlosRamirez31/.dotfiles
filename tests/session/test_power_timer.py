import importlib.machinery
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

loader = importlib.machinery.SourceFileLoader('power_timer', str(Path(__file__).resolve().parents[2] / 'bin/dotfiles-power-timer'))
spec = importlib.util.spec_from_loader(loader.name, loader)
app = importlib.util.module_from_spec(spec)
loader.exec_module(app)


class PowerTimer(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(patch.stopall)
        patch.object(app, 'STATE', Path(self.tmp.name)).start()
        self.run = patch.object(app.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)).start()

    def test_cancelled_or_old_token_cannot_execute_power_action(self):
        app.schedule('poweroff', 5)
        old = app.read_state()['token']
        app.cancel()
        self.run.reset_mock()
        app.execute(old)
        self.run.assert_not_called()
        self.assertEqual(app.read_state(), {})

    def test_new_schedule_replaces_old_token_and_rejects_early_execution(self):
        app.schedule('suspend', 10)
        old = app.read_state()['token']
        app.schedule('poweroff', 20)
        value = app.read_state()
        self.assertNotEqual(old, value['token'])
        self.run.reset_mock()
        app.execute(old)
        app.execute(value['token'])
        self.run.assert_not_called()

    def test_due_action_consumes_token_exactly_once(self):
        with app.locked():
            app.write_state({'kind': 'poweroff', 'token': 'test', 'deadline': time.time() - 1})
        app.execute('test')
        commands = [c.args[0] for c in self.run.call_args_list]
        self.assertIn(['systemctl', 'poweroff'], commands)
        self.run.reset_mock()
        app.execute('test')
        self.run.assert_not_called()

    def test_invalid_inputs_and_failed_timer_do_not_leave_pending_action(self):
        for kind, minutes in [('reboot', 1), ('poweroff', 0), ('suspend', 10081)]:
            with self.assertRaises(ValueError):
                app.schedule(kind, minutes)
        self.run.side_effect = [subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 0), subprocess.CalledProcessError(1, 'systemd-run')]
        with self.assertRaises(subprocess.CalledProcessError):
            app.schedule('poweroff', 1)
        self.assertEqual(app.read_state(), {})
