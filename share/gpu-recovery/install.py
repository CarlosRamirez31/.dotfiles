#!/usr/bin/env python3
"""Install/remove the checked LOQ recovery service as root-owned files."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess

UNIT = 'dotfiles-gpu-recovery.service'
ASSETS = Path(__file__).resolve().parent
PROGRAM = Path('/usr/local/libexec/dotfiles-gpu-recovery')
DESTINATION = Path('/etc/systemd/system') / UNIT


def run(*args):
    subprocess.run(args, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--uninstall', action='store_true')
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SystemExit('Ejecuta este instalador con sudo desde la terminal del sistema.')
    if args.uninstall:
        # Stop first: ExecStopPost restores GPE10 before files are removed.
        run('systemctl', 'disable', '--now', UNIT)
        PROGRAM.unlink(missing_ok=True)
        DESTINATION.unlink(missing_ok=True)
        run('systemctl', 'daemon-reload')
        print('Servicio retirado.')
        return
    run('/usr/bin/python3', str(ASSETS / 'monitor.py'), '--check')
    # Check the unit's syntax before replacing the installed version.
    run('systemd-analyze', 'verify', str(ASSETS / UNIT))
    if DESTINATION.exists():
        run('systemctl', 'stop', UNIT)
    PROGRAM.parent.mkdir(parents=True, exist_ok=True)
    for source, target, mode in ((ASSETS / 'monitor.py', PROGRAM, 0o755),
                                 (ASSETS / UNIT, DESTINATION, 0o644)):
        shutil.copyfile(source, target)
        target.chmod(mode)
        os.chown(target, 0, 0)
    run('systemctl', 'daemon-reload')
    run('systemctl', 'enable', '--now', UNIT)
    run('systemctl', 'is-active', UNIT)
    print('Recuperación automática instalada. Registro: journalctl -u ' + UNIT)


if __name__ == '__main__':
    main()
