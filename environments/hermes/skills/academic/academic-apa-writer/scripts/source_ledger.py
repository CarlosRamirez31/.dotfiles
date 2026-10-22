#!/usr/bin/env python3
"""Create and validate a SourceLedger without inventing metadata."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED = {"type", "title", "supports"}


def load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"generated_at": datetime.now(timezone.utc).isoformat(), "sources": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("sources"), list):
        raise ValueError("El ledger debe contener una lista sources")
    return data


def save(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for position, source in enumerate(data.get("sources", []), 1):
        missing = [field for field in REQUIRED if not source.get(field)]
        if missing:
            errors.append(f"Fuente {position}: faltan {', '.join(sorted(missing))}")
        source_id = source.get("id")
        if not source_id:
            errors.append(f"Fuente {position}: falta id")
        elif source_id in seen:
            errors.append(f"ID duplicado: {source_id}")
        else:
            seen.add(source_id)
        source_type = source.get("type")
        if source_type not in {"local", "web"}:
            errors.append(f"Fuente {source_id or position}: type debe ser local o web")
        if source_type == "local" and not (source.get("path") or source.get("locator")):
            errors.append(f"Fuente {source_id or position}: falta path o locator")
        if source_type == "web" and not source.get("url"):
            errors.append(f"Fuente {source_id or position}: falta URL")
        doi = source.get("doi")
        if doi and not re.match(r"^(?:https://doi\.org/)?10\.\d{4,9}/\S+$", doi, re.I):
            errors.append(f"Fuente {source_id or position}: DOI inválido")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    init_cmd = sub.add_parser("init")
    init_cmd.add_argument("ledger", type=Path)
    add_cmd = sub.add_parser("add")
    add_cmd.add_argument("ledger", type=Path)
    add_cmd.add_argument("--type", choices=["local", "web"], required=True)
    add_cmd.add_argument("--title", required=True)
    add_cmd.add_argument("--supports", action="append", required=True)
    add_cmd.add_argument("--author")
    add_cmd.add_argument("--year")
    add_cmd.add_argument("--url")
    add_cmd.add_argument("--doi")
    add_cmd.add_argument("--path")
    add_cmd.add_argument("--locator")
    add_cmd.add_argument("--citation-key")
    validate_cmd = sub.add_parser("validate")
    validate_cmd.add_argument("ledger", type=Path)
    args = parser.parse_args()
    if args.command == "init":
        save(args.ledger, {"generated_at": datetime.now(timezone.utc).isoformat(), "sources": []})
        print(args.ledger)
        return 0
    data = load(args.ledger)
    if args.command == "add":
        prefix = "LOCAL" if args.type == "local" else "WEB"
        existing = [source for source in data["sources"] if str(source.get("id", "")).startswith(prefix + "-")]
        source: dict[str, Any] = {
            "id": f"{prefix}-{len(existing) + 1:03d}", "type": args.type, "title": args.title,
            "supports": args.supports,
        }
        for key in ("author", "year", "url", "doi", "path", "locator", "citation_key"):
            value = getattr(args, key)
            if value:
                source[key] = value
        data["sources"].append(source)
        save(args.ledger, data)
        print(json.dumps(source, ensure_ascii=False, indent=2))
        return 0
    errors = validate(data)
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
