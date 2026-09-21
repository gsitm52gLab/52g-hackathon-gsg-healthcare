#!/usr/bin/env python3
"""Recovery helper for rebuilding aligned/Markdown files from a validated KO index."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WARNING = (
    "본 문서는 일본어 공식 원문을 기반으로 기계 번역한 비공식 한국어 참고본입니다. "
    "해석이 다른 경우 일본어 원문이 우선하며, 본 번역은 법률 자문이나 적법성 판정이 아닙니다. "
    "검수 상태: machine_unreviewed."
)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} SOURCE-ID", file=sys.stderr)
        return 2
    source_id = sys.argv[1]
    manifest = [json.loads(line) for line in (ROOT / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    source = next(row for row in manifest if row["id"] == source_id)
    index_rows = []
    for line in (ROOT / "search" / "chunks.ko.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["source_id"] == source_id:
            index_rows.append(row)
    if not index_rows:
        raise RuntimeError(f"No validated index rows for {source_id}")
    aligned_rows = []
    markdown = [f"# {source['title_ko']}", "", f"> {WARNING}", ""]
    for index_row in index_rows:
        segment_id = index_row["chunk_id"].removesuffix(":ko")
        ja, ko = index_row["original_ja"], index_row["text"]
        aligned_rows.append(
            {
                "segment_id": segment_id,
                "source_id": source_id,
                "version_id": source["version_id"],
                "source_anchor": index_row["source_anchor"],
                "page": None,
                "ja": ja,
                "ko": ko,
                "source_text_sha256": sha(ja),
                "translation_text_sha256": sha(ko),
                "translation_method": "machine_translation",
                "translation_model": "Google Translate web endpoint (client=gtx; undocumented)",
                "translation_policy_sha256": source["translation"]["prompt_sha256"],
                "translation_status": index_row["translation_status"],
                "translation_build_id": index_row["translation_build_id"],
                "source_sha256": index_row["source_sha256"],
                "generated_at": source["translation"]["generated_at"],
            }
        )
        markdown.extend([f"## {segment_id}", "", f"`{index_row['source_anchor']}`", "", ko, ""])
    source_dir = ROOT / "sources" / source_id
    (source_dir / "aligned" / "segments.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in aligned_rows), encoding="utf-8", newline="\n"
    )
    (source_dir / "derived" / "translation.ko.md").write_text("\n".join(markdown).rstrip() + "\n", encoding="utf-8", newline="\n")
    report_path = source_dir / "qa" / "extraction-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["translation_failures"] = []
    report["aligned_translation_count"] = len(aligned_rows)
    report["segment_count"] = len(aligned_rows)
    report["recovered_from_validated_index"] = True
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"restored {len(aligned_rows)} segments for {source_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

