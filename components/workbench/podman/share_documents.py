#!/usr/bin/env python3
"""Use the entire host Documents folder, preserving any private files."""
import os
from pathlib import Path
import uuid


def share_documents(home, shared):
    documents = home / 'Documents'
    if not shared.is_dir():
        raise RuntimeError(f'No existe la carpeta compartida: {shared}')
    if documents.is_symlink() and documents.resolve() == shared.resolve():
        return None
    backup = None
    if documents.exists() or documents.is_symlink():
        folder = home / '.local/state/podman-workbench'
        folder.mkdir(parents=True, exist_ok=True)
        backup = folder / ('documents-before-share-' + uuid.uuid4().hex[:12])
        documents.rename(backup)
    try:
        documents.symlink_to(shared, target_is_directory=True)
    except OSError:
        if backup is not None:
            backup.rename(documents)
        raise
    return backup


if __name__ == '__main__':
    if os.environ.get('PODMAN_WORKBENCH') not in ('dev-podman', 'parrotos-podman', 'kali-podman') or not Path('/run/.containerenv').exists():
        raise SystemExit('Ejecuta este script dentro de un contenedor Podman workbench.')
    backup = share_documents(Path.home(), Path('/host-home/Documents'))
    print('~/Documents enlazado completo a /host-home/Documents.')
    if backup:
        print(f'Contenido interno anterior conservado en: {backup}')
