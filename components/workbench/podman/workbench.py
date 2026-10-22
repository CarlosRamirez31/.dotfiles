#!/usr/bin/env python3
"""Independent Podman environments. Never changes a Distrobox container."""
import argparse
import base64
import fcntl
import getpass
import json
import os
import re
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
HOME = Path.home()
UID, GID = os.getuid(), os.getgid()
USER = getpass.getuser()
MANAGER = 'dotfiles-podman-workbench'
PODMAN = shlex.split(os.environ.get('PODMAN_WORKBENCH_CLIENT', 'podman'))
PROFILES = json.loads((ROOT / 'profiles.json').read_text())
BASE_COPY = ['.zshrc', '.zshenv', '.zprofile', '.gitconfig', '.config/git',
             '.config/zsh', '.config/starship.toml', '.config/fastfetch',
             '.config/bat', '.config/yazi', '.config/lazygit', '.config/nvim', '.config/fontconfig',
             '.local/share/oh-my-zsh', '.local/share/fonts']
DEV_COPY = ['.dotfiles', '.local/bin', '.local/libexec', '.local/lib', '.java',
            '.DBeaverData', '.dbeaver4', '.eclipse', '.cargo', '.rustup',
            '.nvm', '.npm-global', '.local/share/pnpm', '.local/share/mise',
            '.config/flutter',
            '.config/.android', '.android', '.config/JetBrains', '.config/DBeaverData',
            '.config/dbeaver', '.config/.DBeaverData', '.local/share/DBeaverData',
            '.local/share/.DBeaverData', '.local/share/JetBrains',
            '.local/share/flutter-dev', '.local/share/nvim', '.local/state/nvim',
            '.local/share/NuGet', '.local/share/IsolatedStorage', '.local/share/pki',
            '.gradle', '.m2', '.nuget', '.dotnet', '.pub-cache', '.dart',
            '.flutter', '.flutter_settings', '.flutter_tool_state', '.config/configstore',
            '.config/awesome', '.config/polybar', '.config/alacritty', '.config/rofi',
            '.config/wallpapers', '.config/gtk-3.0', '.config/gtk-4.0',
            '.local/share/icons', '.local/share/zoxide', '.local/state/zsh',
            '.config/github-copilot']


def run(args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, **kwargs)


def pod(*args, **kwargs):
    return run([*PODMAN, *args], **kwargs)


def inspect(name):
    p = subprocess.run([*PODMAN, 'container', 'exists', name])
    if p.returncode == 1:
        return None
    if p.returncode:
        raise RuntimeError(f'Podman no pudo consultar {name} (código {p.returncode}).')
    return json.loads(pod('inspect', name, capture_output=True, text=True).stdout)[0]


def managed(name):
    info = inspect(name)
    if info is None or info['Config'].get('Labels', {}).get('manager') != MANAGER:
        raise RuntimeError(f'{name} no es un contenedor administrado por esta configuración.')
    return info


def start(name):
    info = managed(name)
    if not info['State']['Running']:
        pod('start', name)


def execute(name, *command, root=False, data=None, capture=False):
    args = ['exec', '--user', '0' if root else f'{UID}:{GID}']
    if data is not None:
        args += ['-i']
    return pod(*args, name, *command, input=data, text=True,
               capture_output=capture)


def refresh_authority(name):
    authority = Path(os.environ.get('XAUTHORITY', str(HOME / '.Xauthority')))
    if os.environ.get('DISPLAY') and authority.is_file():
        # Copy the cookie to the internal home. Never bind an ephemeral /tmp
        # authorization file into the container configuration across reboots.
        encoded = base64.b64encode(authority.read_bytes()).decode('ascii')
        execute(name, 'python3', '-c',
                'import base64,os,pathlib,sys; p=pathlib.Path.home()/".Xauthority"; '
                'p.write_bytes(base64.b64decode(sys.stdin.read())); p.chmod(0o600)',
                data=encoded)


