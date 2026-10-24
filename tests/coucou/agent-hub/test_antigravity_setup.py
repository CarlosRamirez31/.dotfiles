import json
from pathlib import Path
import shlex
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'libexec/coucou-agent-hub'))
from antigravity_setup import configure,EVENTS

class AntigravitySetupTests(unittest.TestCase):
    def test_preserves_other_hooks_and_quotes_observer_path(self):
        with tempfile.TemporaryDirectory(prefix="agy ñ ' $() ") as directory:
            root=Path(directory);observer=root/'observer.py';observer.touch()
            hooks=root/'hooks.json';foreign={'PostToolUse':[{'hooks':[{'command':'my-linter'}]}]}
            hooks.write_text(json.dumps({'foreign':foreign}))
            self.assertTrue(configure(hooks,observer));value=json.loads(hooks.read_text())
            self.assertEqual(value['foreign'],foreign)
            self.assertEqual(set(value['coucou-cli-observer']),set(EVENTS))
            for event in EVENTS:
                hook=value['coucou-cli-observer'][event][0]['hooks'][0]
                self.assertEqual(shlex.split(hook['command']),['python3','-B',str(observer),event])
                self.assertEqual(hook['timeout'],8)
            before=hooks.read_bytes();self.assertFalse(configure(hooks,observer))
            self.assertEqual(before,hooks.read_bytes());self.assertEqual(hooks.stat().st_mode&0o777,0o600)
            self.assertEqual(len(list((root/'coucou-backups').iterdir())),1)
    def test_missing_observer_keeps_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'hooks.json';path.write_text('{}')
            with self.assertRaises(ValueError):configure(path,Path(directory)/'absent')
            self.assertEqual(path.read_text(),'{}')
