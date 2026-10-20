#!/usr/bin/env python3
"""Validate that a prose rewrite preserves protected content."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path


PATTERNS = [
    r"```[\s\S]*?```",
    r"`[^`\n]+`",
    r"https?://[^\s)>\]}]+",
    r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b",
    r"\b\d{1,2}\s+de\s+[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+\s+de\s+\d{4}\b",
    r"\b\d{4}-\d{2}-\d{2}\b",
    r"\b\d+(?:[.,]\d+)?\s*%",
    r"(?<![\w])[-+]?\d+(?:[.,]\d+)*(?![\w])",
    r'"[^"\n]+"',
    r"“[^”\n]+”",
]


def protected_items(text: str) -> list[str]:
    items: list[str] = []
    for pattern in PATTERNS:
        items.extend(match.group(0) for match in re.finditer(pattern, text, re.IGNORECASE))
    return items


def compare(original: str, rewritten: str) -> list[str]:
    expected = Counter(protected_items(original))
    actual = Counter(protected_items(rewritten))
    failures: list[str] = []
    for value, count in expected.items():
        if actual[value] < count:
            failures.append(f"Elemento protegido ausente o modificado: {value}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("original", type=Path)
    parser.add_argument("rewritten", type=Path)
    args = parser.parse_args()
    failures = compare(
        args.original.read_text(encoding="utf-8-sig"),
        args.rewritten.read_text(encoding="utf-8-sig"),
    )
    if failures:
        print("FAIL:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
