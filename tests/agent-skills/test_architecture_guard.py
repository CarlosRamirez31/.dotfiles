import importlib.machinery
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
loader=importlib.machinery.SourceFileLoader('architecture_guard',str(ROOT/'bin/dotfiles-architecture-guard'))
spec=importlib.util.spec_from_loader(loader.name,loader)
guard=importlib.util.module_from_spec(spec);loader.exec_module(guard)


class ArchitectureGuardTests(unittest.TestCase):
    def test_missing_draft_read_receipt_and_revision_change(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);project=root/'project';project.mkdir();store=root/'memory';receipts=root/'receipts'
            payload={'tool_name':'apply_patch','tool_input':{'patch':'*** Update File: file.py\n'},'cwd':str(project),'session_id':'one'}
            check=lambda:guard.check(payload,root=store,receipts=receipts)
            self.assertIn('Falta',check())
            folder=guard.memory.initialize(project,store)
            info=guard.memory.save(folder,'architecture','Responsabilidades verificadas\n','missing','draft')
            self.assertIn('borrador',check())
            info=guard.memory.save(folder,'architecture','Definición comprobada: módulo principal\n',info['documents']['architecture']['revision'],'defined')
            self.assertIn('Definición comprobada',check())
            self.assertIsNone(check())
            guard.memory.save(folder,'architecture','Arquitectura actualizada\n',info['documents']['architecture']['revision'],'defined')
            self.assertIn('actualizada',check())
            payload['session_id']='another'
            self.assertIn('actualizada',check())
            self.assertFalse((project/'.git').exists())

    def test_analysis_reads_are_allowed_but_shell_execution_is_gated(self):
        for command in ('rg --files', 'ls -la', 'cat package.json', 'dotfiles-project-context show --project /project'):
            self.assertTrue(guard.readonly(command))
        for command in ('python -c "open(\'x\',\'w\')"', 'rg --pre malicious foo', 'cat x > source.py', 'ls; touch x', 'ls $(touch x)'):
            self.assertFalse(guard.readonly(command),command)
        payload={'toolCall':{'name':'write_to_file','args':{'TargetFile':'/project/src/file.py'}},'workspacePaths':['/project'],'conversationId':'agy-session'}
        name,args,cwd,session=guard.normalize(payload)
        self.assertEqual(session,'agy-session')
        self.assertEqual(guard.normalize({'tool_name':'Shell','tool_input':{'working_directory':'/chosen/project'},'workspace_roots':['/neutral']})[2],Path('/chosen/project'))
        self.assertEqual(guard.targets(name,args,cwd),[Path('/project/src/file.py')])

    def test_each_provider_denies_without_auto_approving_when_ready(self):
        self.assertEqual(guard.reply('codex','missing')['hookSpecificOutput']['permissionDecision'],'deny')
        self.assertEqual(guard.reply('cursor','missing')['permission'],'deny')
        self.assertEqual(guard.reply('hermes','missing')['action'],'block')
        self.assertEqual(guard.reply('antigravity','missing')['decision'],'deny')
        for agent in ('codex','cursor','hermes'):
            self.assertEqual(guard.reply(agent,None),{})
        self.assertEqual(guard.reply('antigravity',None),{'decision':'allow'})
