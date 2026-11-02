#!/usr/bin/python3 -I
"""Root-owned workbench helper for validated dynamic mounts and optional fstab names."""
import fcntl
import errno
import importlib.util
import json
import os
from pathlib import Path
import pwd
import re
import subprocess
import stat
import struct
import sys
import tempfile
import time

policy_spec = importlib.util.spec_from_file_location('mount_policy', Path(__file__).with_name('mount_policy.py'))
policy = importlib.util.module_from_spec(policy_spec)
policy_spec.loader.exec_module(policy)

BASE = Path('/srv/workbench-mounts')
CONFIG = Path('/etc/workbench-mounts')
FSTAB = CONFIG / 'fstab'
ENV = {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LANG': 'C.UTF-8'}
NAME = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}')


def run(*args, **kwargs):
    return subprocess.run(args, check=True, env=ENV, cwd='/', **kwargs)


def entries():
    # Configuration and all its parent directories must remain administrator-owned.
    for path in (CONFIG, FSTAB):
        info = path.lstat()
        if path.is_symlink() or info.st_uid != 0 or info.st_mode & 0o022:
            raise RuntimeError('Configuración de montajes insegura.')
    result = subprocess.run(['/usr/bin/findmnt', '--fstab', '--tab-file', str(FSTAB),
                             '--json', '--output', 'TARGET,FSTYPE'],
                            capture_output=True, text=True, env=ENV, cwd='/')
    if result.returncode == 1 and not result.stdout.strip() and not result.stderr.strip():
        return {}  # An intentionally empty resource list is the default.
    result.check_returncode()
    resources = {}
    for row in json.loads(result.stdout).get('filesystems', []):
        target = Path(row['target'])
        if target.parent != BASE or not NAME.fullmatch(target.name) or target.name in resources:
            raise RuntimeError('Cada destino del fstab debe ser una subcarpeta directa y única de ' + str(BASE))
        resources[target.name] = row['fstype']
    return resources


def validate_base():
    for path in (BASE.parent, BASE):
        info = path.lstat()
        if path.is_symlink() or not path.is_dir() or info.st_uid != 0 or info.st_mode & 0o022:
            raise RuntimeError('La carpeta de montajes debe pertenecer a root y no ser escribible por usuarios.')


def target_for(name, resources=None):
    if not NAME.fullmatch(name) or (resources is not None and name not in resources):
        raise RuntimeError('Recurso no autorizado. Configúralo primero en ' + str(FSTAB))
    target = BASE / name
    if target.is_symlink():
        raise RuntimeError('No se permiten destinos simbólicos.')
    if not target.exists():
        target.mkdir(mode=0o755)
    if not target.is_dir():
        raise RuntimeError('El destino no es una carpeta.')
    if not os.path.ismount(target):
        info = target.stat()
        if info.st_uid != 0 or info.st_mode & 0o022:
            raise RuntimeError('El destino debe pertenecer a root y no ser escribible por usuarios.')
    return target


def removable_device(source):
    device = Path(source).resolve(strict=True)
    info = device.stat()
    if not device.is_relative_to('/dev') or not stat.S_ISBLK(info.st_mode):
        raise RuntimeError('Se requiere un dispositivo de bloques extraíble.')
    major_minor = f'{os.major(info.st_rdev)}:{os.minor(info.st_rdev)}'
    sys_path = Path('/sys/dev/block', major_minor).resolve(strict=True)
    removable = False
    for ancestor in (sys_path, *sys_path.parents):
        flag = ancestor / 'removable'
        if (flag.is_file() and flag.read_text().strip() == '1') or (ancestor / 'subsystem').resolve().name == 'usb':
            removable = True
            break
    if not removable:
        raise RuntimeError('Solo se admiten dispositivos extraíbles/USB, no discos internos del anfitrión.')
    mounted = run('/usr/bin/findmnt', '--json', '--output', 'TARGET,MAJ:MIN', capture_output=True, text=True)
    def check(rows):
        for row in rows:
            if row.get('maj:min') == major_minor and not Path(row['target']).is_relative_to(BASE):
                raise RuntimeError('El dispositivo ya está montado fuera de la carpeta autorizada.')
            check(row.get('children', []))
    check(json.loads(mounted.stdout).get('filesystems', []))
    return str(device)


