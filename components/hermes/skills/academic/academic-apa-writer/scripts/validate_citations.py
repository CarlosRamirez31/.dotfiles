#!/usr/bin/env python3
"""Check author-year citations against Markdown references."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path


YEAR = r"(?:\d{4}|s\.\s*f\.)"


def key(author: str, year: str) -> str:
    first = re.split(r"\s+(?:&|y|et al\.)\s*|,", author.strip(), maxsplit=1)[0].strip("*_ .\t")
    return f"{first.casefold()}|{re.sub(r'\s+', '', year.casefold())}"


def split_document(text: str) -> tuple[str, str]:
    match = re.search(r"(?im)^#{1,6}\s+referencias\s*$", text)
    return (text[: match.start()], text[match.end() :]) if match else (text, "")


def citations(body: str) -> set[str]:
    # Las citas internas de una cita textual no exigen referencias propias.
    # Conserva la atribución externa al final de cada bloque Markdown.
    cleaned = []
    for line in body.splitlines():
        if line.lstrip().startswith("> "):
            attribution = re.search(rf"\(([^()\n]+?),\s*{YEAR}(?:,\s*(?:p|pp|párr)\.[^)]*)?\)\s*$", line, re.I)
            cleaned.append(attribution.group(0) if attribution else "")
        else:
            cleaned.append(line)
    body = "\n".join(cleaned)
    found: set[str] = set()
    for author, year in re.findall(rf"\b([A-ZÁÉÍÓÚÜÑ][\wÁÉÍÓÚÜÑáéíóúüñ-]+(?:\s+et al\.)?(?:\s+(?:&|y)\s+[A-ZÁÉÍÓÚÜÑ][\w-]+)?)\s*\(({YEAR})\)", body):
        found.add(key(author, year))
    for author, year in re.findall(rf"\(([^()\n;]{{2,100}}?),\s*({YEAR})(?:,\s*(?:p|pp|párr)\.[^)]*)?\)", body, re.I):
        found.add(key(author, year))
    return found


def references(section: str) -> tuple[set[str], list[str], list[str]]:
    keys: set[str] = set()
    raw_entries: list[str] = []
    malformed: list[str] = []
    for paragraph in re.split(r"\n\s*\n", section):
        entry = " ".join(line.strip() for line in paragraph.splitlines()).strip(" -*\t")
        if not entry:
            continue
        raw_entries.append(entry)
        match = re.match(rf"(.+?)\s*\(({YEAR})(?:,\s*[^)\n]+)?\)\.", entry, re.I)
        if not match:
            malformed.append(entry[:120])
            continue
        keys.add(key(match.group(1), match.group(2)))
    return keys, raw_entries, malformed


def validate(text: str) -> list[str]:
    body, section = split_document(text)
    cited = citations(body)
    referenced, raw_entries, malformed = references(section)
    failures = [f"Cita sin referencia: {item}" for item in sorted(cited - referenced)]
    failures.extend(f"Referencia no citada: {item}" for item in sorted(referenced - cited))
    failures.extend(f"Referencia con formato no reconocible: {item}" for item in malformed)
    duplicates = [entry for entry, count in Counter(re.sub(r"\s+", " ", item.casefold()) for item in raw_entries).items() if count > 1]
    failures.extend(f"Referencia duplicada: {entry[:120]}" for entry in duplicates)
    for entry in raw_entries:
        for doi in re.findall(r"(?:doi:\s*|https?://doi\.org/)(\S+)", entry, re.I):
            if not re.match(r"10\.\d{4,9}/\S+$", doi.rstrip("."), re.I):
                failures.append(f"DOI mal formado: {doi}")
        if re.search(r"https?://\s*$", entry):
            failures.append(f"URL vacía: {entry[:120]}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("document", type=Path)
    args = parser.parse_args()
    failures = validate(args.document.read_text(encoding="utf-8-sig"))
    if failures:
        print("FAIL:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
