"""Exercise shared directory identity and concurrent notes without Git."""
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'bin/dotfiles-project-context'
loader = importlib.machinery.SourceFileLoader('project_context', str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
context = importlib.util.module_from_spec(spec)
loader.exec_module(context)


class DirectoryMemoryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.root / 'code/ppe'
        self.project.mkdir(parents=True)
        self.store = self.root / 'notes'

    def test_five_sessions_share_one_external_record_without_git(self):
        before = list(self.project.iterdir())
        command = [str(SCRIPT), 'init', '--project', str(self.project), '--root', str(self.store)]
        sessions = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(5)]
        folders = set()
        for process in sessions:
            output, error = process.communicate(timeout=5)
            self.assertEqual(process.returncode, 0, error)
            folders.add(json.loads(output)['context_directory'])
        self.assertEqual(len(folders), 1)
        self.assertEqual(list(self.project.iterdir()), before)
        self.assertFalse((self.project / '.git').exists())
        self.assertFalse(Path(next(iter(folders))).is_relative_to(self.project))

    def test_subdirectories_and_symlinks_reuse_the_registered_directory(self):
        folder = context.initialize(self.project, self.store)
        nested = self.project / 'src/services'
        nested.mkdir(parents=True)
        self.assertEqual(context.existing(nested, self.store), folder)
        alias = self.root / 'alias'
        alias.symlink_to(self.project, target_is_directory=True)
        self.assertEqual(context.initialize(context.project_path(alias), self.store), folder)

    def test_same_name_different_directory_is_not_merged(self):
        other = self.root / 'other/ppe'
        other.mkdir(parents=True)
        self.assertNotEqual(context.initialize(self.project, self.store), context.initialize(other, self.store))

    def test_concurrent_writes_cannot_lose_a_newer_document(self):
        folder = context.initialize(self.project, self.store)
        first = context.save(folder, 'architecture', 'Version A\n', 'missing')
        revision = first['documents']['architecture']['revision']
        context.save(folder, 'architecture', 'Version B\n', revision)
        with self.assertRaisesRegex(ValueError, 'Otra conversación'):
            context.save(folder, 'architecture', 'Obsolete version\n', revision)
        self.assertEqual((folder / 'architecture.md').read_text(), 'Version B\n')
        self.assertFalse((folder / 'decisions.md').exists())

    def test_store_cannot_be_inside_the_project(self):
        with self.assertRaises(ValueError):
            context.initialize(self.project, self.project / 'agent-notes')
        self.assertEqual(list(self.project.iterdir()), [])

    def test_container_mount_uses_the_same_host_identity(self):
        with patch.object(context.Path, 'home', return_value=Path('/home/example')):
            self.assertEqual(context.canonical(Path('/host-home/Documents/ppe')), '/home/example/Documents/ppe')
            self.assertEqual(context.default_root(Path('/host-home/Documents/ppe')), Path('/host-home/Documents/Agentes/proyectos'))


if __name__ == '__main__':
    unittest.main()
