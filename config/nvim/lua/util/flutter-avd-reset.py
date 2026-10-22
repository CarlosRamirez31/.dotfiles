#!/usr/bin/env python3
"""Clear a stopped AVD's writable state without launching Android.

The artifact list follows Android Emulator's clean_up_avd_contents_except_config_ini:
https://android.googlesource.com/platform/external/qemu/+/refs/heads/emu-35-3-release/android/emulator/main-emulator.cpp
"""
import contextlib
import os
from pathlib import Path
import shutil
import sys


ARTIFACTS = (
    'system.img.qcow2', 'vendor.img.qcow2', 'userdata-qemu.img',
    'userdata-qemu.img.qcow2', 'userdata.img', 'userdata.img.qcow2',
    'cache.img', 'cache.img.qcow2', 'version_num.cache', 'bootcompleted.ini',
    'sdcard.img.qcow2', 'encryptionkey.img', 'encryptionkey.img.qcow2',
    'hardware-qemu.ini', 'emulator-user.ini', 'quickbootChoice.ini',
    'emu-launch-params.txt', 'initrd', 'AVD.conf', 'read-snapshot.txt',
    'data', 'modem_simulator', 'default.dtb', 'snapshots', 'snapshot.trace',
)


def avd_directory(name):
    if not name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-' for c in name):
        raise ValueError('Nombre de AVD inválido')
    if name in ('.', '..'):
        raise ValueError('Nombre de AVD inválido')
    home = Path.home()
    roots = []
    if os.environ.get('ANDROID_AVD_HOME'):
        roots.append(Path(os.environ['ANDROID_AVD_HOME']))
    roots.append(Path(os.environ.get('ANDROID_EMULATOR_HOME', home / '.android')) / 'avd')
    if os.environ.get('ANDROID_USER_HOME'):
        roots.append(Path(os.environ['ANDROID_USER_HOME']) / 'avd')
    if os.environ.get('ANDROID_SDK_HOME'):
        roots.append(Path(os.environ['ANDROID_SDK_HOME']) / '.android/avd')
    for root in roots:
        ini = root / (name + '.ini')
        if not ini.is_file():
            continue
        values = dict(line.strip().split('=', 1) for line in ini.read_text().splitlines() if '=' in line)
        if values.get('path'):
            directory = Path(values['path'])
        elif values.get('path.rel'):
            directory = root.parent / values['path.rel']
        else:
            raise ValueError('El AVD no declara su directorio de datos')
        directory = directory.resolve()
        if directory.suffix != '.avd' or not (directory / 'config.ini').is_file():
            raise ValueError('Directorio de AVD inválido; no se borró ningún archivo')
        return directory
    raise ValueError('No se encontró el AVD seleccionado')


@contextlib.contextmanager
def exclusive_avd(directory):
    # Keep the existing lock inode: unlinking it would permit a concurrent boot.
    with (directory / 'multiinstance.lock').open('a+b') as lock:
        try:
            if os.name == 'nt':
                import msvcrt
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.lockf(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise ValueError('El AVD sigue en uso. Ciérralo y vuelve a intentar; no se borraron sus datos') from error
        yield


def reset(name):
    directory = avd_directory(name)
    with exclusive_avd(directory):
        # A custom data disk outside the AVD requires explicit manual handling.
        config = (directory / 'config.ini').read_text()
        for line in config.splitlines():
            if line.startswith('disk.dataPartition.path='):
                disk = line.split('=', 1)[1].strip()
                if disk and disk != '<temp>' and Path(disk).name not in ('userdata.img', 'userdata-qemu.img'):
                    raise ValueError('El AVD usa un disco de datos personalizado; no se borró ningún archivo')
                if disk and disk != '<temp>' and (directory / disk).resolve().parent != directory:
                    raise ValueError('El disco de datos está fuera del AVD; no se borró ningún archivo')
        for name in ARTIFACTS:
            path = directory / name
            if path.is_symlink() or path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
    print('Datos borrados. El emulador permanece apagado.')


if __name__ == '__main__':
    try:
        if len(sys.argv) != 2:
            raise ValueError('Indica un único AVD')
        reset(sys.argv[1])
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
