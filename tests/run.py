#!/usr/bin/env python3
"""Run offline regressions from any working directory, without host installation."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    failures = []
    for folder in sorted((ROOT / 'tests').iterdir()):
        if not folder.is_dir() or folder.name == '__pycache__':
            continue
        if list(folder.glob('test_*.py')):
            print(f'== Python: {folder.name} ==', flush=True)
            result = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(folder)], cwd=ROOT)
            if result.returncode:
                failures.append(str(folder.relative_to(ROOT)))
        for path in sorted(folder.glob('test_*.lua')):
            print(f'== Lua: {path.relative_to(ROOT)} ==', flush=True)
            command = (['nvim', '--headless', '-u', 'NONE', '-i', 'NONE', '-l']
                       if folder.name == 'nvim' else ['lua'])
            try:
                result = subprocess.run([*command, str(path)], cwd=ROOT, timeout=60,
                                        env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
                if result.returncode:
                    failures.append(str(path.relative_to(ROOT)))
            except (OSError, subprocess.TimeoutExpired) as error:
                print(error, file=sys.stderr)
                failures.append(str(path.relative_to(ROOT)))
    if failures:
        print('Failed suites: ' + ', '.join(failures), file=sys.stderr)
    return bool(failures)


if __name__ == '__main__':
    sys.exit(main())