def pipe_tar(name, files, destination, source=HOME, dereference=True):
    if not files:
        return
    # Materialize symlinks: the new home must not depend on shared dotfiles.
    args = ['tar', '-c', '--sparse', '--exclude=*.sock', '--exclude=__pycache__',
            '--exclude=.config/.android/avd/*.lock', '--exclude=.android/avd/*.lock', '-f', '-']
    if dereference:
        args.append('-h')
    producer = subprocess.Popen([*args, '-C', str(source), '--', *files], stdout=subprocess.PIPE)
    try:
        consumer = subprocess.run([*PODMAN, 'exec', '-i', '--user', f'{UID}:{GID}',
                                   name, 'tar', '-x', '--no-same-owner', '-C', str(destination), '-f', '-'],
                                  stdin=producer.stdout)
        producer.stdout.close()
        status = producer.wait()
        if status != 0 or consumer.returncode != 0:
            raise RuntimeError('Falló la copia al home interno; la preparación puede reanudarse.')
    finally:
        if producer.poll() is None:
            producer.terminate()
            producer.wait()


def transfer_home(source, target):
    """Stream the internal home, preserving sparse Android disks and symlinks."""
    managed(source)
    managed(target)
    producer = subprocess.Popen([*PODMAN, 'exec', '--user', f'{UID}:{GID}', source,
                                 'tar', '-cS', '--exclude=*.sock', '-C', str(HOME), '-f', '-', '.'],
                                stdout=subprocess.PIPE)
    try:
        consumer = subprocess.run([*PODMAN, 'exec', '-i', '--user', f'{UID}:{GID}', target,
                                   'tar', '-xS', '--no-same-owner', '-C', str(HOME), '-f', '-'],
                                  stdin=producer.stdout)
        producer.stdout.close()
        if producer.wait() or consumer.returncode:
            raise RuntimeError('Falló la transferencia interna; el contenedor de origen se conserva.')
    finally:
        if producer.poll() is None:
            producer.terminate()
            producer.wait()


def create_args(profile, image):
    args = ['create', '--name', profile['name'], '--hostname', profile['name'],
            '--label', f'manager={MANAGER}', '--userns=keep-id',
            '--user', f'{UID}:{GID}',
            '--annotation', 'run.oci.keep_original_groups=1', '--init',
            '--image-volume=ignore', '--workdir', '/',
            '--mount', f'type=bind,source={HOME},destination=/host-home,rw',
            '--security-opt', 'label=disable', '--entrypoint', '/usr/bin/sleep']
    env = {'HOME': str(HOME), 'USER': USER, 'LOGNAME': USER,
           'SHELL': '/bin/zsh', 'XDG_CONFIG_HOME': str(HOME / '.config'),
           'XDG_DATA_HOME': str(HOME / '.local/share'),
           'XDG_STATE_HOME': str(HOME / '.local/state'),
           'XDG_CACHE_HOME': str(HOME / '.cache'), 'XDG_RUNTIME_DIR': f'/run/user/{UID}',
           'CONTAINER_ID': 'dev' if profile.get('source') else profile['name'],
           'PODMAN_WORKBENCH': profile['name'], 'HOST_HOME': '/host-home',
           'PATH': f'{HOME}/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
           'DOCKER_HOST': ('unix:///host-home/.local/state/podman-workbench/docker.sock'
                           if profile.get('source') else ''),
           'DOCKER_CONTEXT': '', 'SSH_AUTH_SOCK': '',
           'DBUS_SESSION_BUS_ADDRESS': '', 'LANG': 'C.UTF-8',
           'TERM': os.environ.get('TERM', 'xterm-256color')}
    display = os.environ.get('DISPLAY', '')
    display_number = re.search(r':(\d+)(?:\.\d+)?$', display)
    x_socket = Path('/tmp/.X11-unix') / ('X' + display_number[1]) if display_number else None
    if display and x_socket and x_socket.is_socket():
        # Only the parent display socket is shared. Xephyr needs a PRIVATE,
        # writable .X11-unix directory for its own virtual display.
        args += ['--mount', f'type=bind,source={x_socket},destination=/host-x11/{x_socket.name},ro']
        env['DISPLAY'] = os.environ['DISPLAY']
        authority = Path(os.environ.get('XAUTHORITY', str(HOME / '.Xauthority')))
        if authority.is_file():
            env['XAUTHORITY'] = str(HOME / '.Xauthority')
    runtime = Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{UID}'))
    wayland = os.environ.get('WAYLAND_DISPLAY', '')
    if wayland and '/' not in wayland and (runtime / wayland).is_socket():
        args += ['--mount', f'type=bind,source={runtime / wayland},destination=/run/user/{UID}/{wayland}']
        env['WAYLAND_DISPLAY'] = wayland
    if (runtime / 'pulse/native').is_socket():
        args += ['--mount', f'type=bind,source={runtime / "pulse/native"},destination=/run/user/{UID}/pulse/native']
        env['PULSE_SERVER'] = f'unix:/run/user/{UID}/pulse/native'
    if profile.get('source') and (runtime / 'bus').is_socket():
        args += ['--mount', f'type=bind,source={runtime / "bus"},destination=/host-session/bus,ro']
        env['DBUS_SESSION_BUS_ADDRESS'] = 'unix:path=/host-session/bus'
    if Path('/dev/dri').exists():
        args += ['--device', '/dev/dri']
    if profile.get('source') and Path('/dev/kvm').exists():
        args += ['--device', '/dev/kvm']
    for key, value in env.items():
        args += ['--env', f'{key}={value}']
    return [*args, image, 'infinity']


