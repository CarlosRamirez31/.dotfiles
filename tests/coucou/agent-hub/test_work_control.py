import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'libexec/coucou-agent-hub'))
from work_control import control
from agent_hub_terminal import BridgeError

class WorkControlTests(unittest.TestCase):
    def setUp(self):
        self.calls=[]
        def run(argv,**options):
            self.calls.append((argv,options))
            return subprocess.CompletedProcess(argv,1,json.dumps({'id':'RUN-001','title':'fixture','status':'waiting_human',
                'tasks':[{'id':'TASK-001','status':'waiting_human','contract':{'title':'fixture'}}]}),'')
        self.bridge=SimpleNamespace(which=lambda name:'/bin/'+name,run=run)
    def test_plan_opaque_text_uses_separate_argv_and_no_models(self):
        query='ñ " ; $(do-not-run)'
        result=control(self.bridge,{'operation':'plan','query':query,'agent':'codex'})
        self.assertTrue(result['ok'])
        self.assertEqual(self.calls[0][0],['agent-hub','work','run','request','--intent',query,'--agent','codex','--json'])
        self.assertNotIn('shell',self.calls[0][1])
    def test_pending_human_result_is_visible_and_execute_does_not_abandon_after_twenty_seconds(self):
        result=control(self.bridge,{'operation':'execute','id':'RUN-001'})
        self.assertIn('waiting_human',result['text'])
        self.assertIsNone(self.calls[0][1]['timeout'])
    def test_execution_open_preserves_complete_exact_route(self):
        route={'version':1,'agente':'hermes','idCarpeta':'opaque project','idMessage':'handoff-exact'}
        calls=[]
        self.bridge.hub=lambda *argv:calls.append(argv) or {'route':route,'native_id':'native-session'}
        self.bridge.associate=lambda request:calls.append(('associate',request))
        self.bridge.open=lambda request:calls.append(('open',request)) or {'ok':True}
        result=control(self.bridge,{'operation':'open-execution','id':'EXEC-007'})
        self.assertTrue(result['ok'])
        self.assertEqual(calls[0],('work','execution','route','EXEC-007','--json'))
        self.assertEqual(calls[-1][1]['route'],route)
        self.assertEqual(calls[-1][1]['sessionId'],'native-session')

    def test_auto_intake_and_refinement_use_public_cli_and_report_questions(self):
        payload={'status':'needs_input','summary':'Define architecture','questions':['Which stack?'],
                 'architecture':{'path':'/external/architecture.md'},
                 'run':{'id':'RUN-001','status':'pending','configuration':{'request':{'plan':{'files':[],'checks':[]}}}}}
        self.bridge.run=lambda argv,**options:self.calls.append((argv,options)) or subprocess.CompletedProcess(argv,0,json.dumps(payload),'')
        result=control(self.bridge,{'operation':'plan','query':'create project /project','agent':None})
        self.assertIn('--auto',self.calls[0][0]);self.assertIsNone(self.calls[0][1]['timeout'])
        self.assertIn('/definir RUN-001',result['text']);self.assertIn('Which stack?',result['text'])
        control(self.bridge,{'operation':'refine','id':'RUN-001','query':'Use Python','automatic':True})
        self.assertIn('--continue-run',self.calls[-1][0])

    def test_invalid_run_never_launches(self):
        with self.assertRaises(BridgeError):control(self.bridge,{'operation':'execute','id':'--last'})
        self.assertEqual(self.calls,[])

if __name__=='__main__':unittest.main()
