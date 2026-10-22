#!/usr/bin/env python3
"""Preview or repair only existing links into the old repository layout."""
import argparse
import csv
import json
import os
from pathlib import Path
import tempfile


def legacy_paths(source):
    mapping = {}
    with (source / 'setup/links.tsv').open() as stream:
        for row in csv.reader(stream, delimiter='\t'):
            if not row or row[0].startswith('#'):
                continue
            module, current, destination = row
            mapping[f'components/{module}/dotfiles/{destination}'] = current
    # Include directory links only when every descendant keeps its suffix.
    candidates = {str(parent) for old in mapping for parent in Path(old).parents if str(parent) != '.'}
    for directory in candidates:
        prefix = directory + '/'
        translated = set()
        for old, new in list(mapping.items()):
            if old.startswith(prefix):
                suffix = old[len(directory):]
                translated.add(new[:-len(suffix)] if new.endswith(suffix) else None)
        if len(translated) == 1 and None not in translated:
            mapping[directory] = translated.pop()
    return mapping


def plan(home, repo, source):
    paths = legacy_paths(source)
    candidates = set()
    with (source / 'setup/links.tsv').open() as stream:
        for row in csv.reader(stream, delimiter='\t'):
            if not row or row[0].startswith('#'):
                continue
            target = home / row[2]
            candidates.add(target)
            candidates.update(p for p in target.parents if p != home and p.is_relative_to(home))
    units = home / '.config/systemd/user'
    if units.is_dir():
        candidates.update(p for p in units.rglob('*') if p.is_symlink())
    result = []
    # Directory links are replaced first; their children then already resolve.
    for target in sorted(candidates, key=lambda p: (len(p.parts), str(p))):
        if not target.is_symlink():
            continue
        old_link = os.readlink(target)
        old = Path(os.path.normpath(target.parent / old_link))
        if not old.is_relative_to(repo):
            continue
        relative = str(old.relative_to(repo))
        if relative not in paths:
            continue
        new = repo / paths[relative]
        if not (source / paths[relative]).exists():
            raise RuntimeError(f'Missing source for {target}: {new}')
        result.append({'target': str(target), 'before': old_link, 'after': str(new)})
    return result


def apply(changes):
    completed = []
    try:
        for entry in changes:
            target = Path(entry['target'])
            if not target.is_symlink() or os.readlink(target) != entry['before']:
                raise RuntimeError(f'Link changed since preview: {target}')
            # Replace each link atomically; never overwrite an ordinary file.
            with tempfile.TemporaryDirectory(prefix='.dotfiles-link-', dir=target.parent) as directory:
                temporary = Path(directory) / 'link'
                temporary.symlink_to(entry['after'])
                temporary.replace(target)
            completed.append(entry)
    except Exception:
        for entry in reversed(completed):
            target = Path(entry['target'])
            if target.is_symlink() and os.readlink(target) == entry['after']:
                target.unlink()
                target.symlink_to(entry['before'])
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, default=Path.home())
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--source', type=Path, help='New source tree for a preview before switching branches')
    parser.add_argument('--restore', type=Path, help='Restore targets from a saved migration log')
    parser.add_argument('--apply', action='store_true', help='Apply the preview; default is read-only')
    parser.add_argument('--log', type=Path, help='Save the exact before/after link targets')
    args = parser.parse_args()
    repo = args.repo.absolute()
    source = (args.source or repo).absolute()
    if args.apply and source != repo:
        parser.error('--source is only supported for previews')
    if args.restore:
        changes = [{'target': row['target'], 'before': row['after'], 'after': row['before']}
                   for row in json.loads(args.restore.read_text())]
    else:
        changes = plan(args.home.absolute(), repo, source)
    for entry in changes:
        print(f"{entry['target']} -> {entry['after']}")
    if args.log:
        args.log.write_text(json.dumps(changes, indent=2) + '\n')
    if args.apply:
        apply(changes)
    print(f"{'Updated' if args.apply else 'Would update'} {len(changes)} existing links.")


if __name__ == '__main__':
    main()