def seed_home(name, key):
    components = ['shell', 'nvim', 'fastfetch', 'files']
    if key == 'dev':
        components += ['alacritty', 'awesome', 'polybar', 'rofi', 'themes', 'fonts',
                       'wallpaper', 'flutter', 'docker', 'dbeaver', 'rider']
    for component in components:
        source = REPO / 'components' / component / 'dotfiles'
        if source.is_dir():
            pipe_tar(name, ['.'], HOME, source)


def has_marker(name, marker):
    return subprocess.run([*PODMAN, 'exec', '--user', '0', name, 'test', '-e',
                           f'/var/lib/podman-workbench/{marker}']).returncode == 0


def mark(name, marker):
    execute(name, 'bash', '-c',
            'mkdir -p /var/lib/podman-workbench; touch /var/lib/podman-workbench/' + marker,
            root=True)


def integrate_dev():
    """No host packages: forward the existing engine and copy desktop assets."""
    name = PROFILES['dev']['name']
    start(name)
    execute(name, 'python3', '-', data=(ROOT / 'share_documents.py').read_text())
    execute(name, 'pacman', '-S', '--needed', '--noconfirm', 'xorg-xrdb', 'xorg-xsetroot', root=True)
    units = HOME / '.config/systemd/user'
    units.mkdir(parents=True, exist_ok=True)
    for source in (ROOT / 'systemd').glob('workbench-podman.*'):
        shutil.copyfile(source, units / source.name)
    run(['systemctl', '--user', 'daemon-reload'])
    run(['systemctl', '--user', 'enable', 'workbench-podman.socket'])
    run(['systemctl', '--user', 'start', 'workbench-podman.socket'])
    execute(name, 'mkdir', '-p', '/tmp/workbench-icons')
    source = Path('/usr/share/icons')
    if not (source / 'Bibata-Modern-Classic').is_dir():
        source = Path('/run/host/usr/share/icons')
    themes = [theme for theme in ('Bibata-Modern-Classic', 'Oranchelo')
              if (source / theme).is_dir()]
    pipe_tar(name, themes, '/tmp/workbench-icons', source, dereference=False)
    execute(name, 'python3', '-', data=(ROOT / 'integrate_dev.py').read_text())
    execute(name, 'rm', '-rf', '/tmp/workbench-icons')


def integrate_security(key):
    if key not in ('parrotos', 'kali'):
        raise ValueError('Se requiere un perfil de seguridad.')
    name = PROFILES[key]['name']
    start(name)
    helpers = HOME / '.local/libexec/podman-workbench'
    execute(name, 'mkdir', '-p', str(helpers), '/tmp/workbench-icons')
    pipe_tar(name, ['configure_security.py', 'share_documents.py'], helpers, ROOT)
    source = Path('/usr/share/icons')
    themes = [theme for theme in ('Bibata-Modern-Classic', 'Oranchelo')
              if (source / theme).is_dir()]
    pipe_tar(name, themes, '/tmp/workbench-icons', source, dereference=False)
    palette = ''
    if shutil.which('vivid'):
        result = subprocess.run(['vivid', 'generate', 'tokyonight-night'], capture_output=True, text=True)
        if result.returncode == 0:
            palette = result.stdout.strip()
    shared_repo = Path('/host-home') / REPO.relative_to(HOME)
    execute(name, 'env', 'WORKBENCH_LS_COLORS=' + palette,
            'python3', str(helpers / 'configure_security.py'), '--repo', str(shared_repo))
    execute(name, 'rm', '-rf', '/tmp/workbench-icons')


