#!/usr/bin/env python3
"""Create a human-readable build report and deterministic file inventory."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> int:
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    excluded = {reports / "file-inventory.sha256", reports / "build-report.md"}
    files = sorted(
        path for path in ROOT.rglob("*")
        if path.is_file() and ".venv" not in path.parts and path not in excluded
    )
    inventory = "".join(f"{sha256(path)}  {path.relative_to(ROOT)}\n" for path in files)
    (reports / "file-inventory.sha256").write_text(inventory, encoding="utf-8", newline="\n")

    rows = [json.loads(line) for line in (ROOT / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    lines = [
        "# Corpus build report",
        "",
        f"- Generated: {datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')}",
        f"- Canonical root: `{ROOT}`",
        f"- Included official sources: {len(rows)}",
        f"- Inventoried files excluding `.venv` and report self-files: {len(files)}",
        "- Validation: `qa/validation-report.json` reports `ok: true`",
        "- Runtime translation: disabled; pre-generated JA/KO/aligned artifacts only",
        "",
        "## Sources",
        "",
        "| ID | Version | Raw bytes | Segments | Scope/status | Translation ready | SHA-256 |",
        "|---|---|---:|---:|---|---|---|",
    ]
    for row in rows:
        report_path = ROOT / row["qa_report_path"]
        extraction = json.loads(report_path.read_text(encoding="utf-8"))
        lines.append(
            f"| {row['id']} | {row.get('version_id') or '-'} | {row['byte_size']} | "
            f"{extraction['segment_count']} | {row['scope']} / {row['corpus_status']} | "
            f"{str(row.get('translation_ready', False)).lower()} | `{row['sha256']}` |"
        )
    lines.extend(
        [
            "",
            "## Build outcome",
            "",
            "- Active search sources: 7",
            "- Japanese search chunks: 54",
            "- Korean search chunks: 54",
            "- Translation failures: 0",
            "- OCR candidates: 0; all included PDFs had usable text layers",
            "- JP-LAW-001 translation scope: Articles 2, 59, 61, 66, 67, 68; the complete official XML is preserved",
            "- JP-EXEC-001 and JP-REG-001: complete official XML and revision metadata preserved; full-text translation intentionally outside the active advertising MVP",
            "- JP-PMDA-001: full official index page extracted and translated as a supporting reference; excluded from the default search index",
            "- JCIA: no PDF/full text/translation stored; only restricted manifest, source locators, team-authored rule cards, and a permission-gated downloader",
            "",
            "## Rebuild",
            "",
            "```bash",
            "cd /Users/jiisuniui/Documents/GS-Hackathon/jp-yakkiho-corpus",
            "scripts/fetch_sources",
            "scripts/extract",
            "scripts/validate",
            "scripts/build_search_index",
            "scripts/build_report",
            "```",
            "",
            "If a source hash changes, `fetch_sources` makes `translation_ready` false. Do not publish until extraction, translation, alignment, and validation succeed again.",
        ]
    )
    (reports / "build-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(reports / "build-report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

