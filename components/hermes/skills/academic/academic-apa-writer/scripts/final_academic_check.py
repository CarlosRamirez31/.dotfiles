#!/usr/bin/env python3
"""Run the deterministic checks required before academic export."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(label: str, command: list[str]) -> tuple[str, bool, str]:
    process = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    output = (process.stdout + process.stderr).strip()
    return label, process.returncode == 0, output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--document", required=True, type=Path, help="Markdown final")
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--original", type=Path)
    parser.add_argument("--docx", type=Path)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    checks = [
        run("fuentes", [sys.executable, str(here / "validate_sources.py"), "--ledger", str(args.ledger), "--document", str(args.document)] + (["--original", str(args.original)] if args.original else [])),
        run("citas", [sys.executable, str(here / "validate_citations.py"), str(args.document)]),
        run("ledger", [sys.executable, str(here / "source_ledger.py"), "validate", str(args.ledger)]),
    ]
    if args.docx:
        checks.append(run("apa", [sys.executable, str(here / "validate_apa.py"), str(args.docx)]))
    failed = False
    for label, ok, output in checks:
        print(f"[{'OK' if ok else 'FAIL'}] {label}")
        if not ok:
            failed = True
            print(output)
    print("FINAL" if not failed else "NOT FINAL")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