def setup(key, fresh=False):
    profile = PROFILES[key]
    name = profile['name']
    info = inspect(name)
    if info:
        managed(name)
        start(name)
        if has_marker(name, 'ready'):
            verify(key)
            print(f'{name} ya estaba preparado; no se sobrescribió su home.')
            return
        recorded = info['Config']['Labels'].get('workbench.mode', 'copy')
        if (recorded == 'fresh') != fresh:
            raise RuntimeError('Reanuda la preparación usando el mismo valor de --fresh.')
        print(f'Reanudando la preparación incompleta de {name}.')
    image = profile['image']
    if not info and key == 'dev' and not fresh:
        source = inspect(profile['source'])
        if source is None:
            raise RuntimeError('Falta dev original. Usa setup dev --fresh para reconstruir desde las recetas.')
        image = 'localhost/workbench-dev-snapshot:initial'
        p = subprocess.run([*PODMAN, 'image', 'exists', image])
        if p.returncode == 1:
            # Does not pause or reconfigure the original container; excludes all mounts.
            pod('commit', '--pause=false', '--include-volumes=false',
                '--change', f'LABEL manager={MANAGER}', profile['source'], image)
        elif p.returncode:
            raise RuntimeError('No se pudo consultar la imagen de dev.')
    if not info:
        args = create_args(profile, image)
        args[1:1] = ['--label', 'workbench.mode=' + ('fresh' if fresh else 'copy')]
        pod(*args)
    start(name)
    packages = ((ROOT / profile['packages_file']).read_text().splitlines()
                if key == 'dev' else profile['apt_packages'])
    # Snapshot already contains installed packages; fresh environments use recipes.
    script = (ROOT / 'prepare.sh').read_text()
    execute(name, 'bash', '-s', '--', str(UID), str(GID), USER, str(HOME),
            'yes' if key != 'dev' or fresh else 'no', *packages, root=True, data=script)
    refresh_authority(name)
    if not has_marker(name, 'home-copied'):
        seed_home(name, key)
        copies = BASE_COPY + (DEV_COPY if key == 'dev' and not fresh else [])
        files = [p for p in copies if (HOME / p).exists()]
        pipe_tar(name, files, HOME)
        execute(name, 'mkdir', '-p', f'{HOME}/.local/libexec/workbench-source')
        # Versioned installers, never a bind mount back to the original dotfiles.
        pipe_tar(name, ['components', 'scripts'], f'{HOME}/.local/libexec/workbench-source', REPO)
        mark(name, 'home-copied')
    if key == 'dev' and fresh:
        # SDK Manager must read the user's terminal for Android's licenses,
        # never consume the provisioning script itself as license responses.
        pod('exec', '-it', '--user', f'{UID}:{GID}', name, 'bash',
            str(HOME / '.local/libexec/workbench-source/components/workbench/podman/finish.sh'),
            key, 'fresh')
    else:
        execute(name, 'bash', '-s', '--', key, 'copy', data=(ROOT / 'finish.sh').read_text())
    if key == 'dev':
        integrate_dev()
    else:
        integrate_security(key)
    verify(key)
    mark(name, 'ready')
    print(f'{name} preparado. Home interno: {HOME}; home compartido: /host-home')


def verify(key):
    name = PROFILES[key]['name']
    info = managed(name)
    home_mounts = [m for m in info.get('Mounts', [])
                   if m['Destination'] == str(HOME) or m['Destination'].startswith(str(HOME) + '/')]
    if home_mounts:
        raise RuntimeError('El home interno está montado desde fuera del contenedor.')
    mounts = info.get('Mounts', [])
    if any(m['Destination'] in ('/tmp/.X11-unix', '/run/workbench.Xauthority') for m in mounts):
        raise RuntimeError('La conexión gráfica usa montajes antiguos; necesita sockets privados y autorización interna.')
    if not any(m['Destination'] == '/host-home' and Path(m['Source']) == HOME for m in mounts):
        raise RuntimeError('Falta el montaje explícito /host-home.')
    if any(m['Type'] == 'volume' for m in mounts):
        raise RuntimeError('Se encontró un volumen externo no previsto.')
    if any('podman.sock' in m['Source'] or 'docker.sock' in m['Source'] for m in mounts):
        raise RuntimeError('Se encontró un socket de motor del host no previsto.')
    start(name)
    refresh_authority(name)
    execute(name, 'bash', '-s', '--', key, data=(ROOT / 'verify.sh').read_text())


