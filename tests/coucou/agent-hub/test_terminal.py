import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('terminal', (Path(__file__).resolve().parents[3] / 'libexec/coucou-agent-hub') / 'agent_hub_terminal.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TerminalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="coucou ' Unicode-ñ $() ; ")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cwd = self.root / 'proyecto con espacios y 日本語'
        self.cwd.mkdir()
        self.calls, self.launches = [], []
        self.route = {'version': 1, 'idCarpeta': 'opaque-project', 'idMessage': 'native-session', 'agente': 'codex'}
        self.conversations = {'codex': [{'id': 'native-session', 'route': self.route}], 'hermes': []}
        self.error = None
        self.response_route = None
        self.bridge = module.HubTerminal(self.root / 'state', config={
            'terminal': {'program': 'alacritty', 'adapter': 'alacritty'}},
            run=self.run_hub, spawn=self.spawn, which=lambda name: '/bin/' + name)

    def run_hub(self, argv, **kwargs):
        self.calls.append(argv)
        self.assertNotIn('shell', kwargs)
        if self.error:
            return subprocess.CompletedProcess(argv, 1, '', self.error)
        action = argv[1]
        if action == 'conversations':
            result = self.conversations.get(argv[argv.index('--agent') + 1], [])
        elif action == 'open':
            self.assertEqual(argv[-1], '--dry-run')
            path = Path(argv[argv.index('--route-file') + 1])
            result = {'valid': True, 'route': self.response_route or json.loads(path.read_text()), 'cwd': str(self.cwd)}
        elif action == 'new':
            result = dict(self.route, idMessage='new-stable')
        elif action == 'agents':
            result = [{'id': 'codex', 'installed': True}, {'id': 'hermes', 'installed': True}]
        else:
            raise AssertionError(argv)
        return subprocess.CompletedProcess(argv, 0, json.dumps(result), '')

    def spawn(self, argv, **kwargs):
        self.assertNotIn('shell', kwargs)
        self.launches.append((argv, kwargs))
        return type('Process', (), {'pid': 99999999})()

    def test_return_to_agents_lifecycle_uses_configured_terminal(self):
        self.bridge.config['returnToAgents'] = True
        result = self.bridge.open({'route':self.route})
        argv = self.launches[0][0]
        self.assertEqual(argv[:4],['alacritty','--working-directory',str(self.cwd),'-e'])
        self.assertEqual(Path(argv[5]).name,'terminal_session.py')
        self.assertEqual(argv[6:],['--route-file',result['routeFile']])

    def test_automatic_general_creation_persists_before_open_and_reuses(self):
        original = self.bridge.hub
        def hub(*argv):
            if argv[0] == 'projects':
                return [{'idCarpeta': 'opaque-project', 'roots': [str(Path.home())]}]
            return original(*argv)
        self.bridge.hub = hub
        request = {'agent':'codex','sessionId':'legacy','autoCreate':True}
        result = self.bridge.open(request)
        self.assertEqual(result['route']['idMessage'],'new-stable')
        item = module.read_json(self.bridge.metadata_path('codex','legacy'))
        self.assertEqual(item['route'],result['route'])
        with self.assertRaises(module.BridgeError): self.bridge.open(request)
        self.assertEqual(sum(a[1]=='new' for a in self.calls),1)

    def test_codex_and_hermes_exact_execution_in_same_folder(self):
        hermes = dict(self.route, agente='hermes', idMessage='h-native')
        second = dict(self.route, idMessage='second-native')
        self.conversations['hermes'] = [{'id': 'h-native', 'route': hermes}]
        self.conversations['codex'].append({'id': 'second-native', 'route': second})
        for route in (self.route, second, hermes):
            self.bridge.observe({'agent': route['agente'], 'sessionId': route['idMessage'], 'event': 'SessionStart'})
            result = self.bridge.open({'agent': route['agente'], 'sessionId': route['idMessage']})
            self.assertEqual(result['route'], route)
            self.assertEqual(json.loads(Path(result['routeFile']).read_text()), route)
        self.assertEqual(len(self.launches), 3)

    def test_descriptor_opaque_ids_aliases_and_private_atomic_files(self):
        for alias in ('new-opaque " ñ ; $(touch no)', 'handoff-123'):
            route = dict(self.route, idMessage=alias, idCarpeta='not/a/physical/path', extension={'keep': 'unchanged'})
            result = self.bridge.open({'route': route})
            path = Path(result['routeFile'])
            self.assertTrue(path.is_absolute())
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
            self.assertEqual(json.loads(path.read_text(encoding='utf-8')), route)
            argv, kwargs = self.launches[-1]
            self.assertEqual(argv, ['alacritty', '--working-directory', str(self.cwd), '-e',
                                    'agent-hub', 'open', '--route-file', str(path)])
            self.assertEqual(kwargs['cwd'], str(self.cwd))
            self.assertNotIn('sh', argv)
        self.assertEqual(list(self.bridge.routes.glob('.pending-*')), [])

    def test_missing_legacy_identity_requests_explicit_association(self):
        for request in ({}, {'sessionId': 'not-seen'}, {'agent': 'codex', 'sessionId': 'deleted'}):
            self.assertTrue(self.bridge.open(request)['needsAssociation'])
        self.assertEqual(self.launches, [])
        self.assertFalse(any('new' in argv for argv in self.calls))

    def test_same_native_id_in_two_adapters_is_ambiguous(self):
        for agent in ('codex', 'hermes'):
            self.bridge.observe({'agent': agent, 'sessionId': 'same', 'event': 'SessionStart',
                                 'route': dict(self.route, agente=agent, idMessage='same')})
        self.assertTrue(self.bridge.open({'sessionId': 'same'})['needsAssociation'])
        self.assertEqual(self.launches, [])

    def test_locked_session_blocks_then_stop_releases(self):
        request = {'agent': 'codex', 'sessionId': 'native-session'}
        self.bridge.observe(dict(request, event='PermissionRequest'))
        with self.assertRaisesRegex(module.BridgeError, 'activa'):
            self.bridge.open(request)
        self.assertEqual(self.launches, [])
        self.bridge.observe(dict(request, event='Stop'))
        self.assertTrue(self.bridge.open(request)['ok'])

    def test_deleted_session_and_incorrect_ids_never_launch_or_create(self):
        self.error = 'La conversación o carpeta fue eliminada'
        with self.assertRaisesRegex(module.BridgeError, 'eliminada'):
            self.bridge.open({'route': self.route})
        self.assertEqual(self.launches, [])
        self.assertFalse(any('new' in argv for argv in self.calls))
        self.error = None
        self.response_route = dict(self.route, idMessage='wrong-conversation')
        with self.assertRaisesRegex(module.BridgeError, 'exactamente'):
            self.bridge.open({'route': self.route})
        for route in (dict(self.route, version=True), dict(self.route, idMessage=''), dict(self.route, agente=None)):
            with self.assertRaises(module.BridgeError):
                self.bridge.open({'route': route})
        self.assertEqual(self.launches, [])

    def test_missing_binary_and_adapter_mismatch_no_fallback(self):
        self.bridge.which = lambda name: None
        with self.assertRaisesRegex(module.BridgeError, 'agent-hub'):
            self.bridge.open({'route': self.route})
        with self.assertRaisesRegex(module.BridgeError, 'distintos'):
            self.bridge.open({'agent': 'hermes', 'route': self.route})
        self.assertEqual(self.launches, [])

    def test_double_click_prevents_duplicate_terminal(self):
        request = {'route': self.route}
        self.bridge.open(request)
        with self.assertRaisesRegex(module.BridgeError, 'abierta'):
            self.bridge.open(request)
        self.assertEqual(len(self.launches), 1)

    def test_new_is_explicit_saved_before_launch_and_not_repeated_on_error(self):
        with self.assertRaises(module.BridgeError):
            self.bridge.handle({'action': 'new', 'agent': 'codex', 'folder': 'opaque-project'})
        result = self.bridge.handle({'action': 'new', 'confirmed': True, 'agent': 'codex',
                                     'folder': 'opaque-project', 'sessionId': 'legacy'})
        self.assertEqual(result['route']['idMessage'], 'new-stable')
        self.assertEqual(self.launches, [])
        saved = json.loads(self.bridge.metadata_path('codex', 'legacy').read_text())
        self.assertEqual(saved['route'], result['route'])
        self.assertTrue(list(self.bridge.executions.glob('created-*.json')))

    def test_terminal_apis_are_distinct_and_child_argv_preserved(self):
        child = ['agent-hub', 'open', '--route-file', '/ruta con " ; 日本語.json']
        for adapter, separator in [('alacritty', '-e'), ('kitty', '--'), ('gnome-terminal', '--'),
                                   ('konsole', '-e'), ('wezterm', '--'), ('foot', '--'),
                                   ('xterm', '-e'), ('xfce4-terminal', '--execute')]:
            self.bridge.config = {'terminal': {'program': adapter, 'adapter': adapter}}
            argv = self.bridge.terminal_argv(child, str(self.cwd))
            self.assertEqual(argv[-4:], child)
            self.assertEqual(argv[-5], separator)


if __name__ == '__main__':
    unittest.main()
