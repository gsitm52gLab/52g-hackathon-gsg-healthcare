#!/usr/bin/env python3
"""Small read-only loader for runtime regulatory context."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_jcia_rules() -> list[dict]:
    """Return validated team-authored rules; never JCIA full text."""
    return _jsonl(ROOT / "rules" / "jcia" / "rules.jsonl")


def load_search_corpus() -> dict[str, list[dict]]:
    """Load fixed translations and the JCIA Korean rule index for retrieval."""
    return {
        "ja": _jsonl(ROOT / "search" / "chunks.ja.jsonl"),
        "ko": _jsonl(ROOT / "search" / "chunks.ko.jsonl"),
        "jcia_rules_ko": _jsonl(ROOT / "search" / "rules.ko.jsonl"),
    }


if __name__ == "__main__":
    loaded = load_search_corpus()
    print(json.dumps({key: len(value) for key, value in loaded.items()}, ensure_ascii=False))
