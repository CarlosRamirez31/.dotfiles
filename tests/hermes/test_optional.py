#!/usr/bin/env python3
"""Offline checks: optional selection, portable payload and private-data boundary."""
import importlib.util,os,subprocess,tempfile,unittest
from pathlib import Path
REPO=Path(__file__).resolve().parents[2];COMPONENT=REPO/'environments/hermes'
spec=importlib.util.spec_from_file_location('hermes_configure',COMPONENT/'configure.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class OptionalHermes(unittest.TestCase):
    def selected(self,*args):
        return subprocess.check_output([str(REPO/'install.sh'),'--dry-run',*args],text=True).strip().split(': ',1)[1].split()
    def test_default_and_all_exclude_hermes(self):
        self.assertNotIn('hermes',self.selected());self.assertEqual(self.selected(),self.selected('all'))
    def test_only_explicit_selection_installs_hermes(self):
        self.assertEqual(['hermes'],self.selected('hermes'))
        self.assertEqual(self.selected('all')+['hermes'],self.selected('hermes','all','hermes'))
        self.assertEqual(['workbench','hermes'],self.selected('hermes','workbench'))
    def test_invalid_component_fails_before_installation(self):
        p=subprocess.run([str(REPO/'install.sh'),'--dry-run','unknown'],capture_output=True,text=True)
        self.assertEqual(p.returncode,2);self.assertNotIn('Authenticating sudo',p.stdout)
    def test_portable_payload_and_repeat_render(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'render';home=Path(d)/'user with spaces';backup=Path(d)/'backup'
            module.render_payload(COMPONENT,target,home,backup)
            first={p.relative_to(target):p.read_bytes() for p in target.rglob('*') if p.is_file()}
            module.render_payload(COMPONENT,target,home,backup)
            self.assertEqual(first,{p.relative_to(target):p.read_bytes() for p in target.rglob('*') if p.is_file()})
            self.assertFalse(backup.exists())
            for p in target.rglob('*'):
                if not p.is_file():continue
                text=p.read_text()
                self.assertNotIn('@HOST_HOME@',text);self.assertNotIn('/home/beambollow',text)
                if p.suffix=='.py' or text.startswith('#!/usr/bin/env python'):compile(text,str(p),'exec')
                if p.suffix=='.lua':subprocess.run(['luac','-p',str(p)],check=True)
            self.assertIn(str(home/'Documents/Universidad'),(target/'bin/presentacion.py').read_text())
            self.assertTrue((target/'bin/host_hotkeys.py').is_file())
    def test_existing_provider_and_preferences_are_preserved(self):
        data={'model':{'provider':'custom','model':'my-model'},'skills':{'auto_load':['my-existing-skill'],'config':{'other_skill':{'value':42}}},'terminal':{'timeout':90},'private_setting':'keep-this'}
        home=Path('/home/another-user');result=module.merge_settings(data,home)
        self.assertEqual(result['model'],{'provider':'custom','model':'my-model'})
        self.assertEqual(result['private_setting'],'keep-this')
        self.assertEqual(result['terminal']['timeout'],90)
        self.assertEqual(result['terminal']['cwd'],str(home/'Documents/Universidad'))
        self.assertEqual(result['skills']['config']['other_skill'],{'value':42})
        self.assertEqual(result['skills']['auto_load'],['my-existing-skill','humanize-global'])
        self.assertFalse(result['cli']['expose_on_path'])
        module.merge_settings(result,home)
        self.assertEqual(result['skills']['auto_load'].count('humanize-global'),1)
    def test_no_runtime_secrets_or_browser_data(self):
        forbidden={'.env','auth.json','cookies.sqlite','state.json','installed-packages.json','.parentlock','prefs.js','SOUL.md'}
        for p in COMPONENT.rglob('*'):
            self.assertNotIn(p.name,forbidden)
            if p.is_file() and p.suffix not in {'.pdf','.docx','.pyc'} and ('payload' in p.parts or 'skills' in p.parts):
                self.assertNotIn('Respaldo-StealthIt-Hermes',p.read_text())
        self.assertEqual({'user.js'},{p.name for p in (COMPONENT/'payload/firefox-profile').iterdir()})
if __name__=='__main__':unittest.main()
