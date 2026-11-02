"""Architecture supplies context; native permissions retain every tool decision."""
import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def module(name, file):
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT/'bin'/file))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    result = importlib.util.module_from_spec(spec)
    loader.exec_module(result)
    return result


guard = module('architecture_guard', 'dotfiles-architecture-guard')
installer = module('architecture_installer', 'dotfiles-agent-skills')


class ArchitectureContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.project = self.base/'project'
        self.project.mkdir()
        self.store = self.base/'memory'
        self.payload = {'cwd': str(self.project)}  # Session ID is deliberately absent.
        self.env = patch.dict(os.environ, {})
        self.env.start()
        self.addCleanup(self.env.stop)
        for name in ('DOTFILES_WORKSPACE_DIRECTORY', 'DOTFILES_PROJECT_DIRECTORY'):
            os.environ.pop(name, None)

    def context(self):
        return guard.context(self.payload, root=self.store)

    def test_new_empty_directory_needs_no_registration(self):
        message = self.context()
        self.assertIn('ausente o inaccesible', message)
        self.assertIn('no evidencia de una decisión', message)
        self.assertIn('sin exigir registro previo', message)
        self.assertEqual(list(self.project.iterdir()), [])
        self.assertFalse(self.store.exists())

    def test_existing_defined_draft_and_changed_revision_without_receipts(self):
        folder = guard.memory.initialize(self.project, self.store)
        info = guard.memory.save(folder, 'architecture', 'Área pertinente: adaptadores de agentes\n', 'missing', 'defined')
        with patch.object(guard.memory, 'atomic_write', side_effect=PermissionError('receipts read-only')) as write, patch.object(Path, 'mkdir', side_effect=PermissionError('receipts read-only')):
            first = self.context()
            self.assertIn('Estado: defined', first)
            self.assertIn(str(folder/'architecture.md'), first)
            self.assertIn(info['documents']['architecture']['revision'], first)
            self.assertIn('No se ha acreditado su lectura ni su cobertura', first)
            self.assertEqual(first, self.context())
            write.assert_not_called()
        updated = guard.memory.save(folder, 'architecture', 'Decisión pendiente: contrato de integración\n', info['documents']['architecture']['revision'], 'draft')
        second = self.context()
        self.assertIn('Estado: draft', second)
        self.assertIn('solo genera un aviso, nunca un bloqueo', second)
        self.assertIn('Puedes continuar con la tarea', second)
        self.assertIn('sin exigir confirmación por rutina', second)
        self.assertIn(updated['documents']['architecture']['revision'], second)
        self.assertNotEqual(first, second)

    def test_architecture_advice_allows_implementation_without_forced_confirmation(self):
        for state in ('missing', 'draft', 'defined'):
            with self.subTest(state=state):
                if state != 'missing':
                    folder = guard.memory.initialize(self.project, self.store)
                    doc = guard.memory.describe(folder)['documents']['architecture']
                    guard.memory.save(folder, 'architecture', 'Contrato aún pendiente\n', doc['revision'], state)
                message = self.context()
                self.assertIn('Puedes continuar con la tarea', message)
                self.assertIn('o definir la arquitectura primero', message)
                self.assertIn('Si el usuario pidió implementar, continúa', message)
                self.assertIn('sin exigir confirmación por rutina', message)
                self.assertIn('Se mantienen los controles nativos', message)
                for agent in ('codex', 'cursor', 'antigravity'):
                    output = guard.reply(agent, message)
                    self.assertNotIn('permissionDecision', json.dumps(output))
                    self.assertNotIn('"decision"', json.dumps(output))

    def test_unreadable_memory_is_context_not_a_tool_denial(self):
        with patch.object(guard.memory, 'existing', side_effect=PermissionError('read-only sandbox')):
            self.assertIn('ausente o inaccesible', self.context())
            for agent in ('codex', 'cursor', 'antigravity', 'hermes'):
                self.assertIsNone(guard.check(self.payload, agent, root=self.store, receipts=self.base/'forbidden'))

    def test_unwritable_memory_does_not_turn_resolved_design_into_pending(self):
        folder = guard.memory.initialize(self.project, self.store)
        info = guard.memory.save(folder, 'architecture', 'Contrato comprobado\n', 'missing', 'defined')
        with patch.object(guard.memory, 'atomic_write', side_effect=PermissionError('store read-only')):
            with self.assertRaises(PermissionError):
                guard.memory.save(folder, 'architecture', 'Actualización resuelta\n', info['documents']['architecture']['revision'], 'defined')
            self.assertIn('Estado: defined', self.context())
            self.assertIn('actualización pendiente fuera del código', self.context())
            self.assertIn('puedes continuar', self.context())

    def test_workspace_alias_uses_explicit_source_context(self):
        folder = guard.memory.initialize(self.project, self.store)
        guard.memory.save(folder, 'architecture', 'Source\n', 'missing', 'defined')
        workspace = self.base/'workspace'
        workspace.mkdir()
        with patch.dict(os.environ, {'DOTFILES_WORKSPACE_DIRECTORY': str(workspace), 'DOTFILES_PROJECT_DIRECTORY': str(self.project)}):
            self.assertIn(str(folder/'architecture.md'), guard.context({'cwd': str(workspace)}, root=self.store))

    def test_shell_strings_are_neither_parsed_executed_nor_autoapproved(self):
        marker = self.base/'must-not-exist'
        commands = [
            'rg "foo|bar" .', 'rg --files',
            'git -C /project -c protocol.version=2 --no-pager ls-remote upstream',
            'git clone upstream /authorized/destination',
            'command -v python3', 'python3 --version', 'cmake --build build',
            'python3 -m unittest discover -s tests', 'npm test',
            'ls; touch source.py', 'pwd && python3 -c "open(\'x\',\'w\')"',
            'ls | tee source.py', 'cat x > source.py',
            f'ls $(touch {marker})', f'ls `touch {marker}`',
            'rg --pre malicious pattern', 'rg --pre=malicious pattern',
            f'cat > {self.base}/diagnostico.md',
        ]
        for command in commands:
            with self.subTest(command=command):
                payload = dict(self.payload, tool_name='exec_command', tool_input={'cmd': command})
                with patch.object(guard.memory, 'existing', side_effect=AssertionError('Tool gating must not consult memory')):
                    self.assertIsNone(guard.check(payload))
                result = subprocess.run([sys.executable, str(ROOT/'bin/dotfiles-architecture-guard'), '--agent', 'codex'], input=json.dumps(payload), text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), {})
        self.assertFalse(marker.exists())

    def test_authorized_local_acquisition_and_baseline_without_memory(self):
        upstream = self.base/'upstream.git'
        subprocess.run(['git', 'init', '--bare', str(upstream)], check=True, capture_output=True)
        destination = self.base/'acquired'
        payload = dict(self.payload, tool_name='exec_command', tool_input={'cmd': 'git clone upstream.git acquired'})
        self.assertIsNone(guard.check(payload))
        subprocess.run(['git', '-C', str(self.project), '-c', 'protocol.version=2', '--no-pager', 'ls-remote', str(upstream)], check=True, capture_output=True)
        subprocess.run(['git', 'clone', str(upstream), str(destination)], check=True, capture_output=True)
        self.assertTrue((destination/'.git').is_dir())
        test = destination/'test_baseline.py'
        test.write_text('import unittest\nclass Baseline(unittest.TestCase):\n    def test_python(self):\n        self.assertEqual(2 + 2, 4)\n')
        result = subprocess.run([sys.executable, '-m', 'unittest', 'discover'], cwd=destination, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Ran 1 test', result.stderr)
        self.assertFalse(self.store.exists())

    def test_session_protocols_and_malformed_payload(self):
        self.assertEqual(guard.reply('codex', 'context'), {'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': 'context'}})
        self.assertEqual(guard.reply('cursor', 'context'), {'additional_context': 'context'})
        self.assertEqual(guard.reply('antigravity', 'context'), {'injectSteps': [{'systemMessage': {'systemMessage': 'context'}}]})
        with self.assertRaises(ValueError):
            guard.reply('hermes', 'context')
        for agent in ('codex', 'cursor', 'antigravity'):
            result = subprocess.run([sys.executable, str(ROOT/'bin/dotfiles-architecture-guard'), '--agent', agent, '--event', 'SessionStart'], input='not JSON', text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('No se pudo consultar', json.dumps(json.loads(result.stdout), ensure_ascii=False))
            self.assertNotIn('permissionDecision', result.stdout)
            self.assertNotIn('"decision"', result.stdout)
            self.assertNotIn('"permission"', result.stdout)
        # These adapters cannot emit a neutral PreToolUse decision. Installation removes it.
        for agent in ('cursor', 'antigravity'):
            with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(guard.main(['--agent', agent]), 1)
            self.assertEqual(out.getvalue(), '')


class ArchitectureDistributionTests(unittest.TestCase):
    def test_migration_preserves_mixed_groups_and_is_idempotent(self):
        guard_path = str(ROOT/'bin/dotfiles-architecture-guard')
        for agent in ('codex', 'cursor', 'antigravity'):
            with self.subTest(agent=agent):
                old = {'command': f'{guard_path} --agent {agent}'}
                foreign = {'command': 'security-check --secrets'}
                startup = {'command': 'personal-startup'}
                key = 'dotfiles-architecture' if agent == 'antigravity' else 'hooks'
                pre, start = ('preToolUse', 'sessionStart') if agent == 'cursor' else ('PreToolUse', 'SessionStart')
                data = {key: {pre: [old, foreign] if agent == 'cursor' else [{'matcher': '*', 'hooks': [old, foreign]}], start: [startup]}, 'personal': {'preserve': True}}
                result = installer.architecture_hooks(data, agent, guard_path)
                self.assertEqual(result[key][pre], [foreign] if agent == 'cursor' else [{'matcher': '*', 'hooks': [foreign]}])
                self.assertEqual(result[key][start][0], startup)
                self.assertEqual(result['personal'], {'preserve': True})
                before = json.dumps(result, sort_keys=True)
                self.assertEqual(before, json.dumps(installer.architecture_hooks(result, agent, guard_path), sort_keys=True))

    def test_selective_sync_does_not_install_other_components(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            policy_path = home/'.codex/AGENTS.md'
            policy_path.parent.mkdir()
            policy_path.write_text('Mi identidad\n'+installer.BEGIN+'\nold\n'+installer.END+'\nMis reglas finales\n')
            with patch.object(Path, 'home', return_value=home), patch.dict(os.environ, {'CODEX_HOME': str(home/'.codex'), 'XDG_STATE_HOME': str(home/'state')}), patch.object(sys, 'argv', ['dotfiles-agent-skills', '--architecture-only', '--source', str(ROOT/'config/agent-skills')]), patch.object(installer, 'link', side_effect=AssertionError('No skill link changes')), patch.object(installer.subprocess, 'run', side_effect=AssertionError('No external commands')):
                installer.main()
                before = {p: p.read_bytes() for p in home.rglob('*') if p.is_file() and 'state' not in p.parts}
                installer.main()
                self.assertEqual(before, {p: p.read_bytes() for p in home.rglob('*') if p.is_file() and 'state' not in p.parts})
            policy = policy_path.read_text()
            self.assertTrue(policy.startswith('Mi identidad\n'))
            self.assertTrue(policy.endswith('\nMis reglas finales\n'))
            self.assertNotIn('\nold\n', policy)
            self.assertFalse((home/'.agents').exists())
            self.assertFalse((home/'.cursor/skills').exists())
            for relative, key, pre in (('.codex/hooks.json', 'hooks', 'PreToolUse'), ('.cursor/hooks.json', 'hooks', 'preToolUse'), ('.gemini/config/hooks.json', 'dotfiles-architecture', 'PreToolUse')):
                self.assertNotIn(pre, json.loads((home/relative).read_text())[key])

    def test_hermes_cleanup_preserves_academic_skills_and_personal_rules(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            soul = home/'SOUL.md'
            soul.write_text('Identidad académica\n'+installer.BEGIN+'\ncode policy\n'+installer.END+'\nPreferencias APA\n')
            academic = home/'skills/academic/custom/SKILL.md'
            academic.parent.mkdir(parents=True)
            academic.write_text('Mi skill académica')
            custom = home/'skills/programming/personal/SKILL.md'
            custom.parent.mkdir(parents=True)
            custom.write_text('Contenido ajeno al instalador')
            for name in installer.NATIVE_NAMES:
                path = home/'skills/programming'/name/'SKILL.md'
                path.parent.mkdir(parents=True)
                path.write_text(name)
            for name in ('dotfiles-architecture', 'dotfiles-context-efficiency'):
                path = home/'plugins'/name
                path.mkdir(parents=True)
                (path/'__init__.py').write_text('managed')
            personal_plugin = home/'plugins/academic'
            personal_plugin.mkdir()
            backup = Path(installer.remove_hermes_programming(home, installer.NATIVE_NAMES))
            self.assertEqual(soul.read_text(), 'Identidad académica\n\nPreferencias APA\n')
            self.assertIn('code policy', (backup/'SOUL.md').read_text())
            self.assertEqual(academic.read_text(), 'Mi skill académica')
            self.assertEqual(custom.read_text(), 'Contenido ajeno al instalador')
            self.assertTrue(personal_plugin.is_dir())
            self.assertFalse((home/'plugins/dotfiles-architecture').exists())
            for name in installer.NATIVE_NAMES:
                self.assertFalse((home/'skills/programming'/name).exists())
                self.assertTrue((backup/'skills/programming'/name/'SKILL.md').exists())
            self.assertIsNone(installer.remove_hermes_programming(home, installer.NATIVE_NAMES))

    def test_hermes_cleanup_rejects_broken_markers_before_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            (home/'SOUL.md').write_text(installer.BEGIN)
            with self.assertRaises(ValueError):
                installer.remove_hermes_programming(home, installer.NATIVE_NAMES)
            self.assertEqual((home/'SOUL.md').read_text(), installer.BEGIN)
            self.assertFalse((home/'backups').exists())

    def test_hermes_programming_installation_is_no_longer_available(self):
        with patch.object(sys, 'argv', ['dotfiles-agent-skills', '--hermes', 'fixture']), contextlib.redirect_stderr(io.StringIO()), patch.object(installer.subprocess, 'run') as run:
            with self.assertRaises(SystemExit):
                installer.main()
            run.assert_not_called()

    def test_standalone_hermes_cleanup_payload_and_container_argv(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            (home/'SOUL.md').write_text('academic')
            with patch.object(installer.subprocess, 'run') as run:
                installer.uninstall_hermes_programming('--not-an-option')
            argv = run.call_args.args[0]
            self.assertEqual(argv[:5], ['podman', 'exec', '-i', '--', '--not-an-option'])
            code = argv[-1].replace('/opt/hermes/.hermes', str(home))
            with contextlib.redirect_stdout(io.StringIO()) as out:
                exec(compile(code, '<cleanup>', 'exec'), {})
            self.assertEqual(json.loads(out.getvalue()), {'backup': None})
            self.assertEqual((home/'SOUL.md').read_text(), 'academic')
