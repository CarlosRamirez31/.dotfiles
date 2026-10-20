#!/usr/bin/env python3
"""Configure only physical keyboard input; preserve the rest of the AVD."""
import argparse
from pathlib import Path
import re

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('config', type=Path)
parser.add_argument('keyboard', choices=('yes', 'no', 'keep'))
args = parser.parse_args()
if args.keyboard != 'keep':
    original = args.config.read_bytes()
    newline = b'\r\n' if b'\r\n' in original else b'\n'
    setting = b'hw.keyboard=' + args.keyboard.encode('ascii')
    pattern = rb'(?m)^hw\.keyboard[ \t]*=[^\r\n]*'
    if re.search(pattern, original):
        updated = re.sub(pattern, lambda _: setting, original)
    else:
        updated = original + (newline if original and not original.endswith(b'\n') else b'') + setting + newline
    if updated != original:
        args.config.write_bytes(updated)
