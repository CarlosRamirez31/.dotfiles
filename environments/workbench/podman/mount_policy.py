"""Workbench dynamic mount policy, shared by the client and root-owned helper."""
from pathlib import PurePosixPath
import re

TARGET = '/mnt/montajes'
NAME = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}')
TYPES = {'cifs', 'nfs', 'nfs4', 'iso9660', 'udf', 'auto', 'ext4', 'vfat', 'exfat', 'ntfs3'}
FLAGS = {'ro', 'rw', 'nosuid', 'nodev', 'noexec', 'exec', 'sync', 'async', 'dirsync', 'noatime', 'relatime'}


def clean_text(value, limit=2048):
    return isinstance(value, str) and len(value) <= limit and not any(c in value for c in '\x00\r\n')


def validate(payload, uid, gid):
    if not isinstance(payload, dict):
        raise ValueError('Solicitud inválida.')
    action = payload.get('action')
    fields = {'action', 'target'} if action == 'detach' else {'action', 'target', 'source', 'fstype', 'options', 'auth'}
    if action not in ('attach', 'detach') or set(payload) != fields:
        raise ValueError('Operación o campos no permitidos.')
    target = payload['target']
    if not clean_text(target):
        raise ValueError('Destino inválido.')
    path = PurePosixPath(target)
    if str(path) != target or str(path.parent) != TARGET or not NAME.fullmatch(path.name):
        raise ValueError('Usa una subcarpeta directa de /mnt/montajes, sin enlaces ni ..')
    if action == 'detach':
        return payload
    source, kind, options, auth = (payload[k] for k in ('source', 'fstype', 'options', 'auth'))
    if not isinstance(kind, str) or kind not in TYPES or not clean_text(source) or not source:
        raise ValueError('Origen o sistema de archivos no admitido.')
    if kind == 'cifs':
        if not re.fullmatch(r'//[^/\s]+/[^\x00\r\n]+', source):
            raise ValueError('CIFS requiere //SERVIDOR/RECURSO.')
    elif kind in ('nfs', 'nfs4'):
        if not re.fullmatch(r'(?:\[[0-9a-fA-F:%.]+\]|[^/:\s]+):/[^\x00\r\n]*', source):
            raise ValueError('NFS requiere SERVIDOR:/recurso.')
    elif kind in ('iso9660', 'udf'):
        if not source.startswith('/host-home/') or '..' in PurePosixPath(source).parts:
            raise ValueError('Las imágenes deben estar en /host-home (el home compartido del anfitrión).')
    elif not source.startswith('/dev/') or '..' in PurePosixPath(source).parts:
        raise ValueError('Este tipo requiere un dispositivo extraíble del anfitrión en /dev/.')
    if not isinstance(auth, dict) or set(auth) - {'username', 'password', 'domain'}:
        raise ValueError('Credenciales inválidas.')
    if (auth and kind != 'cifs') or any(not clean_text(v) for v in auth.values()):
        raise ValueError('Credenciales inválidas.')
    if not isinstance(options, list) or len(options) > 32:
        raise ValueError('Opciones inválidas.')
    for option in options:
        if not clean_text(option, 128) or ',' in option or not option:
            raise ValueError('Opción inválida.')
        key, sep, value = option.partition('=')
        allowed = not sep and key in FLAGS
        if kind == 'cifs':
            allowed |= (not sep and key in {'guest', 'nounix', 'noserverino', 'serverino'})
            allowed |= bool(sep and key == 'vers' and value in {'2.0', '2.1', '3.0', '3.02', '3.1.1', 'default'})
            allowed |= bool(sep and key == 'sec' and value in {'ntlmssp', 'ntlmsspi', 'ntlmv2', 'ntlmv2i'})
            allowed |= bool(sep and key in {'file_mode', 'dir_mode'} and re.fullmatch(r'0?[0-7]{3}', value))
        if kind in ('nfs', 'nfs4'):
            allowed |= (not sep and key in {'soft', 'hard', 'nolock', 'lock'})
            allowed |= bool(sep and key in {'vers', 'nfsvers'} and value in {'3', '4', '4.0', '4.1', '4.2'})
            allowed |= bool(sep and key in {'proto', 'mountproto'} and value in {'tcp', 'udp'})
            allowed |= bool(sep and key == 'sec' and value == 'sys')
            allowed |= bool(sep and key in {'timeo', 'retrans', 'rsize', 'wsize'} and value.isdecimal() and 1 <= int(value) <= 1048576)
        if kind in ('iso9660', 'udf'):
            allowed |= not sep and key == 'loop'
        if kind in ('cifs', 'vfat', 'exfat', 'ntfs3'):
            allowed |= bool(sep and key == 'uid' and value == str(uid))
            allowed |= bool(sep and key == 'gid' and value == str(gid))
            allowed |= bool(sep and key == 'iocharset' and value == 'utf8')
            allowed |= bool(sep and key in {'umask', 'fmask', 'dmask'} and re.fullmatch(r'0?[0-7]{3}', value))
        if kind in ('cifs', 'nfs', 'nfs4'):
            allowed |= bool(sep and key in {'port', 'mountport'} and value.isdecimal() and 1 <= int(value) <= 65535)
        if not allowed:
            # Do not echo an untrusted option: it may contain a password.
            raise ValueError('Opción no permitida para este sistema de archivos.')
    return payload
