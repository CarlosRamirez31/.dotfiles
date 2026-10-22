#!/usr/bin/env python3
"""Materialize selected managed files in the dev container's private home."""
import argparse
import csv
import datetime
import os
from pathlib import Path
import shutil
import tempfile


def copy_components(repo, home, modules):
    home = home.resolve()
    selected = []
    with (repo / 'setup/links.tsv').open() as stream:
        for row in csv.reader(stream, delimiter='\t'):
            if not row or row[0].startswith('#') or row[0] not in modules:
                continue
            _, relative, destination = row
            source, target = repo / relative, home / destination
            if not source.is_file() or Path(destination).is_absolute() or '..' in Path(destination).parts:
                raise ValueError(f'Invalid managed destination: {destination}')
            if not target.parent.resolve().is_relative_to(home):
                raise ValueError(f'Destination leaves the private home: {target}')
            selected.append((source, target))
    for source, target in selected:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_file() and not target.is_symlink() and target.read_bytes() == source.read_bytes():
            target.chmod(source.stat().st_mode & 0o777)
            continue
        if target.exists() or target.is_symlink():
            stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
            target.rename(target.with_name(target.name + '.backup.' + stamp))
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
        try:
            shutil.copy2(source, temporary)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('modules', nargs='+')
    args = parser.parse_args()
    if os.environ.get('CONTAINER_ID') != 'dev' or not Path('/run/.containerenv').exists():
        parser.error('Run only inside the dev container.')
    copy_components(Path(__file__).resolve().parents[1], Path.home(), set(args.modules))


if __name__ == '__main__':
    main()
