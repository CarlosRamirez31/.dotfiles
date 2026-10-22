#!/usr/bin/env python3
"""Route research to local documents first and expose a testable web fallback."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

from local_research import search_local_documents


WebSearch = Callable[[str], list[dict[str, Any]]]


def research(
    query: str,
    *,
    top_k: int = 6,
    sources_dir: Path | None = None,
    cache_path: Path | None = None,
    web_search: WebSearch | None = None,
) -> dict[str, Any]:
    local = search_local_documents(query, top_k, sources_dir, cache_path)
    if local["assessment"]["local_sufficient"]:
        return {"route": "local", "web_search_count": 0, "local": local, "web": []}
    if web_search is None:
        return {
            "route": "web_required",
            "web_search_count": 0,
            "local": local,
            "web": [],
            "missing": local["assessment"]["missing"],
        }
    web_results = web_search(query)
    return {"route": "web", "web_search_count": 1, "local": local, "web": web_results}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=6)
    parser.add_argument("--sources", type=Path)
    parser.add_argument("--cache", type=Path)
    args = parser.parse_args()
    result = research(
        args.query,
        top_k=args.top_k,
        sources_dir=args.sources,
        cache_path=args.cache,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
