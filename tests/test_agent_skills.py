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
            env = {'XDG_STATE_HOME': str(home / 'state'), 'CODEX_HOME': str(old.parent)}
            argv = ['dotfiles-agent-skills', '--source', str(ROOT / 'config/agent-skills')]
            with patch.object(installer.Path, 'home', return_value=home), patch.dict(os.environ, env), patch.object(sys, 'argv', argv):
                installer.main()
                first = old.read_text()
                installer.main()
            self.assertEqual(first, old.read_text())
            self.assertTrue(first.startswith('Reglas previas del usuario.'))
            for base in ('.agents/skills', '.gemini/config/skills'):
                self.assertEqual({p.name for p in (home / base).iterdir()}, set(installer.NAMES))

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
root=Path(sys.argv[1]); skills=sorted((root/'config/agent-skills').glob('*/SKILL.md'))
with tempfile.TemporaryDirectory() as temporary:
    directory=Path(temporary);repo=directory/'repo';repo.mkdir()
    def git(*args): subprocess.run(['git','-C',str(repo),*args],capture_output=True,check=True)
    git('init','-b','main');(repo/'button.css').write_text('button { color: red; }\n')
    git('add','button.css');git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','fixture')
    cache=Cache(':memory:');conn=cache.conn
    for file in skills:Skills(conn).register(file.parent.name,file.read_text())
    task=TaskStore(conn).create({'title':'Cambiar color del botón','objective':'Cambiar solo el color','scope':{'files':['button.css']},'complexity':'trivial','budget':{'max_chars':20000}})
    Workspaces(conn,directory/'state').create(task.id,repo)
    profile={'id':'fixture','skills':[],'context_max_chars':20000}
    pack=Contexts(conn,directory/'state').build(task.id,profile)
    assert {s['id'] for s in pack['skills']}=={p.parent.name for p in skills}
    assert pack['files'][0]['content']=='button { color: red; }\n'
    assert len(json.dumps(pack,ensure_ascii=False))<20000
    assert pack['omitted']==[]
    print('Five skills, requested file and context budget verified without models')
'''
        result = subprocess.run([sys.executable, '-c', code, str(ROOT)], env=dict(os.environ, PYTHONPATH=str(hub)), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
