#!/usr/bin/env python3
"""Health check for Hermes Academic Writer."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

from ruamel.yaml import YAML

from local_research import hermes_home, load_index


GUIDE_SHA256 = "5A5976C29E808C6B4666885DAD15E10E7F242EB03DD423D7F1B79EB1ECC1A0B8"
UNICARIBE_GUIDE_SHA256 = "8FA65AF422FC477BC256E76B60C8435B9FDF84B4203E1B96DBB21427428DC18A"


def check(label: str, ok: bool, fix: str = "") -> bool:
    print(f"[{'OK' if ok else 'FAIL'}] {label}" + (f" - {fix}" if not ok and fix else ""))
    return ok


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, default=hermes_home())
    args = parser.parse_args()
    home = args.home.resolve()
    skill = home / "skills" / "academic" / "academic-apa-writer"
    humanizer = home / "skills" / "writing" / "humanize-global"
    results = []
    hermes_bin = home / "bin" / ("hermes.exe" if os.name == "nt" else "hermes")
    results.append(check("Hermes", hermes_bin.exists(), f"Instala Hermes en {home}"))
    results.append(check("humanize-global", (humanizer / "SKILL.md").exists(), "Ejecuta install_academic_writer.ps1"))
    results.append(check("academic-apa-writer", (skill / "SKILL.md").exists(), "Ejecuta install_academic_writer.ps1"))
    sources = home / "academic" / "sources"
    cache = home / "academic" / "cache" / "local_index.json"
    try:
        index = load_index(sources, cache)
        rag_ok = not index.get("errors")
    except Exception as exc:
        rag_ok = False
        index = {"errors": [str(exc)]}
    results.append(check("local RAG", rag_ok, json.dumps(index.get("errors"), ensure_ascii=False)))
    config = home / "config.yaml"
    web_ready = False
    if config.exists():
        try:
            parsed = YAML(typ="safe").load(config.read_text(encoding="utf-8-sig")) or {}
            cli_toolsets = (parsed.get("platform_toolsets") or {}).get("cli") or []
            web_ready = "web" in cli_toolsets
        except Exception:
            web_ready = False
    results.append(check("web tools", web_ready, "Ejecuta hermes tools y habilita web"))
    results.append(check("python-docx", importlib.util.find_spec("docx") is not None, "Instala requirements-academic.txt"))
    results.append(check("APA reference", (skill / "references" / "apa7_reference.txt").exists()))
    guide_pdf = skill / "references" / "Guia-Normas-APA-7ma-edicion.pdf"
    guide_text = skill / "references" / "Guia-Normas-APA-7ma-edicion.txt"
    guide_hash = hashlib.sha256(guide_pdf.read_bytes()).hexdigest().upper() if guide_pdf.exists() else ""
    results.append(check("user APA guide PDF", guide_hash == GUIDE_SHA256, "Restaura la copia íntegra aportada por el usuario"))
    text_complete = guide_text.exists() and "=== PAGE 57 ===" in guide_text.read_text(encoding="utf-8", errors="replace")
    results.append(check("user APA guide text", text_complete, "Regenera la extracción completa de 57 páginas"))
    unicaribe_pdf = skill / "references" / "Normas-APA-7ma-Edicion-UNICARIBE.pdf"
    unicaribe_text = skill / "references" / "Normas-APA-7ma-Edicion-UNICARIBE.txt"
    unicaribe_hash = hashlib.sha256(unicaribe_pdf.read_bytes()).hexdigest().upper() if unicaribe_pdf.exists() else ""
    results.append(check("UNICARIBE APA guide PDF", unicaribe_hash == UNICARIBE_GUIDE_SHA256, "Restaura la copia íntegra de UNICARIBE"))
    unicaribe_text_complete = unicaribe_text.exists() and "=== PAGE 12 ===" in unicaribe_text.read_text(encoding="utf-8", errors="replace")
    results.append(check("UNICARIBE APA guide text", unicaribe_text_complete, "Regenera la extracción completa de 12 páginas"))
    results.append(check("UNICARIBE format profile", (skill / "references" / "UNICARIBE_FORMAT_PROFILE.md").exists()))
    template = skill / "templates" / "apa7_template.docx"
    results.append(check("Word template", template.exists() and template.stat().st_size > 0))
    output = home / "academic" / "output"
    writable = output.exists() and os.access(output, os.W_OK)
    results.append(check("output directory", writable, f"Crea {output}"))
    results.append(check("source validator", (skill / "scripts" / "validate_sources.py").exists()))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
