"""Attach the integrated camera to an existing rootless dev container.

Run through podman unshare. Detached mount trees allow adding the devices
without rebuilding or stopping the container and without host sudo.
"""
import ctypes
import os
from pathlib import Path
import subprocess
import sys


def main():
    pid = int(sys.argv[1])
    libc = ctypes.CDLL(None, use_errno=True)
    for device in sys.argv[2:]:
        if device not in ('/dev/video0', '/dev/video1'):
            raise ValueError('Only the integrated camera nodes are supported')
        if not Path(device).is_char_device():
            continue
        # Linux open_tree(OPEN_TREE_CLONE) then move_mount(EMPTY_PATH).
        tree = libc.syscall(428, -100, device.encode(), 1 | os.O_CLOEXEC)
        if tree < 0:
            raise OSError(ctypes.get_errno(), 'open_tree', device)
        code = ('import ctypes; lib=ctypes.CDLL(None,use_errno=True); '
                f'r=lib.syscall(429,{tree},b"",-100,{device.encode()!r},4); '
                'err=ctypes.get_errno(); '
                'assert r == 0, ("move_mount",err)')
        try:
            subprocess.run([
                'nsenter', f'--user=/proc/{pid}/ns/user',
                f'--mount=/proc/{pid}/ns/mnt', f'--pid=/proc/{pid}/ns/pid',
                'python', '-c', code,
            ], pass_fds=(tree,), check=True)
        finally:
            os.close(tree)


if __name__ == '__main__':
    main()
