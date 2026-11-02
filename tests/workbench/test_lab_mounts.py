"""Privilege-boundary and reversible container migration checks (no real mounts)."""
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch

ROOT = Path(__file__).resolve().parents[2] / 'environments/workbench/podman'


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


c, h, w, p, installer = (load(name) for name in
                          ('mounts', 'mount_helper', 'workbench', 'mount_policy', 'install_mount_bridge'))


class MountTests(unittest.TestCase):
    def payload(self, **changes):
        return {'action': 'attach', 'target': '/mnt/montajes/company',
                'source': '//server/Company Data', 'fstype': 'cifs',
                'options': ['vers=3.1.1'], 'auth': {}, **changes}

    def test_dynamic_policy_rejects_mount_escape_options_and_privileged_ids(self):
        for changes in ({'target': '/etc/company'}, {'target': '/mnt/montajes/../etc'},
                        {'target': '/mnt/montajes/a/b'}, {'fstype': 'proc'}, {'fstype': []},
                        {'options': ['bind']}, {'options': ['remount']}, {'options': ['suid']},
                        {'options': ['dev']}, {'options': ['uid=0']},
                        {'options': ['credentials=/etc/shadow']}, {'auth': {'password': 'x\nusername=root'}},
                        {'source': '/etc/shadow'}, {'options': ['vers=3.1.1,dev']}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                p.validate(self.payload(**changes), 1000, 1000)
        p.validate(self.payload(options=['uid=1000', 'gid=1000']), 1000, 1000)
        p.validate(self.payload(fstype='nfs', source='server:/data', auth={}, options=['vers=4']), 1000, 1000)
        p.validate(self.payload(fstype='iso9660', source='/host-home/lab.iso', options=['loop', 'ro']), 1000, 1000)
        p.validate(self.payload(fstype='ext4', source='/dev/disk/by-uuid/example', options=[]), 1000, 1000)

    def test_normal_mount_syntax_handles_order_spaces_credentials_and_other_types(self):
        with patch.object(c.os, 'getuid', return_value=1000), patch.object(c.os, 'getgid', return_value=1000), \
             patch.object(c.getpass, 'getpass', return_value='fixture-value') as prompt:
            data = c.parse_mount('attach', ['-t', 'cifs', '-o', 'username=student,vers=3.1.1',
                                           '//server/Company Data', '/mnt/montajes/company/'])
            self.assertEqual(data['source'], '//server/Company Data')
            self.assertEqual(data['target'], '/mnt/montajes/company')
            self.assertEqual(data['auth']['username'], 'student')
            prompt.assert_called_once()
            nfs = c.parse_mount('attach', ['server:/data', '/mnt/montajes/nfs', '-o', 'vers=4'])
            self.assertEqual(nfs['fstype'], 'nfs')
            iso = c.parse_mount('attach', ['-o', 'loop', '/host-home/lab.iso', '/mnt/montajes/iso'])
            self.assertEqual(iso['fstype'], 'iso9660')
            self.assertEqual(c.parse_mount('detach', ['/mnt/montajes/iso']),
                             {'action': 'detach', 'target': '/mnt/montajes/iso'})

    def test_broker_sends_dynamic_credentials_on_stdin_not_privileged_argv(self):
        connection = Mock()
        connection.getsockopt.return_value = struct.pack('3i', 100, c.os.getuid(), 1000)
        data = self.payload(auth={'username': 'student', 'password': 'fixture-value'})
        connection.recv.return_value = json.dumps(data).encode() + b'\n'
        with patch.object(c.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'ok', '')) as run:
            self.assertTrue(c.response_for(connection)['ok'])
            self.assertEqual(run.call_args.args[0], ['/usr/bin/sudo', '-n', c.HELPER, 'request'])
            self.assertEqual(json.loads(run.call_args.kwargs['input']), data)

    def test_dynamic_root_mount_uses_temporary_credentials_and_creates_target(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(h, 'CONFIG', Path(directory)), \
             patch.object(h, 'validate_base'), patch.object(h, 'target_for', return_value=h.BASE / 'company') as target, \
             patch.object(h.pwd, 'getpwuid', return_value=SimpleNamespace(pw_gid=1000)), \
             patch.object(h.os.path, 'ismount', return_value=False):
            (Path(directory) / 'enabled').write_text('enabled')
            def mount(*argv, **kwargs):
                self.assertNotIn('fixture-value', ' '.join(argv))
                options = argv[argv.index('--options') + 1].split(',')
                credentials = Path(next(o.split('=', 1)[1] for o in options if o.startswith('credentials=')))
                self.assertEqual(credentials.stat().st_mode & 0o777, 0o600)
                self.assertIn('username=student\n', credentials.read_text())
                self.assertEqual(options[-2:], ['nosuid', 'nodev'])
                self.assertEqual(argv[argv.index('--source') + 1], '//server/Company Data')
            with patch.object(h, 'run', side_effect=mount):
                h.dynamic_mount(self.payload(auth={'username': 'student', 'password': 'fixture-value'}), 1000)
            target.assert_called_once_with('company')
            self.assertFalse(list(Path(directory).glob('credentials-*')))

    def test_iso_source_opened_as_user_and_only_regular_files_accepted(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(h.os, 'setgroups') as groups, \
             patch.object(h.os, 'setegid'), patch.object(h.os, 'seteuid') as user:
            source = Path(directory) / 'lab.iso'
            source.write_bytes(b'not mounted in this test')
            account = SimpleNamespace(pw_dir=directory, pw_name='test', pw_uid=1000, pw_gid=1000)
            with patch.object(h.os, 'getgrouplist', return_value=[1000]):
                descriptor = h.open_image('/host-home/lab.iso', account)
                try:
                    self.assertEqual(os.read(descriptor, 3), b'not')
                finally:
                    os.close(descriptor)
                self.assertEqual(user.call_args_list[0].args, (1000,))
                self.assertEqual(user.call_args_list[-1].args, (0,))
                groups.assert_called()
                source.unlink()
                source.symlink_to('/dev/null')
                with self.assertRaisesRegex(RuntimeError, 'regular'):
                    h.open_image('/host-home/lab.iso', account)

    def test_iso_mount_pins_descriptor_and_forces_readonly(self):
        native_close = os.close
        with tempfile.TemporaryDirectory() as directory, patch.object(h, 'CONFIG', Path(directory)), \
             patch.object(h, 'validate_base'), patch.object(h, 'target_for', return_value=h.BASE / 'iso'), \
             patch.object(h.pwd, 'getpwuid', return_value=SimpleNamespace(pw_gid=1000)), \
             patch.object(h.os.path, 'ismount', return_value=False), \
             patch.object(h, 'open_image', return_value=42), \
             patch.object(h, 'attach_loop', return_value=('/dev/loop7', 43)) as loop, \
             patch.object(h.os, 'close', side_effect=lambda fd: None if fd in (42, 43) else native_close(fd)) as close, \
             patch.object(h, 'run') as run:
            (Path(directory) / 'enabled').write_text('enabled')
            h.dynamic_mount(self.payload(source='/host-home/lab.iso', fstype='iso9660', options=['rw']), 1000)
            command = run.call_args.args
            self.assertEqual(command[command.index('--source') + 1], '/dev/loop7')
            self.assertTrue(command[command.index('--options') + 1].endswith('ro,nosuid,nodev'))
            self.assertNotIn('loop', command[command.index('--options') + 1].split(','))
            loop.assert_called_once_with(42)
            self.assertEqual(sum(call.args == (42,) for call in close.call_args_list), 1)
            self.assertEqual(sum(call.args == (43,) for call in close.call_args_list), 1)

    def test_loop_configuration_uses_original_fd_readonly_and_autoclear(self):
        with patch.object(h.Path, 'exists', return_value=True), \
             patch.object(h.os, 'open', side_effect=[30, 31]), patch.object(h.os, 'close') as close, \
             patch.object(h.fcntl, 'ioctl', side_effect=[7, 0]) as ioctl:
            self.assertEqual(h.attach_loop(42), ('/dev/loop7', 31))
            call = ioctl.call_args_list[1].args
            self.assertEqual(call[:2], (31, 0x4C0A))
            self.assertEqual(len(call[2]), 304)
            config = struct.unpack('=II5Q4I64s64s32s10Q', call[2])
            self.assertEqual(config[0], 42)
            self.assertEqual(config[10], 1 | 4)
            close.assert_called_once_with(30)

    def test_device_policy_rejects_internal_and_already_mounted_devices(self):
        device = MagicMock()
        device.__str__.return_value = '/dev/sdz1'
        device.resolve.return_value = device
        device.stat.return_value = SimpleNamespace(st_mode=h.stat.S_IFBLK, st_rdev=os.makedev(8, 1))
        device.is_relative_to.return_value = True
        sys_path = MagicMock()
        sys_path.resolve.return_value = sys_path
        sys_path.parents = []
        flag = Mock()
        flag.is_file.return_value = True
        flag.read_text.return_value = '0'
        subsystem = Mock()
        subsystem.resolve.return_value.name = 'block'
        sys_path.__truediv__.side_effect = lambda key: flag if key == 'removable' else subsystem
        with patch.object(h, 'Path', side_effect=[device, sys_path]), patch.object(h, 'run') as run:
            with self.assertRaisesRegex(RuntimeError, 'internos'):
                h.removable_device('/dev/sdz1')
            run.assert_not_called()
        flag.read_text.return_value = '1'
        with patch.object(h, 'Path', side_effect=[device, sys_path, Path('/')]), \
             patch.object(h, 'run', return_value=subprocess.CompletedProcess([], 0,
                          json.dumps({'filesystems': [{'target': '/', 'maj:min': '8:1'}]}), '')):
            with self.assertRaisesRegex(RuntimeError, 'fuera'):
                h.removable_device('/dev/sdz1')

    def test_wrapper_drops_container_root_before_connecting_and_keeps_native_operations(self):
        with patch.object(c.Path, 'exists', return_value=True), patch.object(c.os, 'geteuid', return_value=0), \
             patch.dict(c.os.environ, {'SUDO_UID': '1000', 'SUDO_GID': '1000'}), \
             patch.object(c.os, 'setgroups'), patch.object(c.os, 'setgid') as gid, \
             patch.object(c.os, 'setuid') as uid, patch.object(c, 'send_payload') as send, \
             patch.object(c.os, 'execv', side_effect=RuntimeError('native')) as native:
            c.bridge('detach', ['/mnt/montajes/company'])
            uid.assert_called_once_with(1000)
            gid.assert_called_once_with(1000)
            send.assert_called_once_with({'action': 'detach', 'target': '/mnt/montajes/company'})
            with self.assertRaisesRegex(RuntimeError, 'native'):
                c.bridge('attach', [])
            native.assert_called_once_with('/usr/bin/mount', ['/usr/bin/mount'])

    def test_wrapper_installer_is_reversible_preserves_foreign_files_and_validates_sudoers(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / 'local'
            sudoers = Path(directory) / 'sudoers'
            with patch.object(installer, 'PREFIX', prefix), patch.object(installer, 'SUDOERS', sudoers):
                installer.configure(ROOT, 'student')
                for name in ('mount', 'umount'):
                    wrapper = prefix / 'sbin' / name
                    subprocess.run(['bash', '-n', str(wrapper)], check=True)
                    self.assertIn('bridge-' + name, wrapper.read_text())
                installer.configure()
                self.assertFalse((prefix / 'sbin/mount').exists())
                (prefix / 'sbin/mount').write_text('# unrelated wrapper')
                with self.assertRaisesRegex(RuntimeError, 'ajeno'):
                    installer.configure(ROOT, 'student')

    def test_protocol_rejects_paths_options_and_unknown_fields(self):
        for request in ({'action': 'prepare'}, {'action': 'release'},
                        {'action': 'mount', 'name': '../escape'},
                        {'action': 'unmount', 'name': '/etc'},
                        {'action': 'mount', 'name': '--all'},
                        {'action': 'mount', 'name': 'usb;id'},
                        {'action': 'mount', 'name': 'usb', 'options': 'suid'},
                        {'action': 'list', 'name': 'usb'}, [], None):
            with self.subTest(request=request), self.assertRaises(ValueError):
                c.validate(request)
        self.assertEqual(c.validate({'action': 'mount', 'name': 'lab-1'}), ['mount', 'lab-1'])

    def test_wire_protocol_round_trip_and_size_limit(self):
        connection = Mock()
        connection.recv.side_effect = [b'{"action":', b'"list"}\n']
        self.assertEqual(c.receive(connection), {'action': 'list'})
        connection.recv.side_effect = [b'x' * (c.LIMIT + 1)]
        with self.assertRaisesRegex(ValueError, 'larga'):
            c.receive(connection)

    def test_broker_checks_peer_uid_and_passes_only_validated_argv(self):
        connection = Mock()
        connection.getsockopt.return_value = struct.pack('3i', 100, c.os.getuid(), 1000)
        connection.recv.return_value = b'{"action":"mount","name":"usb"}\n'
        with patch.object(c.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'ok', '')) as run:
            self.assertEqual(c.response_for(connection), {'ok': True, 'output': 'ok'})
            run.assert_called_once_with(['/usr/bin/sudo', '-n', c.HELPER, 'mount', 'usb'],
                                        capture_output=True, text=True)
        connection.getsockopt.return_value = struct.pack('3i', 100, c.os.getuid() + 1, 1000)
        with patch.object(c.subprocess, 'run') as run:
            self.assertFalse(c.response_for(connection)['ok'])
            run.assert_not_called()

    def test_real_findmnt_parses_different_types_and_spaces(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory)
            table = config / 'fstab'
            table.write_text('//host/Company\\040Data /srv/workbench-mounts/company cifs noauto 0 0\n'
                             'host:/data /srv/workbench-mounts/nfs nfs noauto 0 0\n'
                             '/srv/lab.iso /srv/workbench-mounts/iso iso9660 loop,ro 0 0\n')
            info = SimpleNamespace(st_uid=0, st_mode=0o600)
            with patch.object(h, 'CONFIG', config), patch.object(h, 'FSTAB', table), \
                 patch.object(Path, 'lstat', return_value=info), patch.object(Path, 'is_symlink', return_value=False):
                self.assertEqual(h.entries(), {'company': 'cifs', 'nfs': 'nfs', 'iso': 'iso9660'})
                table.write_text('# resources are intentionally disabled\n')
                self.assertEqual(h.entries(), {})
                table.write_text('host:/data /etc/escape nfs noauto 0 0\n')
                with self.assertRaisesRegex(RuntimeError, 'subcarpeta'):
                    h.entries()

    def test_destinations_reject_symlinks_unknown_names_and_user_writable_directories(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(h, 'BASE', Path(directory)):
            target = Path(directory) / 'lab'
            target.symlink_to('/etc')
            with self.assertRaisesRegex(RuntimeError, 'simbólicos'):
                h.target_for('lab', {'lab': 'ext4'})
            with self.assertRaisesRegex(RuntimeError, 'autorizado'):
                h.target_for('../lab', {'lab': 'ext4'})
            target.unlink()
            target.mkdir(mode=0o777)
            target.chmod(0o777)
            with self.assertRaisesRegex(RuntimeError, 'root'):
                h.target_for('lab', {'lab': 'ext4'})

    def test_helper_never_accepts_extra_arguments_or_mount_flags(self):
        for argv in (['mount', 'lab', '-o', 'suid'], ['unmount', 'lab', '-f'], ['prepare', 'lab']):
            with patch.object(h.os, 'geteuid', return_value=0), patch.object(h, 'operate') as operate:
                with self.assertRaisesRegex(RuntimeError, 'Argumentos'):
                    h.main(argv)
                operate.assert_not_called()

    def test_helper_uses_fixed_fstab_and_forces_nosuid_nodev(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(h, 'CONFIG', Path(directory)), \
             patch.object(h, 'validate_base'), patch.object(h, 'entries', return_value={'lab': 'cifs'}), \
             patch.object(h, 'target_for', return_value=h.BASE / 'lab'), \
             patch.object(h.os.path, 'ismount', return_value=False), patch.object(h, 'run') as run:
            (Path(directory) / 'enabled').write_text('enabled')
            h.operate('mount', 'lab')
            run.assert_called_once_with('/usr/bin/mount', '--fstab', str(h.FSTAB), '--options',
                                        'nosuid,nodev', '--target', str(h.BASE / 'lab'))
            (Path(directory) / 'enabled').unlink()
            with self.assertRaisesRegex(RuntimeError, 'desactivados'):
                h.operate('mount', 'lab')

    def info(self, enabled=False):
        mounts = [{'Type': 'bind', 'Destination': '/host-home', 'Source': str(w.HOME)}]
        if enabled:
            mounts.append({'Type': 'bind', 'Destination': w.MOUNT_TARGET, 'Source': str(w.MOUNT_SOURCE)})
        return {'State': {'Running': True}, 'Mounts': mounts,
                'Config': {'Labels': {'manager': w.MANAGER, 'custom': 'preserved'}}}

    def test_sharing_only_changes_kali_parrot_without_container_privileges(self):
        for profile in ('kali', 'parrotos', 'dev'):
            args = w.create_args({**w.PROFILES[profile], 'lab_mounts': True}, 'image')
            self.assertEqual(any('destination=/mnt/montajes' in str(arg) for arg in args), profile != 'dev')
            self.assertNotIn('--privileged', args)
            self.assertNotIn('--cap-add', args)
        args = w.create_args({**w.PROFILES['kali'], 'lab_mounts': False}, 'image')
        self.assertFalse(any('destination=/mnt/montajes' in str(arg) for arg in args))

    def test_migration_failure_restores_original_and_keeps_backups(self):
        calls = []
        def pod(*args, **kwargs):
            calls.append(args)
            if args[0] == 'rename' and args[1].startswith('kali-podman-mounts-') and args[-1] == 'kali-podman':
                raise RuntimeError('rename failed')
        with patch.object(w, 'managed', return_value=self.info()), \
             patch.object(w.Path, 'is_file', return_value=True), \
             patch.object(w, 'execute'), patch.object(w, 'install_mount_client'), \
             patch.object(w, 'pod', side_effect=pod):
            with self.assertRaisesRegex(RuntimeError, 'rename failed'):
                w.lab_mounts('kali', 'enable')
        self.assertEqual(calls[0], ('stop', 'kali-podman'))
        self.assertEqual(calls[-1], ('start', 'kali-podman'))
        self.assertEqual(calls[-2][0], 'rename')
        self.assertIn('-before-mounts-', calls[-2][1])
        self.assertFalse(any(call[0] == 'rm' for call in calls))
        create = next(call for call in calls if call[0] == 'create')
        self.assertIn('custom=preserved', create)
        self.assertTrue(any('bind-propagation=rslave' in arg for arg in create))

    def test_disable_removes_share_and_keeps_original_and_dev_is_refused(self):
        with patch.object(w, 'managed', return_value=self.info(True)), patch.object(w, 'pod') as pod, \
             patch.object(w, 'execute'):
            w.lab_mounts('parrotos', 'disable')
            create = next(call.args for call in pod.call_args_list if call.args[0] == 'create')
            self.assertFalse(any('destination=/mnt/montajes' in str(arg) for arg in create))
            self.assertFalse(any(call.args[0] == 'rm' for call in pod.call_args_list))
        with self.assertRaisesRegex(RuntimeError, 'Kali y Parrot'):
            w.lab_mounts('dev', 'enable')

    def test_migration_preserves_custom_binds_by_refusing_to_drop_them(self):
        info = self.info(True)
        info['Mounts'].append({'Type': 'bind', 'Source': '/srv/private', 'Destination': '/data'})
        with patch.object(w, 'managed', return_value=info), patch.object(w, 'pod') as pod:
            with self.assertRaisesRegex(RuntimeError, 'personalizados'):
                w.lab_mounts('kali', 'disable')
            pod.assert_not_called()

    def test_repeated_enable_preserves_a_stopped_container(self):
        info = self.info(True)
        info['State']['Running'] = False
        with patch.object(w, 'managed', return_value=info), patch.object(w, 'start') as start, \
             patch.object(w.Path, 'is_file', return_value=True), patch.object(w, 'pod') as pod, \
             patch.object(w, 'install_mount_client'):
            w.lab_mounts('kali', 'enable')
            start.assert_called_once_with('kali-podman')
            pod.assert_called_once_with('stop', 'kali-podman')


if __name__ == '__main__':
    unittest.main()
