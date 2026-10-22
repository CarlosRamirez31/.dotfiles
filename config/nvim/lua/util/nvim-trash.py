#!/usr/bin/env python3
"""Private, five-hour trash shared by host and Distrobox Neovim sessions."""
import argparse
import contextlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import time
import uuid

RETENTION = 5 * 60 * 60


class Trash:
    def __init__(self, root=None):
        self.root = Path(root or Path.home() / '.local/share/nvim-trash').absolute()
        self.items = self.root / 'items'

    @contextlib.contextmanager
    def locked(self):
        self.items.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.root.chmod(0o700)
        with (self.root / '.lock').open('a+b') as lock:
            if os.name == 'nt':
                import msvcrt
                if lock.seek(0, 2) == 0:
                    lock.write(b'0')
                    lock.flush()
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(lock, fcntl.LOCK_EX)
            yield

    @staticmethod
    def exists(path):
        return os.path.lexists(path)

    def entries(self):
        entries = []
        for folder in self.items.iterdir():
            if folder.is_symlink() or not folder.is_dir():
                continue
            try:
                info = json.loads((folder / 'info.json').read_text())
                if not isinstance(info, dict):
                    continue
                if (info.get('id') != folder.name or not isinstance(info.get('original'), str)
                        or not isinstance(info.get('expires_at'), (int, float))
                        or not isinstance(info.get('deleted_at'), (int, float))
                        or info.get('kind') not in ('file', 'directory')):
                    continue
                if self.exists(folder / 'payload'):
                    entries.append(info)
            except (OSError, ValueError, TypeError):
                # Unknown/corrupt records are never automatically destroyed.
                continue
        return sorted(entries, key=lambda info: info['deleted_at'], reverse=True)

    def put(self, paths, now=None):
        now = time.time() if now is None else now
        paths = sorted(set(os.path.abspath(path) for path in paths), key=lambda path: len(Path(path).parts))
        selected = []
        errors = []
        # A selected directory subsumes selected descendants, including links.
        for value in paths:
            path = Path(value)
            if any(parent in path.parents for parent in selected if parent.is_dir() and not parent.is_symlink()):
                continue
            selected.append(path)
        entries = []
        for path in selected:
            folder = None
            try:
                if not self.exists(path):
                    raise ValueError('La ruta ya no existe')
                source = path.parent.resolve() / path.name
                root = self.root.resolve()
                if source == root or source in root.parents or root in source.parents:
                    raise ValueError('No se puede enviar la papelera ni sus directorios contenedores a sí misma')
                mode = path.lstat().st_mode
                if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode) or stat.S_ISLNK(mode)):
                    raise ValueError('Solo se admiten archivos, carpetas y enlaces')
                identifier = uuid.uuid4().hex
                folder = self.items / identifier
                folder.mkdir(mode=0o700)
                info = {
                    'id': identifier, 'original': str(source), 'name': path.name,
                    'kind': 'directory' if stat.S_ISDIR(mode) else 'file',
                    'deleted_at': now, 'expires_at': now + RETENTION,
                }
                # Journal first: a crash after the move still leaves a recoverable entry.
                metadata = folder / 'info.json'
                with metadata.open('x', encoding='utf-8') as stream:
                    json.dump(info, stream, ensure_ascii=False)
                    stream.flush()
                    os.fsync(stream.fileno())
                shutil.move(str(path), str(folder / 'payload'))
                entries.append(info)
            except (OSError, ValueError, shutil.Error) as error:
                errors.append({'path': str(path), 'error': str(error)})
                # Preserve anything copied/moved before a failure for recovery.
                if folder and not self.exists(folder / 'payload'):
                    shutil.rmtree(folder)
        return {'entries': entries, 'errors': errors}

    def restore(self, identifier, now=None):
        now = time.time() if now is None else now
        if len(identifier) != 32 or any(c not in '0123456789abcdef' for c in identifier):
            raise ValueError('Identificador de papelera inválido')
        info = next((entry for entry in self.entries() if entry['id'] == identifier), None)
        if info is None:
            raise ValueError('La entrada ya no está en la papelera')
        if info['expires_at'] <= now:
            raise ValueError('La entrada cumplió las cinco horas de retención')
        destination = Path(info['original'])
        if self.exists(destination):
            raise ValueError('Ya existe un archivo o carpeta en la ruta original; no se sobrescribió')
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = self.items / identifier / 'payload'
        # Reserve the destination atomically so a concurrently recreated file
        # cannot be silently overwritten by rename/shutil.move.
        is_directory = info['kind'] == 'directory'
        if is_directory:
            destination.mkdir()
        else:
            fd = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
        try:
            if is_directory:
                # Move into our reserved empty directory, then rename contents.
                # os.replace can atomically replace an empty reserved directory.
                try:
                    os.replace(payload, destination)
                except OSError as error:
                    import errno
                    if error.errno != errno.EXDEV:
                        raise
                    shutil.copytree(payload, destination, dirs_exist_ok=True, symlinks=True)
                    shutil.rmtree(payload)
            else:
                try:
                    os.replace(payload, destination)
                except OSError as error:
                    import errno
                    if error.errno != errno.EXDEV:
                        raise
                    if payload.is_symlink():
                        destination.unlink()
                        destination.symlink_to(os.readlink(payload))
                        payload.unlink()
                    else:
                        shutil.copy2(payload, destination)
                        payload.unlink()
        except Exception:
            # Only remove an untouched reservation; never remove partial recovery data.
            if destination.is_dir() and not any(destination.iterdir()):
                destination.rmdir()
            elif destination.is_file() and destination.stat().st_size == 0:
                destination.unlink()
            raise
        shutil.rmtree(self.items / identifier)
        return info

    def purge(self, now=None):
        now = time.time() if now is None else now
        removed = []
        for info in self.entries():
            if info['expires_at'] <= now:
                shutil.rmtree(self.items / info['id'])
                removed.append(info['id'])
        return removed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest='action', required=True)
    put = sub.add_parser('put')
    put.add_argument('paths', nargs='+')
    sub.add_parser('list')
    restore = sub.add_parser('restore')
    restore.add_argument('identifier')
    sub.add_parser('purge')
    args = parser.parse_args()
    trash = Trash(args.root)
    try:
        with trash.locked():
            if args.action == 'put':
                result = trash.put(args.paths)
            elif args.action == 'restore':
                result = {'restored': trash.restore(args.identifier)}
            elif args.action == 'purge':
                result = {'purged': trash.purge()}
            else:
                result = {'entries': [entry for entry in trash.entries() if entry['expires_at'] > time.time()]}
        print(json.dumps(result, ensure_ascii=False))
    except (OSError, ValueError, shutil.Error) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
