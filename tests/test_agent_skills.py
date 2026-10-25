"""Check policy installation and bounded Hub context without model execution."""
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('shared_programming_skills', str(ROOT / 'bin/dotfiles-agent-skills'))
spec = importlib.util.spec_from_loader(loader.name, loader)
installer = importlib.util.module_from_spec(spec)
loader.exec_module(installer)


class ProgrammingSkillsTests(unittest.TestCase):
    def test_policy_merge_preserves_personal_content_and_is_idempotent(self):
        existing = '# Identidad personal\nContenido anterior.\n'
        first = installer.merge_policy(existing, 'Preferencias v1')
        self.assertTrue(first.startswith(existing))
        self.assertEqual(first, installer.merge_policy(first, 'Preferencias v1'))
        updated = installer.merge_policy(first, 'Preferencias v2')
        self.assertIn('Contenido anterior.', updated)
        self.assertNotIn('Preferencias v1', updated)
        with self.assertRaises(ValueError):
            installer.merge_policy(installer.BEGIN, 'No sobrescribir')

    def test_skill_link_preserves_unrelated_skill(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source'
            source.mkdir()
            target = root / 'target'
            installer.link(source, target)
            installer.link(source, target)
            self.assertEqual(target.resolve(), source)
            occupied = root / 'occupied'
            occupied.mkdir()
            (occupied / 'SKILL.md').write_text('personal')
            with self.assertRaises(ValueError):
                installer.link(source, occupied)
            self.assertEqual((occupied / 'SKILL.md').read_text(), 'personal')

    def test_installer_preserves_global_rules_and_repeats_safely(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            old = home / '.codex/AGENTS.md'
            old.parent.mkdir()
            old.write_text('Reglas previas del usuario.\n')
            personal = {'hooks': {'SessionStart': [{'hooks': [{'type': 'command', 'command': 'personal-hook'}]}]}}
            (old.parent/'hooks.json').write_text(__import__('json').dumps(personal))
            env = {'XDG_STATE_HOME': str(home / 'state'), 'CODEX_HOME': str(old.parent)}
            argv = ['dotfiles-agent-skills', '--source', str(ROOT / 'config/agent-skills')]
            with patch.object(installer.Path, 'home', return_value=home), patch.dict(os.environ, env), patch.object(sys, 'argv', argv):
                installer.main()
                first = old.read_text()
                first_hooks = {str(p.relative_to(home)): p.read_text() for p in home.rglob('hooks.json')}
                installer.main()
                self.assertEqual(first_hooks, {str(p.relative_to(home)): p.read_text() for p in home.rglob('hooks.json')})
            hooks = __import__('json').loads((home / '.cursor/hooks.json').read_text())
            self.assertEqual(len(hooks['hooks']['sessionStart']), 1)
            self.assertEqual(first, old.read_text())
            self.assertTrue(first.startswith('Reglas previas del usuario.'))
            codex = __import__('json').loads((old.parent/'hooks.json').read_text())
            self.assertEqual(codex['hooks']['SessionStart'][0], personal['hooks']['SessionStart'][0])
            self.assertEqual(len(codex['hooks']['SessionStart']), 2)
            agy = __import__('json').loads((home/'.gemini/config/hooks.json').read_text())
            self.assertEqual(len(agy['dotfiles-context-efficiency']['SessionStart']), 1)
            for base in ('.agents/skills', '.gemini/config/skills', '.cursor/skills'):
                self.assertEqual({p.name for p in (home / base).iterdir()}, set(installer.NATIVE_NAMES))

    def test_session_hook_injects_only_startup_summary_with_native_protocols(self):
        import runpy
        helper = runpy.run_path(str(ROOT/'bin/dotfiles-session-context'))
        content = (ROOT/'config/agent-skills/context-efficiency/SKILL.md').read_text()
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            skill = home/'.config/agent-skills/context-efficiency/SKILL.md'
            skill.parent.mkdir(parents=True)
            skill.write_text(content)
            policy = skill.parent.parent/'AGENTS.md'
            policy.write_text('Personal programming preferences.')
            with patch.object(Path, 'home', return_value=home):
                codex = helper['payload']('codex')['hookSpecificOutput']
                self.assertEqual(codex['hookEventName'], 'SessionStart')
                agy = helper['payload']('antigravity')['injectSteps'][0]['systemMessage']['systemMessage']
                cursor = helper['payload']('cursor')['additional_context']
                self.assertEqual(codex['additionalContext'], agy)
                self.assertIn('Prioriza exactitud y trabajo completo.', agy)
                self.assertNotIn('## Guía bajo demanda', agy)
                self.assertNotIn('Al transferir contexto conserva', agy)
                self.assertLess(len(agy), 600)
                self.assertIn(policy.read_text(), cursor)
                self.assertTrue(cursor.endswith(agy))
                skill.write_text(content+'\nUpdated detailed guide.\n')
                self.assertEqual(helper['skill_context'](), agy)
                skill.write_text(content.replace('Prioriza exactitud y trabajo completo.', 'Updated summary.'))
                self.assertIn('Updated summary.', helper['skill_context']())
                skill.write_text('No startup marker')
                with self.assertRaises(ValueError):
                    helper['skill_context']()
                skill.write_text('\n## Inicio de sesión\n' + 'x'*901)
                with self.assertRaises(ValueError):
                    helper['skill_context']()
                skill.write_text('x'*16001)
                with self.assertRaises(ValueError):
                    helper['skill_context']()
                skill.unlink()
                with self.assertRaises(OSError):
                    helper['skill_context']()

    def test_hermes_context_is_registered_once_as_native_session_section(self):
        from unittest.mock import Mock
        namespace = {}
        exec(installer.hermes_context_plugin(), namespace)
        ctx = Mock()
        namespace['register'](ctx)
        ctx.register_system_prompt_section.assert_called_once()
        args, kwargs = ctx.register_system_prompt_section.call_args
        self.assertEqual(args[0], 'dotfiles.context-efficiency')
        self.assertEqual(kwargs['max_chars'], 4000)
        with patch.object(namespace['runpy'], 'run_path', return_value={'skill_context': lambda path: 'loaded '+path.name}):
            self.assertEqual(args[1]({}), 'loaded SKILL.md')
        with patch.object(namespace['runpy'], 'run_path', return_value={'skill_context': lambda path: 'x'*4001}):
            with self.assertRaises(ValueError):
                args[1]({})
        ctx.register_hook.assert_not_called()

    @unittest.skipUnless((Path.home() / 'Documents/Programacion/codex-hub/agent_hub').exists(), 'Local Agent Hub is optional')
    def test_hub_context_includes_skills_inside_the_budget(self):
        hub = Path.home() / 'Documents/Programacion/codex-hub'
        code = r'''
from pathlib import Path
import json,subprocess,sys,tempfile
from agent_hub.cache import Cache
from agent_hub.engine.skills import Skills
from agent_hub.engine.tasks import TaskStore
from agent_hub.engine.workspace import Workspaces
from agent_hub.engine.context import Contexts
root=Path(sys.argv[1]); names=('surgical-edits','anti-overengineering','repo-scaffold','appsec-guardrail','software-architect','context-efficiency'); skills=sorted(root/'config/agent-skills'/name/'SKILL.md' for name in names)
with tempfile.TemporaryDirectory() as temporary:
    directory=Path(temporary);repo=directory/'repo';repo.mkdir()
    def git(*args): subprocess.run(['git','-C',str(repo),*args],capture_output=True,check=True)
    git('init','-b','main');(repo/'button.css').write_text('button { color: red; }\n')
    git('add','button.css');git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','fixture')
    cache=Cache(':memory:');conn=cache.conn
    for file in skills:Skills(conn).register(file.parent.name,file.read_text())
    task=TaskStore(conn).create({'title':'Cambiar color del botón','objective':'Cambiar solo el color','scope':{'files':['button.css']},'complexity':'trivial','permissions':{'filesystem':'write'},'budget':{'max_chars':20000}})
    Workspaces(conn,directory/'state').create(task.id,repo)
    profile={'id':'fixture','skills':[],'context_max_chars':20000}
    pack=Contexts(conn,directory/'state').build(task.id,profile)
    assert {s['id'] for s in pack['skills']}=={p.parent.name for p in skills}-{'repo-scaffold','software-architect','context-efficiency'}
    assert sum(len(s['content']) for s in pack['skills']) < sum(len(p.read_text()) for p in skills if p.parent.name != 'context-efficiency')
    assert pack['files'][0]['content']=='button { color: red; }\n'
    assert len(json.dumps(pack,ensure_ascii=False))<20000
    assert pack['omitted']==[]
    print('Relevant skills, requested file and context budget verified without models')
'''
        result = subprocess.run([sys.executable, '-c', code, str(ROOT)], env=dict(os.environ, PYTHONPATH=str(hub)), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
