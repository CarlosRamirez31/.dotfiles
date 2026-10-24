import json
import os
from pathlib import Path
import shlex
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'libexec/coucou-agent-hub'))
from gemini_setup import configure, EVENTS

class GeminiSetupTests(unittest.TestCase):
    def test_preserves_foreign_settings_hooks_and_is_idempotent(self):
        with tempfile.TemporaryDirectory(prefix="Gemini ñ ' $() ") as directory:
            root=Path(directory);relay=root/'coucou hook';relay.touch();relay.chmod(0o700)
            settings=root/'settings.json'
            foreign={'type':'command','command':'other-observer','name':'foreign'}
            original={'hooks':{'BeforeTool':[{'matcher':'read_file','hooks':[foreign]}]},
                      'security':{'auth':{'selectedType':'oauth-personal'}},'model':{'name':'user-choice'}}
            settings.write_text(json.dumps(original))
            self.assertTrue(configure(settings,relay))
            value=json.loads(settings.read_text())
            self.assertEqual(value['security'],original['security'])
            self.assertEqual(value['model'],original['model'])
            self.assertEqual(value['hooks']['BeforeTool'][0]['hooks'][0],foreign)
            for event,mapped in EVENTS.items():
                hook=value['hooks'][event][-1]['hooks'][0]
                self.assertEqual(shlex.split(hook['command']),[str(relay),'--agent','gemini',mapped])
                self.assertNotIn('decision',hook)
            self.assertFalse(value['privacy']['usageStatisticsEnabled'])
            self.assertFalse(value['telemetry']['enabled'])
            self.assertEqual(settings.stat().st_mode&0o777,0o600)
            before=settings.read_bytes();self.assertFalse(configure(settings,relay))
            self.assertEqual(before,settings.read_bytes())
            self.assertEqual(len(list((root/'coucou-backups').iterdir())),1)
    def test_missing_relay_does_not_change_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'settings.json';path.write_text('{}')
            with self.assertRaises(ValueError):configure(path,Path(directory)/'absent')
            self.assertEqual(path.read_text(),'{}')
