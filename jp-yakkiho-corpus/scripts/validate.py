#!/usr/bin/env python3
"""Validate hashes, Unicode normalization, extraction artifacts, and alignment."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.jsonl"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> int:
    errors = []
    results = []
    rows = [json.loads(line) for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()]
    for row in rows:
        source_errors = []
        original = ROOT / row["original_path"]
        required = [
            original,
            ROOT / "sources" / row["id"] / "derived" / "original.ja.txt",
            ROOT / "sources" / row["id"] / "derived" / "translation.ko.md",
            ROOT / "sources" / row["id"] / "aligned" / "segments.jsonl",
            ROOT / "sources" / row["id"] / "qa" / "extraction-report.json",
        ]
        for path in required:
            if not path.exists():
                source_errors.append(f"missing: {path.relative_to(ROOT)}")
        if original.exists() and digest(original) != row["sha256"]:
            source_errors.append("original sha256 mismatch")

        for path in required[1:3]:
            if path.exists():
                text = path.read_text(encoding="utf-8")
                if text != unicodedata.normalize("NFC", text):
                    source_errors.append(f"not NFC: {path.relative_to(ROOT)}")

        segment_path = required[3]
        ids = set()
        segment_count = 0
        if segment_path.exists():
            for line_no, line in enumerate(segment_path.read_text(encoding="utf-8").splitlines(), start=1):
                if not line.strip():
                    continue
                segment = json.loads(line)
                segment_count += 1
                if segment["segment_id"] in ids:
                    source_errors.append(f"duplicate segment id at line {line_no}")
                ids.add(segment["segment_id"])
                if segment["source_id"] != row["id"]:
                    source_errors.append(f"wrong source id at line {line_no}")
                if not segment["ja"].strip() or not segment["ko"].strip():
                    source_errors.append(f"blank aligned text at line {line_no}")
                if segment["ko"] == "[MACHINE_TRANSLATION_FAILED]":
                    source_errors.append(f"translation failed: {segment['segment_id']}")
                if segment.get("translation_status") not in {"machine_unreviewed", "human_reviewed", "legal_reviewed"}:
                    source_errors.append(f"invalid translation status: {segment['segment_id']}")
                if segment.get("source_sha256") != row["sha256"]:
                    source_errors.append(f"stale translation source hash: {segment['segment_id']}")
                expected_build_id = f"ko-draft-v1-{row['sha256'][:12]}"
                if segment.get("translation_build_id") != expected_build_id:
                    source_errors.append(f"stale translation build: {segment['segment_id']}")
                if segment["ja"] != unicodedata.normalize("NFC", segment["ja"]):
                    source_errors.append(f"JA not NFC: {segment['segment_id']}")
                if segment["ko"] != unicodedata.normalize("NFC", segment["ko"]):
                    source_errors.append(f"KO not NFC: {segment['segment_id']}")
        if not row.get("metadata_only") and segment_count == 0:
            source_errors.append("no aligned segments")
        if not row.get("metadata_only"):
            if row.get("translation_ready") is not True:
                source_errors.append("translation_ready gate is false or missing")
            translation = row.get("translation") or {}
            if translation.get("source_sha256") != row["sha256"]:
                source_errors.append("manifest translation source hash is stale")
            if translation.get("failure_count") != 0:
                source_errors.append("manifest records translation failures")

        results.append({"source_id": row["id"], "ok": not source_errors, "segment_count": segment_count, "errors": source_errors})
        errors.extend(f"{row['id']}: {error}" for error in source_errors)

    rules_command = [sys.executable, str(ROOT / "rules" / "jcia" / "validate_rules.py")]
    rules_process = subprocess.run(rules_command, cwd=ROOT, capture_output=True, text=True, check=False)
    try:
        rules_report = json.loads(rules_process.stdout)
    except json.JSONDecodeError:
        rules_report = {"ok": False, "errors": [rules_process.stderr or rules_process.stdout or "no validator output"]}
    if rules_process.returncode != 0 or not rules_report.get("ok"):
        errors.extend(f"JCIA rules: {error}" for error in rules_report.get("errors", ["validation failed"]))

    report = {
        "validated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "source_count": len(rows),
        "ok": not errors,
        "errors": errors,
        "sources": results,
        "jcia_rules": rules_report,
    }
    report_path = ROOT / "qa" / "validation-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
