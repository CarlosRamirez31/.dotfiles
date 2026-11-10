"""Exercise weekly scheduling and terminal choices without touching real backups."""
import os
from pathlib import Path
import pty
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
BACKUP = REPO / 'bin/dotfiles-backup'


class BackupSchedule(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / 'home'
        self.commands = self.root / 'commands'
        self.commands.mkdir()
        (self.home / '.local/bin').mkdir(parents=True)
        self.env = dict(os.environ, HOME=str(self.home),
                        XDG_CONFIG_HOME=str(self.root / 'config'),
                        XDG_STATE_HOME=str(self.root / 'state'),
                        XDG_RUNTIME_DIR=str(self.root / 'runtime'),
                        TZ='America/Santo_Domingo', TEST_NOW='2026-11-09 10:00',
                        PATH=str(self.commands) + os.pathsep + os.environ['PATH'])
        self.env.pop('DOTFILES_BACKUP_CYCLE', None)
        self.state = self.root / 'state/dotfiles/backup/finished-cycle'
        self.command(self.commands / 'date', '''case "$1" in
+%F|+%u|+%s) exec /usr/bin/date -d "$TEST_NOW" "$1" ;;
*) exec /usr/bin/date "$@" ;;
esac''')
        self.command(self.home / '.local/bin/dotfiles-terminal', 'echo WINDOW_OPENED')

    def command(self, path, body):
        path.write_text('#!/bin/sh\n' + body + '\n')
        path.chmod(0o755)

    def run_backup(self, action, answers=None):
        if answers is None:
            return subprocess.run([str(BACKUP), action], env=self.env,
                                  capture_output=True, text=True, timeout=5)
        master, slave = pty.openpty()
        try:
            child = subprocess.Popen([str(BACKUP), action], env=self.env, stdin=slave,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     text=True)
            os.close(slave)
            slave = None
            os.write(master, answers.encode())
            try:
                output, _ = child.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.communicate()
                raise
            self.assertEqual(child.returncode, 0, output)
            return output
        finally:
            os.close(master)
            if slave is not None:
                os.close(slave)

    def test_cancel_survives_new_process_and_resets_next_monday_at_ten(self):
        output = self.run_backup('scheduled-run', '3\n')
        self.assertIn('Cancelado por esta semana', output)
        self.assertTrue(self.state.exists())
        for now in ('2026-11-09 12:00', '2026-11-15 22:00', '2026-11-16 09:59'):
            self.env['TEST_NOW'] = now
            self.assertNotIn('WINDOW_OPENED', self.run_backup('scheduled-popup').stdout)
        self.env['TEST_NOW'] = '2026-11-16 10:00'
        self.assertIn('WINDOW_OPENED', self.run_backup('scheduled-popup').stdout)

    def test_defer_leaves_cycle_pending(self):
        output = self.run_backup('scheduled-run', '2\n')
        self.assertIn('dentro de 2 horas', output)
        self.assertFalse(self.state.exists())
        self.assertIn('WINDOW_OPENED', self.run_backup('scheduled-popup').stdout)

    def configure(self, disk=False):
        config = self.root / 'config/dotfiles/backup.conf'
        config.parent.mkdir(parents=True)
        repository = self.root / 'repository'
        repository.mkdir()
        (repository / 'config').touch()
        config.write_text(f'RESTIC_REPOSITORY={repository}\n' +
                          ('BACKUP_DISK_UUID=private-disk-id\n' if disk else ''))
        self.command(self.commands / 'restic', 'echo "restic $1"')

    def test_missing_disk_hides_identifier_and_allows_defer(self):
        self.configure(disk=True)
        self.command(self.commands / 'findmnt', 'exit 1')
        self.command(self.commands / 'udisksctl', 'echo private-disk-id >&2; exit 1')
        output = self.run_backup('scheduled-run', '1\n2\n')
        self.assertIn('No pude abrir tu disco', output)
        self.assertIn('dentro de 2 horas', output)
        self.assertNotIn('private-disk-id', output)
        self.assertNotIn('restic backup', output)
        self.assertIn('private-disk-id', self.state.with_name('mount.log').read_text())
        self.assertFalse(self.state.exists())

    def test_failed_backup_can_be_cancelled(self):
        self.configure(disk=True)
        self.command(self.commands / 'findmnt', 'exit 1')
        self.command(self.commands / 'udisksctl', 'exit 1')
        self.run_backup('scheduled-run', '1\n3\n')
        self.assertNotIn('WINDOW_OPENED', self.run_backup('scheduled-popup').stdout)

    def test_success_suppresses_further_attempts_this_week(self):
        self.configure()
        output = self.run_backup('scheduled-run', '1\ntest-password\n\n')
        self.assertIn('restic backup', output)
        self.assertIn('restic forget', output)
        self.assertIn('Tus archivos ya están respaldados', output)
        self.assertNotIn('WINDOW_OPENED', self.run_backup('scheduled-popup').stdout)


if __name__ == '__main__':
    unittest.main()
