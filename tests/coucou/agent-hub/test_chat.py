import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str((Path(__file__).resolve().parents[3] / 'libexec/coucou-agent-hub')))
from agent_hub_terminal import HubTerminal, BridgeError, read_json
from native_chat import send

class ChatTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="chat ñ ' $() ")
        self.addCleanup(self.temp.cleanup)
        self.bridge = HubTerminal(self.temp.name, config={})
        self.commands = []
        self.agent = 'codex'
        self.native = 'exact-native'
        self.fail = False
        self.events = None
        self.route = {'version':1,'agente':'codex','idCarpeta':'opaque folder','idMessage':self.native}
        self.bridge.hub = self.hub
        self.bridge.spawn = self.spawn
        self.bridge.validate = lambda route: (Path(self.temp.name)/'route', self.temp.name)
    def hub(self, *argv):
        if argv[0] == 'agents':
            return [{'id':'codex','installed':True}, {'id':'gemini','installed':True}, {'id':'hermes','installed':True,'container':'dev-podman'}]
        if argv[0] == 'conversations':
            return [{'id':self.native,'route':self.route}]
        raise AssertionError(argv)
    def spawn(self, argv, **kw):
        self.commands.append((argv, kw['stdin'].read().decode()))
        assert 'shell' not in kw
        events = self.events
        if events is None:
            events = ([{'type':'thread.started','thread_id':self.native},
                       {'type':'item.completed','item':{'type':'agent_message','text':'respuesta exacta'}}]
                      if self.agent == 'codex' else
                      [{'type':'system','subtype':'init','session_id':self.native},
                       {'type':'result','session_id':self.native,'exit_code':0,'text':'respuesta exacta'}])
        return type('Process', (), {'stdout':io.StringIO(''.join(json.dumps(e)+'\n' for e in events)),
                                   'wait':lambda p: 1 if self.fail else 0})()
    def test_new_and_resume_exact_codex_id_stdin_no_shell(self):
        query = 'Hola 日本語 " ; $(not-run) `no`'
        self.assertEqual(send(self.bridge, {'agent':'codex','query':query})['text'], 'respuesta exacta')
        send(self.bridge, {'agent':'codex','query':'continúa'})
        self.assertEqual(self.commands[0][0], ['codex','exec','--json','--skip-git-repo-check','-'])
        self.assertEqual(self.commands[0][1], query)
        self.assertEqual(self.commands[1][0], ['codex','exec','resume',self.native,'--json','--skip-git-repo-check','-'])
        self.assertEqual(read_json(Path(self.temp.name)/'chat/codex.json')['route'],self.route)
    def test_hermes_native_events_container_and_resume(self):
        self.agent = 'hermes'; self.route['agente'] = 'hermes'
        # Installed state is in host home; arbitrary test dirs need not be mounted.
        with patch('native_chat.private_dir', side_effect=lambda p: Path(p).mkdir(parents=True,exist_ok=True) or Path(p)):
            send(self.bridge, {'agent':'hermes','query':'primero'})
            send(self.bridge, {'agent':'hermes','query':'segundo'})
        argv = self.commands[-1][0]
        self.assertEqual(argv[:3], ['podman','exec','-i'])
        self.assertIn('/usr/local/bin/hermes', argv)
        self.assertEqual(argv[-2:], ['--resume',self.native])
    def gemini_events(self):
        self.agent = 'gemini'; self.route['agente'] = 'gemini'
        self.events = [{'type':'init','session_id':self.native},
                       {'type':'message','role':'user','content':'do not display'},
                       {'type':'message','role':'assistant','content':'respuesta ','delta':True},
                       {'type':'message','role':'assistant','content':'exacta','delta':True},
                       {'type':'result','status':'success'}]
    def test_gemini_native_init_chunks_resume_and_reset(self):
        self.gemini_events()
        self.assertEqual(send(self.bridge, {'agent':'gemini','query':'日本語 ; $(no)'})['text'],'respuesta exacta')
        send(self.bridge, {'agent':'gemini','query':'continúa'})
        self.assertEqual(self.commands[0][0],['gemini','--output-format','stream-json','--prompt','Respond to the user message supplied on stdin.'])
        self.assertEqual(self.commands[0][1],'日本語 ; $(no)')
        self.assertEqual(self.commands[1][0][-2:],['--resume',self.native])
        self.assertEqual(read_json(Path(self.temp.name)/'chat/gemini.json')['route'],self.route)
        self.assertTrue(self.bridge.handle({'action':'chat-reset','agent':'gemini'})['ok'])
        self.assertFalse((Path(self.temp.name)/'chat/gemini.json').exists())
    def test_gemini_failure_preserves_verified_native_id(self):
        self.gemini_events(); self.fail=True
        self.events[-1]={'type':'result','status':'error','error':{'message':'quota'}}
        with self.assertRaises(BridgeError):send(self.bridge,{'agent':'gemini','query':'one'})
        self.assertEqual(read_json(Path(self.temp.name)/'chat/gemini.json')['nativeId'],self.native)
        self.gemini_events();self.fail=False
        send(self.bridge,{'agent':'gemini','query':'retry'})
        self.assertEqual(self.commands[-1][0][-2:],['--resume',self.native])
    def test_gemini_changed_session_never_replaces_selected_identity(self):
        self.gemini_events();send(self.bridge,{'agent':'gemini','query':'one'})
        self.events[0]['session_id']='wrong-session'
        with self.assertRaisesRegex(BridgeError,'otra identidad'):
            send(self.bridge,{'agent':'gemini','query':'two'})
        self.assertEqual(read_json(Path(self.temp.name)/'chat/gemini.json')['nativeId'],self.native)
    def test_alias_resolves_only_exact_public_route(self):
        self.route['idMessage'] = 'handoff-exact'
        send(self.bridge, {'agent':'codex','query':'continúa','route':self.route})
        self.assertIn(self.native,self.commands[0][0])
        self.assertNotIn('handoff-exact',self.commands[0][0])
    def test_deleted_or_mismatched_route_never_creates(self):
        other = dict(self.route,idMessage='deleted')
        with self.assertRaises(BridgeError):
            send(self.bridge, {'agent':'codex','query':'hola','route':other})
        self.assertEqual(self.commands,[])
    def test_unknown_start_identity_does_not_repeat_creation(self):
        self.events = []; self.fail = True
        with self.assertRaises(BridgeError): send(self.bridge, {'agent':'codex','query':'uno'})
        with self.assertRaisesRegex(BridgeError,'ID verificable'): send(self.bridge, {'agent':'codex','query':'dos'})
        self.assertEqual(len(self.commands),1)
    def test_failed_turn_keeps_native_identity(self):
        self.fail = True
        with self.assertRaises(BridgeError): send(self.bridge, {'agent':'codex','query':'uno'})
        self.fail = False
        send(self.bridge, {'agent':'codex','query':'dos'})
        self.assertIn('resume',self.commands[-1][0])
    def test_active_lock_and_double_send(self):
        import fcntl
        directory = Path(self.temp.name)/'chat'; directory.mkdir()
        with open(directory/'codex.lock','w') as guard:
            fcntl.flock(guard,fcntl.LOCK_EX)
            with self.assertRaisesRegex(BridgeError,'respondiendo'):
                send(self.bridge,{'agent':'codex','query':'hola'})
        self.assertEqual(self.commands,[])
    def test_explicit_new_chat_archives_previous_route(self):
        send(self.bridge, {'agent':'codex','query':'uno'})
        self.assertTrue(self.bridge.handle({'action':'chat-reset','agent':'codex'})['ok'])
        self.assertFalse((Path(self.temp.name)/'chat/codex.json').exists())
        archived = list((Path(self.temp.name)/'chat/archive').glob('*.json'))
        self.assertEqual(read_json(archived[0])['nativeId'],self.native)
        send(self.bridge, {'agent':'codex','query':'dos'})
        self.assertNotIn('resume',self.commands[-1][0])

    def test_wrong_agent_never_starts(self):
        with self.assertRaises(BridgeError):
            send(self.bridge,{'agent':'hermes','query':'hola','route':self.route})
        self.assertEqual(self.commands,[])

if __name__ == '__main__': unittest.main()