def lifecycle(action, key, options=()):
    """Operate on exactly one managed container; never expand to all/latest."""
    name = PROFILES[key]['name']
    info = managed(name)
    if action == 'rm':
        if any(option not in ('--force', '-f', '--volumes', '-v') for option in options):
            raise RuntimeError('rm admite únicamente --force/-f y --volumes/-v.')
    elif options:
        raise RuntimeError(f'{action} no admite argumentos adicionales.')
    if action == 'start':
        start(name)
    elif action == 'ps':
        pod('ps', '-a', '--filter', 'name=^' + name + '$')
    else:
        pod(action, *options, info['Id'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['setup', 'enter', 'exec', 'verify', 'status', 'integrate',
                                         'start', 'stop', 'restart', 'rm', 'ps', 'inspect', 'logs'])
    parser.add_argument('profile', choices=[*PROFILES, 'all'])
    parser.add_argument('--fresh', action='store_true', help='Reconstruir dev desde paquetes e instaladores, sin snapshot.')
    args, command = parser.parse_known_args()
    if command[:1] == ['--']:
        command = command[1:]
    if command and args.action not in ('exec', 'rm'):
        parser.error('Argumentos no reconocidos: ' + shlex.join(command))
    if args.fresh and args.action != 'setup':
        parser.error('--fresh solo se usa con setup')
    if UID == 0:
        parser.error('Ejecuta este comando como tu usuario normal, sin sudo.')
    if args.fresh and args.profile in ('dev', 'all') and not sys.stdin.isatty():
        parser.error('--fresh requiere una terminal interactiva para revisar las licencias de Android.')
    if args.profile == 'all' and args.action not in ('setup', 'verify', 'status'):
        parser.error('Usa un perfil concreto para enter o exec')
    # The client may explicitly select Podman's supported remote API.
    # Never fall back to sudo, a different engine, or Distrobox creation.
    pod('info', stdout=subprocess.DEVNULL)
    keys = list(PROFILES) if args.profile == 'all' else [args.profile]
    for key in keys:
        name = PROFILES[key]['name']
        if args.action == 'setup':
            # Independent clients may prepare different profiles concurrently.
            # Serialize two setup requests targeting the same profile.
            with open(f'/tmp/podman-workbench-{UID}-{key}.lock', 'a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                setup(key, args.fresh)
        elif args.action == 'verify':
            verify(key)
        elif args.action == 'status':
            info = inspect(name)
            print(f'{name}: {info["State"]["Status"] if info else "no creado"}')
        elif args.action == 'integrate':
            if key == 'dev':
                integrate_dev()
            else:
                integrate_security(key)
                verify(key)
        elif args.action in ('start', 'stop', 'restart', 'rm', 'ps', 'inspect', 'logs'):
            lifecycle(args.action, key, command)
        else:
            start(name)
            refresh_authority(name)
            invocation = [*PODMAN, 'exec', '--user', f'{UID}:{GID}', '--workdir', str(HOME)]
            if key == 'dev':
                endpoint = os.environ.get('DOCKER_HOST') or 'unix:///host-home/.local/state/podman-workbench/docker.sock'
                if endpoint == f'unix:///run/user/{UID}/podman/podman.sock':
                    endpoint = 'unix:///host-home/.local/state/podman-workbench/docker.sock'
                invocation += ['--env', 'DOCKER_HOST=' + endpoint,
                               '--env', 'DOCKER_CONTEXT=' + os.environ.get('DOCKER_CONTEXT', ''),
                               '--env', 'XCURSOR_THEME=Bibata-Modern-Classic', '--env', 'XCURSOR_SIZE=24']
            if os.environ.get('DISPLAY'):
                invocation += ['--env', 'DISPLAY=' + os.environ['DISPLAY'],
                               '--env', 'XAUTHORITY=' + str(HOME / '.Xauthority')]
            if sys.stdin.isatty():
                invocation += ['-it']
            invocation += [name, *(command or ['zsh', '-l'])]
            os.execvp(PODMAN[0], invocation)


if __name__ == '__main__':
    try:
        main()
    except (subprocess.CalledProcessError, OSError, RuntimeError) as error:
        print(f'Error: {error}', file=sys.stderr)
        sys.exit(1)
