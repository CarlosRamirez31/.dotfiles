"""Return to the existing Codex session without opening a fresh terminal."""
from pathlib import Path
import runpy
import shutil
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


class SessionLauncher(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.env = patch.dict('os.environ', {'XDG_RUNTIME_DIR': self.directory.name})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.module = runpy.run_path(str(ROOT / 'bin/dotfiles-coucou-open-session'))
        self.session = '01a16904-5d1b-7892-a156-8cb410ab4581'

    def test_focus_live_terminal_without_opening_anything(self):
        self.module['record'](self.session, {'pid': 123, 'started': '42'}, '/')
        with patch.dict(self.module['open_session'].__globals__, {'process': lambda pid: ('alacritty', 1, '42')}), patch('subprocess.run') as run, patch('subprocess.Popen') as launch:
            run.return_value.stdout = 'boolean true'
            self.module['open_session'](self.session)
            self.assertIn('c.pid == 123', run.call_args.args[0][1])
            launch.assert_not_called()

    def test_closed_or_reused_terminal_resumes_exact_session(self):
        self.module['record'](self.session, {'pid': 123, 'started': '42'}, '/')
        with patch.dict(self.module['open_session'].__globals__, {'process': lambda pid: ('alacritty', 1, '99')}), patch('subprocess.Popen') as launch:
            self.module['open_session'](self.session)
            self.assertEqual(launch.call_args.args[0][-4:], ['-e', 'codex', 'resume', self.session])
            self.assertIn('--working-directory', launch.call_args.args[0])
        with patch('subprocess.Popen') as launch:
            self.module['open_session']('')
            self.assertEqual(launch.call_args.args[0][-4:], ['-e', 'codex', 'resume', '--all'])
        with patch('subprocess.Popen') as launch:
            with self.assertRaises(ValueError):
                self.module['open_session']('invalid; command')
            launch.assert_not_called()

    def test_hook_preserves_original_bytes_and_permissions(self):
        import io
        raw = ('{ "session_id": "' + self.session + '", "cwd": "/", "hook_event_name": "PermissionRequest" }').encode()
        globals_ = self.module['hook'].__globals__
        with patch('sys.stdin') as stdin, patch.dict(globals_, {'terminal_owner': lambda: {'pid': 123, 'started': '42'}}), patch('subprocess.run') as run:
            stdin.buffer = io.BytesIO(raw)
            run.return_value.returncode = 7
            self.assertEqual(self.module['hook'](), 7)
            self.assertEqual(run.call_args.kwargs['input'], raw)
        with patch('sys.stdin') as stdin, patch.dict(globals_, {'terminal_owner': lambda: None}), patch('subprocess.run') as run:
            stdin.buffer = io.BytesIO(raw)
            self.assertEqual(self.module['hook'](), 0)
            run.assert_not_called()

    def test_install_is_idempotent_preserving_other_hooks(self):
        import json
        import os
        root = Path(self.directory.name)
        original = str(Path.home() / '.local/share/coucou/bin/coucou-hook')
        data = {'hooks': {'Stop': [{'hooks': [{'command': repr(original) + ' --agent codex', 'timeout': 3}, {'command': 'other-hook'}]}]}}
        path = root / 'hooks.json'
        path.write_text(json.dumps(data))
        with patch.dict(os.environ, {'CODEX_HOME': str(root)}):
            self.module['install_hooks']()
            first = path.read_text()
            self.module['install_hooks']()
        self.assertEqual(path.read_text(), first)
        hooks = json.loads(first)['hooks']['Stop'][0]['hooks']
        self.assertTrue(hooks[0]['command'].endswith(' --hook'))
        self.assertEqual(hooks[0]['timeout'], 3)
        self.assertEqual(hooks[1]['command'], 'other-hook')
        self.assertTrue(path.with_name('hooks.json.before-coucou-terminal').exists())

    @unittest.skipUnless(shutil.which('node'), 'Node is required')
    def test_current_native_bridge(self):
        result = subprocess.run(['node', '--test', 'tests/coucou/agent-hub/bridge.test.mjs'],
                                cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
