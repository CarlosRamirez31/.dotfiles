#!/usr/bin/env python3
"""Validate a document against its SourceLedger and pre-humanized draft."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
HUMANIZER_VALIDATOR = SCRIPT_DIR.parents[2] / "writing" / "humanize-global" / "scripts"
if str(HUMANIZER_VALIDATOR) not in sys.path:
    sys.path.insert(0, str(HUMANIZER_VALIDATOR))
from validate_rewrite import compare  # type: ignore  # noqa: E402

from source_ledger import validate as validate_ledger  # noqa: E402
from validate_citations import citations, split_document  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--document", required=True, type=Path)
    parser.add_argument("--original", type=Path)
    args = parser.parse_args()
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    text = args.document.read_text(encoding="utf-8-sig")
    failures = validate_ledger(ledger)
    available = {str(source.get("citation_key", "")).casefold() for source in ledger.get("sources", []) if source.get("citation_key")}
    body, _ = split_document(text)
    for citation in citations(body):
        display = citation.replace("|", ", ")
        if citation.casefold() not in available:
            failures.append(f"La cita {display} no tiene citation_key correspondiente en SourceLedger")
    ids = {source.get("id") for source in ledger.get("sources", [])}
    for marker in re.findall(r"\[((?:LOCAL|WEB)-\d{3})\]", text):
        if marker not in ids:
            failures.append(f"Identificador de fuente ausente del ledger: {marker}")
    if args.original:
        failures.extend(compare(args.original.read_text(encoding="utf-8-sig"), text))
    if failures:
        print("FAIL:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
