#!/usr/bin/python3 -I
"""lab-mount: toggle the host-backed mount/umount bridge for Kali and Parrot."""
import argparse
import getpass
import importlib.util
import json
import os
from pathlib import Path
import pwd
import re
import socket
import stat
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
policy_spec = importlib.util.spec_from_file_location('mount_policy', ROOT / 'mount_policy.py')
policy = importlib.util.module_from_spec(policy_spec)
policy_spec.loader.exec_module(policy)
HELPER = '/usr/local/libexec/workbench-mount-helper'
CLIENT = '/usr/local/libexec/workbench-mount-client'
NAME = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}')
LIMIT = 8192


def host_home():
    return Path('/host-home') if Path('/run/.containerenv').exists() else Path.home()


def socket_path():
    return host_home() / '.local/state/podman-workbench/mounts.sock'


def validate(request):
    if isinstance(request, dict) and request.get('action') in ('attach', 'detach'):
        policy.validate(request, os.getuid(), os.getgid())
        return ['request']
    if not isinstance(request, dict) or request.get('action') not in ('list', 'mount', 'unmount'):
        raise ValueError('Operación no permitida.')
    action = request['action']
    if action == 'list' and set(request) == {'action'}:
        return [action]
    name = request.get('name')
    if action != 'list' and set(request) == {'action', 'name'} and isinstance(name, str) and NAME.fullmatch(name):
        return [action, name]
    raise ValueError('Usa un nombre de recurso, sin rutas ni opciones adicionales.')


def receive(connection, limit=LIMIT):
    data = bytearray()
    while b'\n' not in data:
        chunk = connection.recv(1024)
        if not chunk:
            raise ValueError('Solicitud incompleta.')
        data.extend(chunk)
        if len(data) > limit:
            raise ValueError('Solicitud demasiado larga.')
    return json.loads(data.split(b'\n', 1)[0])


