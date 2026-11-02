#!/usr/bin/python3 -I
"""Install/remove managed workbench mount wrappers inside a rootless lab container."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

MARKER = '# Managed workbench mount bridge'
PREFIX = Path('/usr/local')
SUDOERS = Path('/etc/sudoers.d/workbench-mount-bridge')


def check(path):
    if path.is_symlink() or (path.exists() and MARKER not in path.read_text()):
        raise RuntimeError(f'Se conserva el archivo ajeno: {path}')


def configure(source=None, username=None):
    paths = [PREFIX / 'sbin' / name for name in ('mount', 'umount')]
    for path in [*paths, SUDOERS]:
        check(path)
    if source is None:
        for path in [*paths, SUDOERS]:
            path.unlink(missing_ok=True)
        return
    if not re.fullmatch(r'[a-z_][a-z0-9_-]*\$?', username):
        raise RuntimeError('Usuario inválido.')
    library = PREFIX / 'libexec/workbench-mount-bridge'
    if library.is_symlink():
        raise RuntimeError('La biblioteca del puente no puede ser un enlace simbólico.')
    for name in ('mounts.py', 'mount_policy.py'):
        target = library / name
        if target.is_symlink() or (target.exists() and 'workbench' not in target.read_text().lower()):
            raise RuntimeError(f'Se conserva el archivo ajeno: {target}')
    library.mkdir(parents=True, exist_ok=True)
    for name in ('mounts.py', 'mount_policy.py'):
        shutil.copyfile(source / name, library / name)
        (library / name).chmod(0o644)
    for path, action in zip(paths, ('bridge-mount', 'bridge-umount')):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('#!/usr/bin/env bash\n' + MARKER + '\n'
                        'exec /usr/bin/python3 -I /usr/local/libexec/workbench-mount-bridge/mounts.py '
                        + action + ' "$@"\n')
        path.chmod(0o755)
    SUDOERS.write_text(MARKER + '\nDefaults:' + username +
                       ' secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"\n')
    SUDOERS.chmod(0o440)
    subprocess.run(['/usr/sbin/visudo', '-cf', str(SUDOERS)], check=True)


if __name__ == '__main__':
    if os.geteuid() != 0 or not Path('/run/.containerenv').exists():
        raise SystemExit('Instala este puente únicamente como root dentro del contenedor.')
    if sys.argv[1:] == ['--remove']:
        configure()
    elif len(sys.argv) == 3:
        configure(Path(sys.argv[1]), sys.argv[2])
    else:
        raise SystemExit('Argumentos inválidos.')
