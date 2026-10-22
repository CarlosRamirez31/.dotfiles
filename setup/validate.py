#!/usr/bin/env python3
"""Read-only validation of source syntax, data, managed files and local docs."""
import csv
import json
from pathlib import Path
import re
import subprocess
import sys
import tomllib

import yaml
from urllib.parse import unquote
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def repository_files():
    result = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '-z', '--cached', '--others', '--exclude-standard'])
    return sorted({ROOT / name.decode() for name in result.split(b'\0') if name and (ROOT / name.decode()).is_file()})


def validate():
    errors = []
    counts = {'Python': 0, 'TOML': 0, 'JSON/JSONC': 0, 'Markdown': 0, 'YAML': 0, 'XML/SVG': 0, 'DOCX': 0}
    for path in repository_files():
        relative = path.relative_to(ROOT)
        try:
            first_line = path.open('rb').readline(200)
            if path.suffix == '.py' or (first_line.startswith(b'#!') and b'python' in first_line):
                compile(path.read_bytes(), str(path), 'exec')
                counts['Python'] += 1
            elif path.suffix == '.toml':
                tomllib.loads(path.read_text())
                counts['TOML'] += 1
            elif path.suffix in ('.json', '.jsonc'):
                data = path.read_text()
                if path.suffix == '.jsonc':
                    data = re.sub(r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*.*?\*/',
                                  lambda m: m[0] if m[0].startswith('"') else ' ', data, flags=re.S)
                json.loads(data)
                counts['JSON/JSONC'] += 1
            elif path.suffix in ('.svg', '.xml'):
                ET.parse(path)
                counts['XML/SVG'] += 1
            elif path.suffix == '.docx':
                with zipfile.ZipFile(path) as archive:
                    if archive.testzip():
                        raise ValueError('Corrupt DOCX archive')
                counts['DOCX'] += 1
            elif path.suffix in ('.yaml', '.yml'):
                yaml.safe_load(path.read_text())
                counts['YAML'] += 1
            elif path.suffix == '.md':
                counts['Markdown'] += 1
                for link in re.findall(r'\]\(([^)\s]+)(?:\s+"[^"]*")?\)', path.read_text()):
                    if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', link) or link.startswith(('#', '/')):
                        continue
                    target = unquote(link.split('#')[0])
                    if target and not (path.parent / target).exists():
                        errors.append(f'{relative}: broken local link {link}')
        except (ValueError, SyntaxError, OSError, yaml.YAMLError, ET.ParseError, zipfile.BadZipFile) as error:
            errors.append(f'{relative}: {error}')
    destinations, sources = set(), set()
    with (ROOT / 'setup/links.tsv').open() as manifest:
        for number, row in enumerate(csv.reader(manifest, delimiter='\t'), 1):
            if not row or row[0].startswith('#'):
                continue
            if len(row) != 3:
                errors.append(f'links.tsv:{number}: expected three columns')
                continue
            module, source, target = row
            for value in (source, target):
                if not value or Path(value).is_absolute() or '..' in Path(value).parts or '.' in value.split('/'):
                    errors.append(f'links.tsv:{number}: invalid path {value!r}')
            if target in destinations:
                errors.append(f'links.tsv:{number}: duplicate destination {target}')
            destinations.add(target)
            sources.add(source)
            if not (ROOT / source).is_file():
                errors.append(f'links.tsv:{number}: missing source {source}')
            if not ((ROOT / f'setup/modules/{module}.sh').is_file() or
                    (ROOT / f'setup/modules/{module}/install.sh').is_file()):
                errors.append(f'links.tsv:{number}: missing installer for {module}')
    for folder in ('config', 'home', 'bin', 'libexec', 'share', 'assets', 'system/systemd/user'):
        for path in repository_files():
            relative = str(path.relative_to(ROOT))
            if relative.startswith(folder + '/') and relative not in sources:
                errors.append(f'{relative}: managed file absent from links.tsv')
    for name, count in counts.items():
        print(f'{name}: {count} files checked')
    print(f'Manifest: {len(destinations)} managed destinations checked')
    for error in errors:
        print(error, file=sys.stderr)
    return bool(errors)


if __name__ == '__main__':
    sys.exit(validate())