def response_for(connection):
    try:
        _, uid, _ = struct.unpack('3i', connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        if uid != os.getuid():
            raise ValueError('Usuario no autorizado.')
        payload = receive(connection)
        command = validate(payload)
        result = subprocess.run(['/usr/bin/sudo', '-n', HELPER, *command],
                                capture_output=True, text=True,
                                **({'input': json.dumps(payload)} if command == ['request'] else {}))
        return {'ok': result.returncode == 0, 'output': result.stdout + result.stderr}
    except (OSError, ValueError) as error:
        return {'ok': False, 'output': str(error)}


def serve():
    if Path('/run/.containerenv').exists() or os.getuid() == 0:
        raise RuntimeError('El servicio debe ejecutarse como usuario normal en el anfitrión.')
    path = socket_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        info = path.lstat()
        if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid():
            raise RuntimeError('La ruta del socket está ocupada por otro archivo.')
        with socket.socket(socket.AF_UNIX) as probe:
            try:
                probe.connect(str(path))
            except ConnectionRefusedError:
                path.unlink()
            else:
                raise RuntimeError('El servicio de montajes ya está activo.')
    with socket.socket(socket.AF_UNIX) as listener:
        listener.bind(str(path))
        path.chmod(0o600)
        listener.listen(8)
        while True:
            connection, _ = listener.accept()
            with connection:
                connection.settimeout(3)
                response = response_for(connection)
                try:
                    connection.sendall(json.dumps(response).encode() + b'\n')
                except OSError:
                    pass


def send_payload(payload):
    validate(payload)
    with socket.socket(socket.AF_UNIX) as client:
        client.settimeout(120)
        try:
            client.connect(str(socket_path()))
        except (FileNotFoundError, ConnectionRefusedError):
            raise RuntimeError('Montajes desactivados. Activa lab-mount enable desde el anfitrión.') from None
        client.sendall(json.dumps(payload).encode() + b'\n')
        response = receive(client, 65536)
    print(response['output'], end='' if response['output'].endswith('\n') else '\n')
    if not response['ok']:
        raise RuntimeError('No se completó la operación de montaje.')


def request(action, name=None):
    payload = {'action': action}
    if name is not None:
        payload['name'] = name
    send_payload(payload)


def parse_mount(action, argv):
    parser = argparse.ArgumentParser(prog='mount' if action == 'attach' else 'umount', add_help=False)
    if action == 'attach':
        parser.add_argument('-t', '--types')
        parser.add_argument('-o', '--options', action='append', default=[])
        parser.add_argument('-r', '--read-only', action='store_true')
        parser.add_argument('-w', '--rw', action='store_true')
        parser.add_argument('source')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('target')
    args = parser.parse_intermixed_args(argv)
    payload = {'action': action, 'target': str(Path(args.target).absolute()).rstrip('/')}
    if action == 'detach':
        return payload
    source = args.source
    kind = args.types
    if not kind:
        kind = ('cifs' if source.startswith('//') else 'nfs' if ':/' in source
                else 'iso9660' if source.lower().endswith('.iso') else 'auto')
    if kind in ('iso9660', 'udf'):
        source = str(Path(source).absolute())
    auth, options = {}, []
    aliases = {'user': 'username', 'username': 'username', 'pass': 'password',
               'password': 'password', 'domain': 'domain', 'workgroup': 'domain'}
    for group in args.options:
        for option in group.split(','):
            key, sep, value = option.partition('=')
            if kind == 'cifs' and sep and key in aliases:
                auth[aliases[key]] = value
            elif kind == 'cifs' and sep and key in ('credentials', 'cred'):
                for line in Path(value).read_text().splitlines():
                    field, equals, content = line.partition('=')
                    if equals and field.strip() in ('username', 'password', 'domain'):
                        auth[field.strip()] = content
            else:
                options.append(option)
    if args.read_only:
        options.append('ro')
    if args.rw:
        options.append('rw')
    payload.update(source=source, fstype=kind, options=options, auth=auth)
    # Validate before prompting or asking the privileged helper to do anything.
    policy.validate(payload, os.getuid(), os.getgid())
    if kind == 'cifs' and 'guest' not in options:
        auth.setdefault('username', pwd.getpwuid(os.getuid()).pw_name)
        if 'password' not in auth:
            auth['password'] = getpass.getpass('Contraseña SMB: ')
        policy.validate(payload, os.getuid(), os.getgid())
    return payload


def bridge(action, argv):
    if not Path('/run/.containerenv').exists():
        raise RuntimeError('El puente mount/umount solo se instala dentro de Kali y Parrot.')
    native = '/usr/bin/mount' if action == 'attach' else '/usr/bin/umount'
    # Preserve ordinary container operations and mount listing outside our subtree.
    if not any(not arg.startswith('-') and
               (str(Path(arg).absolute()) == policy.TARGET or
                str(Path(arg).absolute()).startswith(policy.TARGET + '/')) for arg in argv):
        os.execv(native, [native, *argv])
    if os.geteuid() == 0:
        uid, gid = int(os.environ.get('SUDO_UID', '0')), int(os.environ.get('SUDO_GID', '0'))
        if uid <= 0 or gid < 0:
            raise RuntimeError('Ejecuta sudo mount desde tu usuario normal del contenedor.')
        try:
            os.setgroups([])
        except PermissionError:
            pass  # Some rootless user namespaces deny setgroups entirely.
        os.setgid(gid)
        os.setuid(uid)
    send_payload(parse_mount(action, argv))


def toggle(enabled):
    if Path('/run/.containerenv').exists() or os.getuid() == 0:
        raise RuntimeError('Activa/desactiva desde el anfitrión como usuario normal.')
    unit = Path.home() / '.config/systemd/user/workbench-mount-broker.service'
    if enabled:
        if unit.is_symlink() or (unit.exists() and not unit.read_text().startswith('# Managed workbench mount broker')):
            raise RuntimeError('La unidad del usuario ya existe y no pertenece a esta función.')
        # Check both managed containers before installing or starting host services.
        subprocess.run([sys.executable, '-I', str(ROOT / 'workbench.py'), 'lab-mounts', 'all', 'status'], check=True)
        subprocess.run(['sudo', '/usr/bin/bash', str(ROOT / 'install-mounts.sh'),
                        pwd.getpwuid(os.getuid()).pw_name], check=True)
        text = ('# Managed workbench mount broker\n[Unit]\nDescription=Workbench mount broker\n'
                '[Service]\nExecStart=/usr/bin/python3 -I ' + CLIENT + ' serve\n'
                'Restart=on-failure\nRestartSec=3\nUMask=0077\n'
                '[Install]\nWantedBy=default.target\n')
        unit.parent.mkdir(parents=True, exist_ok=True)
        unit.write_text(text)
        subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', '--user', 'enable', unit.name], check=True)
        subprocess.run(['systemctl', '--user', 'restart', unit.name], check=True)
    else:
        if unit.exists():
            subprocess.run(['systemctl', '--user', 'disable', '--now', unit.name], check=True)
        subprocess.run(['sudo', HELPER, 'release'], check=True)
        subprocess.run(['sudo', 'systemctl', 'disable', '--now', 'workbench-mounts.service'], check=True)
    subprocess.run([sys.executable, '-I', str(ROOT / 'workbench.py'), 'lab-mounts', 'all',
                    'enable' if enabled else 'disable'], check=True)
    print('Montajes ' + ('activados' if enabled else 'desactivados') + ' para Kali y Parrot.')


def main():
    if sys.argv[1:2] in (['bridge-mount'], ['bridge-umount']):
        bridge('attach' if sys.argv[1] == 'bridge-mount' else 'detach', sys.argv[2:])
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['enable', 'disable', 'status', 'list', 'mount', 'unmount', 'serve'])
    parser.add_argument('name', nargs='?')
    args = parser.parse_args()
    if args.action not in ('mount', 'unmount') and args.name is not None:
        parser.error('Esta operación no admite un nombre.')
    if args.action in ('enable', 'disable'):
        toggle(args.action == 'enable')
    elif args.action == 'serve':
        serve()
    elif args.action == 'status':
        if Path('/run/.containerenv').exists():
            print('Carpeta: /mnt/montajes; ' + ('disponible' if os.path.ismount('/mnt/montajes') else 'desactivada'))
        else:
            print('Anfitrión: ' + ('activado' if Path('/etc/workbench-mounts/enabled').is_file() else 'desactivado'))
            subprocess.run([sys.executable, '-I', str(ROOT / 'workbench.py'), 'lab-mounts', 'all', 'status'], check=True)
    else:
        request(args.action, args.name)


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, EOFError, subprocess.CalledProcessError) as error:
        print(f'Error: {error}', file=sys.stderr)
        sys.exit(1)