def open_image(source, account):
    # Open with the caller's permissions, then pass the pinned regular-file FD to mount.
    # Following user-controlled paths as root would expose arbitrary host files/devices.
    source = Path(account.pw_dir) / Path(source).relative_to('/host-home')
    old_gid, old_groups = os.getegid(), os.getgroups()
    try:
        os.setgroups(os.getgrouplist(account.pw_name, account.pw_gid))
        os.setegid(account.pw_gid)
        os.seteuid(account.pw_uid)
        descriptor = os.open(source, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
    finally:
        os.seteuid(0)
        os.setegid(old_gid)
        os.setgroups(old_groups)
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise RuntimeError('La imagen debe ser un archivo regular legible por tu usuario.')
    return descriptor


def attach_loop(image_descriptor):
    # Linux UAPI loop_config: fd, block_size, loop_info64, reserved[8].
    # Configure from the already-open FD: libmount's -o loop canonicalizes and
    # reopens backing paths, which would defeat the caller-permission check.
    if not Path('/dev/loop-control').exists():
        raise RuntimeError('Falta soporte loop en el host; carga el módulo con sudo modprobe loop.')
    control = os.open('/dev/loop-control', os.O_RDWR | os.O_CLOEXEC)
    try:
        for _ in range(8):
            loop_descriptor = None
            try:
                number = fcntl.ioctl(control, 0x4C82)  # LOOP_CTL_GET_FREE
                device = f'/dev/loop{number}'
                loop_descriptor = os.open(device, os.O_RDONLY | os.O_CLOEXEC)
                config = struct.pack('=II5Q4I64s64s32s10Q', image_descriptor, 0,
                                     *([0] * 5), 0, 0, 0, 1 | 4,  # READ_ONLY | AUTOCLEAR
                                     b'workbench', b'', b'', *([0] * 10))
                fcntl.ioctl(loop_descriptor, 0x4C0A, config)  # LOOP_CONFIGURE, Linux >= 5.8
                return device, loop_descriptor
            except OSError as error:
                if loop_descriptor is not None:
                    os.close(loop_descriptor)
                if error.errno in (errno.ENOTTY, errno.ENOSYS):
                    raise RuntimeError('Las imágenes requieren LOOP_CONFIGURE (Linux 5.8 o posterior).') from error
                if error.errno not in (errno.EBUSY, errno.ENOENT, errno.ENXIO):
                    raise
                time.sleep(0.05)
        raise RuntimeError('No se pudo reservar un dispositivo loop libre; reintenta.')
    finally:
        os.close(control)


def dynamic_mount(payload, uid):
    if uid == 0:
        raise RuntimeError('La solicitud requiere un usuario normal del anfitrión.')
    account = pwd.getpwuid(uid)
    policy.validate(payload, uid, account.pw_gid)
    if payload['action'] == 'attach' and payload['fstype'] == 'cifs' and 'guest' not in payload['options']:
        if not payload['auth'].get('username') or 'password' not in payload['auth']:
            raise RuntimeError('Faltan las credenciales CIFS; usa el prompt del cliente o guest.')
    validate_base()
    if not (CONFIG / 'enabled').is_file():
        raise RuntimeError('Los montajes están desactivados en el anfitrión.')
    target = target_for(Path(payload['target']).name)
    if payload['action'] == 'detach':
        if os.path.ismount(target):
            run('/usr/bin/umount', '--', str(target))
        print('Desmontado: ' + payload['target'])
        return
    if os.path.ismount(target):
        raise RuntimeError('El destino ya está montado; desmóntalo primero.')
    source, kind = payload['source'], payload['fstype']
    options = list(payload['options'])
    descriptor = None
    loop_descriptor = None
    with tempfile.TemporaryDirectory(prefix='credentials-', dir=CONFIG) as directory:
        try:
            if kind == 'cifs':
                options += [f'uid={uid}', f'gid={account.pw_gid}']
                if payload['auth']:
                    credentials = Path(directory) / 'cifs'
                    credentials.touch(mode=0o600)
                    credentials.write_text(''.join(f'{key}={value}\n' for key, value in payload['auth'].items()))
                    options.append('credentials=' + str(credentials))
            elif kind in ('iso9660', 'udf'):
                descriptor = open_image(source, account)
                source, loop_descriptor = attach_loop(descriptor)
                options = [option for option in options if option != 'loop'] + ['ro']
            elif kind not in ('nfs', 'nfs4'):
                source = removable_device(source)
                if kind in ('vfat', 'exfat', 'ntfs3'):
                    options += [f'uid={uid}', f'gid={account.pw_gid}']
            options += ['nosuid', 'nodev']
            run('/usr/bin/mount', '--no-canonicalize', '--types', kind, '--options', ','.join(options),
                '--source', source, '--target', str(target))
        finally:
            if loop_descriptor is not None:
                os.close(loop_descriptor)
            if descriptor is not None:
                os.close(descriptor)
    print('Montado: ' + payload['target'])


def operate(action, name=None):
    validate_base()
    if action == 'prepare':
        # A separate shared subtree propagates into rslave container bind mounts.
        if not os.path.ismount(BASE):
            run('/usr/bin/mount', '--bind', str(BASE), str(BASE))
        run('/usr/bin/mount', '--make-rshared', str(BASE))
        (CONFIG / 'enabled').write_text('enabled\n')
        return
    if action == 'release':
        (CONFIG / 'enabled').unlink(missing_ok=True)
        if not os.path.ismount(BASE):
            return
        # Use current mountinfo rather than fstab: an administrator may have edited it.
        result = run('/usr/bin/findmnt', '--json', '--submounts', '--mountpoint', str(BASE),
                     '--output', 'TARGET', capture_output=True, text=True)
        def unmount_tree(row):
            for child in row.get('children', []):
                unmount_tree(child)
            target = Path(row['target'])
            if target != BASE and not target.is_relative_to(BASE):
                raise RuntimeError('Montaje fuera de la carpeta autorizada.')
            run('/usr/bin/umount', '--', str(target))
        for row in json.loads(result.stdout).get('filesystems', []):
            unmount_tree(row)
        return
    if not (CONFIG / 'enabled').is_file():
        raise RuntimeError('Los montajes están desactivados en el anfitrión.')
    resources = entries()
    if action == 'list':
        result = run('/usr/bin/findmnt', '--json', '--submounts', '--mountpoint', str(BASE),
                     '--output', 'TARGET,FSTYPE', capture_output=True, text=True)
        def show(rows):
            for row in rows:
                path = Path(row['target'])
                if path != BASE and path.parent == BASE:
                    print(f'{path.name}\t{row["fstype"]}\tmontado')
                    resources.pop(path.name, None)
                show(row.get('children', []))
        show(json.loads(result.stdout).get('filesystems', []))
        for key, kind in resources.items():
            print(f'{key}\t{kind}\tdesmontado')
        return
    target = target_for(name, resources)
    if action == 'mount':
        if not os.path.ismount(target):
            run('/usr/bin/mount', '--fstab', str(FSTAB), '--options', 'nosuid,nodev',
                '--target', str(target))
    elif os.path.ismount(target):
        # No force/lazy/recursive flags are accepted from callers.
        run('/usr/bin/umount', '--', str(target))
    print(f'{name}: {"montado" if action == "mount" else "desmontado"}')


def main(argv):
    if os.geteuid() != 0:
        raise RuntimeError('Usa lab-mount; este helper requiere root.')
    if not argv or argv[0] not in ('prepare', 'release', 'list', 'mount', 'unmount', 'request'):
        raise RuntimeError('Operación no permitida.')
    if len(argv) != (2 if argv[0] in ('mount', 'unmount') else 1):
        raise RuntimeError('Argumentos no permitidos.')
    with (CONFIG / 'lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if argv == ['request']:
            data = sys.stdin.read(8193)
            if len(data) > 8192:
                raise RuntimeError('Solicitud demasiado larga.')
            dynamic_mount(json.loads(data), int(os.environ['SUDO_UID']))
        else:
            operate(*argv)


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except (OSError, RuntimeError, subprocess.CalledProcessError, ValueError, KeyError) as error:
        print(f'Error: {error}', file=sys.stderr)
        sys.exit(1)
