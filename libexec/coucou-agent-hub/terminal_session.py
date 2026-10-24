#!/usr/bin/env python3
"""Coucou terminal lifecycle: exact Hub route, then agent selection on exit."""
import argparse
from pathlib import Path
import signal
import subprocess
import sys


def session(route_file, run=subprocess.call):
    path = Path(route_file)
    if not path.is_absolute() or not path.is_file():
        print('Coucou: no está disponible el descriptor de la conversación.', file=sys.stderr)
        return 1
    # The terminal delivers Ctrl+C to the foreground process group. Keep only
    # this parent alive; the native CLI receives and handles the signal itself.
    previous = signal.signal(signal.SIGINT, lambda number, frame: None)
    try:
        code = run(['agent-hub', 'open', '--route-file', str(path)])
        if code not in (0, 130, -signal.SIGINT):
            return code  # A failed route must never launch another conversation.
        return run(['agent-hub'])  # Registry/agent selector; never --last or implicit new.
    finally:
        signal.signal(signal.SIGINT, previous)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--route-file', required=True)
    args = parser.parse_args()
    try:
        return session(args.route_file)
    except OSError as error:
        print('Coucou: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
