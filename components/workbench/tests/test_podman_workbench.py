"""Regression checks for disposable homes and protecting existing containers."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / 'podman/workbench.py'
spec = importlib.util.spec_from_file_location('workbench', MODULE)
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


class WorkbenchTests(unittest.TestCase):
    def test_documents_link_preserves_private_files_and_shared_files(self):
        spec = importlib.util.spec_from_file_location('documents', MODULE.parent / 'share_documents.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / 'internal'
            shared = Path(directory) / 'host/Documents'
            (home / 'Documents').mkdir(parents=True)
            shared.mkdir(parents=True)
            (home / 'Documents/only-in-container.txt').write_text('private')
            (shared / 'project.txt').write_text('host')
            backup = module.share_documents(home, shared)
            self.assertEqual((backup / 'only-in-container.txt').read_text(), 'private')
            self.assertEqual((home / 'Documents/project.txt').read_text(), 'host')
            (home / 'Documents/project.txt').write_text('edited')
            self.assertEqual((shared / 'project.txt').read_text(), 'edited')
            self.assertIsNone(module.share_documents(home, shared))
            self.assertEqual((backup / 'only-in-container.txt').read_text(), 'private')

    def info(self, name, mounts=None):
        return {'Config': {'Labels': {'manager': w.MANAGER}},
                'State': {'Running': True}, 'Mounts': mounts or [
                    {'Type': 'bind', 'Destination': '/host-home', 'Source': str(w.HOME)}]}

    def test_distinct_names_and_no_external_home_volume(self):
        names = {p['name'] for p in w.PROFILES.values()}
        self.assertEqual(names, {'dev-podman', 'parrotos-podman', 'kali-podman'})
        for profile in w.PROFILES.values():
            args = w.create_args(profile, profile['image'])
            self.assertIn('--image-volume=ignore', args)
            self.assertIn('--userns=keep-id', args)
            mounts = [args[i+1] for i, item in enumerate(args) if item == '--mount']
            self.assertIn(f'type=bind,source={w.HOME},destination=/host-home,rw', mounts)
            self.assertFalse(any(f'destination={w.HOME}' in mount for mount in mounts))
            self.assertFalse(any('podman.sock' in mount or 'docker.sock' in mount for mount in mounts))
            self.assertNotIn('--privileged', args)
            self.assertNotIn('--replace', args)
            self.assertFalse(any('destination=/tmp/.X11-unix,' in mount for mount in mounts))
            self.assertFalse(any('workbench.Xauthority' in mount for mount in mounts))

    def test_refuses_container_with_wrong_owner_label(self):
        info = self.info('dev-podman')
        info['Config']['Labels']['manager'] = 'distrobox'
        with patch.object(w, 'inspect', return_value=info), self.assertRaises(RuntimeError):
            w.managed('dev-podman')

    def test_rejects_shared_home_and_unexpected_volumes(self):
        bad_mounts = [
            {'Type': 'bind', 'Destination': str(w.HOME), 'Source': str(w.HOME)},
            {'Type': 'bind', 'Destination': str(w.HOME / '.config'), 'Source': str(w.HOME / '.config')},
            {'Type': 'bind', 'Destination': '/tmp/.X11-unix', 'Source': '/tmp/.X11-unix'},
            {'Type': 'volume', 'Destination': '/data', 'Source': '/volumes/db'},
            {'Type': 'bind', 'Destination': '/run/docker.sock', 'Source': '/run/docker.sock'},
        ]
        for mount in bad_mounts:
            info = self.info('dev-podman')
            info['Mounts'].append(mount)
            with patch.object(w, 'managed', return_value=info), self.assertRaises(RuntimeError):
                w.verify('dev')

    def test_completed_environment_never_recopies_home(self):
        with patch.object(w, 'inspect', return_value=self.info('dev-podman')), \
             patch.object(w, 'managed'), patch.object(w, 'start'), \
             patch.object(w, 'has_marker', return_value=True), patch.object(w, 'verify'), \
             patch.object(w, 'pipe_tar') as copy, patch.object(w, 'pod') as pod:
            w.setup('dev')
            copy.assert_not_called()
            pod.assert_not_called()

    def test_runtime_error_is_not_treated_as_missing_container(self):
        with patch.object(w.subprocess, 'run', return_value=subprocess.CompletedProcess([], 125)), \
             self.assertRaises(RuntimeError):
            w.inspect('dev-podman')

    def test_snapshot_reads_source_without_pausing_or_copying_mounts(self):
        with patch.object(w, 'inspect', side_effect=[None, self.info('dev')]), \
             patch.object(w, 'start'), patch.object(w, 'execute') as execute, \
             patch.object(w, 'pipe_tar'), patch.object(w, 'seed_home'), \
             patch.object(w, 'has_marker', return_value=False), patch.object(w, 'verify'), \
             patch.object(w, 'mark'), patch.object(w, 'integrate_dev'), patch.object(w, 'pod') as pod, \
             patch.object(w.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)):
            w.setup('dev')
            commits = [call.args for call in pod.call_args_list if call.args[0] == 'commit']
            self.assertEqual(len(commits), 1)
            self.assertIn('--pause=false', commits[0])
            self.assertIn('--include-volumes=false', commits[0])
            self.assertTrue(all(call.args[0] == 'dev-podman' for call in execute.call_args_list))
            self.assertFalse(any(call.args[0] in ('rm', 'stop', 'kill', 'prune') for call in pod.call_args_list))

    def test_fresh_dev_does_not_require_the_original_or_snapshot(self):
        with patch.object(w, 'inspect', return_value=None) as inspect, \
             patch.object(w, 'start'), patch.object(w, 'execute') as execute, \
             patch.object(w, 'pipe_tar'), patch.object(w, 'seed_home'), \
             patch.object(w, 'has_marker', return_value=False), patch.object(w, 'verify'), \
             patch.object(w, 'mark'), patch.object(w, 'integrate_dev'), patch.object(w, 'pod') as pod:
            w.setup('dev', fresh=True)
            inspect.assert_called_once_with('dev-podman')
            self.assertFalse(any(call.args[0] == 'commit' for call in pod.call_args_list))
            self.assertTrue(any('yes' in call.args and 'neovim' in call.args for call in execute.call_args_list))

    def test_security_recipes_do_not_install_development_stacks(self):
        banned = {'flutter', 'android-sdk', 'dbeaver', 'dotnet-sdk', 'postgresql', 'mariadb-server'}
        for key in ('parrotos', 'kali'):
            self.assertFalse(banned.intersection(w.PROFILES[key]['apt_packages']))
            for package in ('neovim', 'zsh', 'git', 'ripgrep'):
                self.assertIn(package, w.PROFILES[key]['apt_packages'])
        for component in w.PROFILES['dev']['optional_components']:
            self.assertTrue((w.REPO / 'components' / component / 'setup-container.sh').is_file())

    def test_host_launcher_maps_project_paths_but_preserves_engine_bind_sources(self):
        helper = MODULE.parent.parent / 'dotfiles/.local/bin/dotfiles-dev-exec'
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            binary = home / '.local/bin/dotfiles-podman'
            binary.parent.mkdir(parents=True)
            binary.write_text('#!/usr/bin/env python3\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n')
            binary.chmod(0o755)
            project = home / 'project with spaces'
            project.mkdir()
            def launch(*args):
                return w.json.loads(subprocess.check_output(
                    ['bash', str(helper), *args], cwd=project,
                    env=dict(os.environ, HOME=str(home)), text=True))
            rider = launch('rider', str(project), '.')
            self.assertEqual(rider[-4:], ['/host-home/project with spaces', 'rider',
                                          '/host-home/project with spaces', '.'])
            docker = launch('docker', 'run', '-v', str(project) + ':/work')
            self.assertEqual(docker[-3:], ['run', '-v', str(project) + ':/work'])

    def test_presentation_targets_new_container_and_private_pid_namespace(self):
        spec = importlib.util.spec_from_file_location('adapt', MODULE.parent / 'adapt_presentation.py')
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        originals = w.REPO / 'components/hermes/payload/bin'
        before = {name: (originals / name).read_bytes()
                  for name in ('presentacion.py', 'host_hotkeys.py')}
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, {'PODMAN_WORKBENCH': 'dev-podman'}):
            root = Path(directory)
            (root / 'bin').mkdir()
            for name in before:
                shutil.copy2(originals / name, root / 'bin' / name)
            adapter.adapt(root)
            adapter.adapt(root)  # Must remain safe to reapply.
            presentation = (root / 'bin/presentacion.py').read_text()
            keys = (root / 'bin/host_hotkeys.py').read_text()
            self.assertNotIn('distrobox-host-exec', presentation)
            self.assertNotIn("'distrobox','enter'", keys)
            self.assertIn("'dev-podman'", keys)
            self.assertIn('bridge-alive.py', keys)
            self.assertNotIn("io.open('/proc/PID/stat'", keys)
            helper = root / 'bin/bridge-alive.py'
            identity = Path(f'/proc/{os.getpid()}/stat').read_text().rsplit(')', 1)[1].split()[19]
            good = subprocess.run(['python3', str(helper), str(os.getpid()), identity])
            bad = subprocess.run(['python3', str(helper), str(os.getpid()), 'wrong-start-time'])
            self.assertEqual(good.returncode, 0)
            self.assertEqual(bad.returncode, 1)
        for name, contents in before.items():
            self.assertEqual((originals / name).read_bytes(), contents)


if __name__ == '__main__':
    unittest.main()
