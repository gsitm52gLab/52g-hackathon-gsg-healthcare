#!/usr/bin/env python3
"""Build lightweight JA/KO JSONL indexes only after translation-ready validation."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    subprocess.run([str(ROOT / "scripts" / "validate")], cwd=ROOT, check=True)
    rows = [json.loads(line) for line in (ROOT / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    ja_rows, ko_rows = [], []
    for source in rows:
        if source.get("corpus_status") != "active":
            continue
        if source.get("translation_ready") is not True:
            raise RuntimeError(f"{source['id']}: translation_ready is not true")
        segment_path = ROOT / source["aligned_segments_path"]
        for line in segment_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            segment = json.loads(line)
            common = {
                "source_id": source["id"],
                "version_id": source["version_id"],
                "authority_type": source["authority_type"],
                "title_ja": source["title_ja"],
                "title_ko": source["title_ko"],
                "source_anchor": segment["source_anchor"],
                "canonical_url": source["canonical_url"],
                "source_sha256": source["sha256"],
                "translation_build_id": segment["translation_build_id"],
                "translation_status": segment["translation_status"],
            }
            ja_rows.append({**common, "chunk_id": f"{segment['segment_id']}:ja", "language": "ja", "text": segment["ja"]})
            ko_rows.append({**common, "chunk_id": f"{segment['segment_id']}:ko", "language": "ko", "text": segment["ko"], "original_ja": segment["ja"]})
    output = ROOT / "search"
    output.mkdir(parents=True, exist_ok=True)
    (output / "chunks.ja.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in ja_rows), encoding="utf-8", newline="\n")
    (output / "chunks.ko.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in ko_rows), encoding="utf-8", newline="\n")
    rules = [json.loads(line) for line in (ROOT / "rules" / "jcia" / "rules.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    rule_rows = []
    for rule in rules:
        searchable_text = " ".join(
            [rule["title_ko"], *rule["trigger_concepts"], *rule["review_questions"],
             *rule["allowed_context"], *rule["risky_context"]]
        )
        rule_rows.append({
            "chunk_id": f"{rule['rule_id']}:ko",
            "language": "ko",
            "document_type": "jcia_practical_rule",
            "rule_id": rule["rule_id"],
            "risk_type": rule["risk_type"],
            "text": searchable_text,
            "rule": rule,
        })
    (output / "rules.ko.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in rule_rows), encoding="utf-8", newline="\n")
    print(json.dumps({"active_sources": len({r['source_id'] for r in ja_rows}), "ja_chunks": len(ja_rows), "ko_chunks": len(ko_rows), "jcia_rule_chunks": len(rule_rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
