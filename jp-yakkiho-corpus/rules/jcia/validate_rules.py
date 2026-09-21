#!/usr/bin/env python3
"""Strictly validate JCIA cards, evidence ownership, and release coverage."""

from __future__ import annotations

import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parent
CORPUS_ROOT = ROOT.parents[1]
RULES = ROOT / "rules.jsonl"
RULE_SCHEMA = ROOT / "rules.schema.json"
FINDING_SCHEMA = ROOT / "finding.schema.json"
RULESET = ROOT / "ruleset.yaml"
ALLOWLIST = ROOT / "locator-allowlist.json"
POLICY = "pre_screening_only_no_legality_or_approval_conclusion"


def read_utf8_nfc_lf(path: Path) -> str:
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="strict")
    try:
        label = path.relative_to(CORPUS_ROOT)
    except ValueError:
        label = path
    if b"\r" in raw:
        raise ValueError(f"{label}: CR/CRLF is not allowed")
    if text != unicodedata.normalize("NFC", text):
        raise ValueError(f"{label}: text is not Unicode NFC")
    return text


def load_rows(path: Path = RULES) -> list[dict]:
    rows = []
    for line_no, line in enumerate(read_utf8_nfc_lf(path).splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {line_no}: invalid JSON: {exc}") from exc
    return rows


def corpus_sources() -> tuple[dict[str, dict], dict[str, str]]:
    manifest: dict[str, dict] = {}
    owners: dict[str, str] = {}
    for line in read_utf8_nfc_lf(CORPUS_ROOT / "manifest.jsonl").splitlines():
        if not line.strip():
            continue
        source = json.loads(line)
        manifest[source["id"]] = source
        segment_path = CORPUS_ROOT / source["aligned_segments_path"]
        for segment_line in read_utf8_nfc_lf(segment_path).splitlines():
            if segment_line.strip():
                segment = json.loads(segment_line)
                anchor = segment.get("source_anchor")
                if anchor:
                    owners[anchor] = source["id"]
    return manifest, owners


def normalized_basis(items: list[dict]) -> list[dict]:
    keys = ("source_id", "locator", "source_anchor")
    return [{key: item[key] for key in keys} for item in items]


def validate(rows: list[dict]) -> list[str]:
    errors: list[str] = []
    manifest, anchor_owner = corpus_sources()
    rule_schema = json.loads(read_utf8_nfc_lf(RULE_SCHEMA))
    finding_schema = json.loads(read_utf8_nfc_lf(FINDING_SCHEMA))
    ruleset = yaml.safe_load(read_utf8_nfc_lf(RULESET))
    allowlist = json.loads(read_utf8_nfc_lf(ALLOWLIST))
    jsonschema.Draft202012Validator.check_schema(rule_schema)
    jsonschema.Draft202012Validator.check_schema(finding_schema)
    schema_validator = jsonschema.Draft202012Validator(rule_schema)

    jcia_sources = {source["source_document_id"]: source for source in ruleset["source_documents"]}
    ids = [row.get("rule_id") for row in rows]
    risks = [row.get("risk_type") for row in rows]
    for rule_id, count in Counter(ids).items():
        if count > 1:
            errors.append(f"duplicate rule_id: {rule_id}")
    for risk, count in Counter(risks).items():
        if count > 1:
            errors.append(f"duplicate risk_type: {risk}")

    expected_ids = {f"JCIA-R-{n:03d}" for n in range(1, allowlist["rule_count"] + 1)}
    if set(ids) != expected_ids:
        errors.append(f"coverage gate failed: expected {sorted(expected_ids)}, got {sorted(ids)}")
    if len(rows) != ruleset["rule_count"] or len(rows) != allowlist["rule_count"]:
        errors.append("rule count disagrees with ruleset/allowlist")

    for row in rows:
        rid = row.get("rule_id", "unknown")
        for issue in schema_validator.iter_errors(row):
            path = "/".join(map(str, issue.absolute_path)) or "$"
            errors.append(f"{rid}: schema {path}: {issue.message}")
        if row.get("output_policy") != POLICY:
            errors.append(f"{rid}: output policy changed")
        if any(key in row for key in ("conclusion", "legal_conclusion", "approval_status")):
            errors.append(f"{rid}: rule card must not contain a legal/approval conclusion")

        source = jcia_sources.get(row.get("source_document_id"))
        if not source:
            errors.append(f"{rid}: source missing from ruleset inventory")
        else:
            if row.get("official_url") != source["official_url"]:
                errors.append(f"{rid}: JCIA official URL mismatch")
            if row.get("version_status") != source["version_status"]:
                errors.append(f"{rid}: JCIA version status mismatch")

        expected = allowlist["rules"].get(rid)
        if not expected:
            errors.append(f"{rid}: absent from locator allowlist")
        else:
            if row.get("risk_type") != expected["risk_type"]:
                errors.append(f"{rid}: risk_type differs from coverage gate")
            if row.get("source_document_id") != expected["source_document_id"]:
                errors.append(f"{rid}: source differs from coverage gate")
            if normalized_basis(row.get("legal_basis", [])) != expected["legal_basis"]:
                errors.append(f"{rid}: legal source/locator/anchor is outside reviewed allowlist")
            if normalized_basis(row.get("supporting_guidance", [])) != expected["supporting_guidance"]:
                errors.append(f"{rid}: JCIA section/page is outside reviewed allowlist")

        unresolved = not row.get("legal_basis")
        for basis in row.get("legal_basis", []) + row.get("supporting_guidance", []):
            is_unresolved = basis.get("exact_basis_unresolved") is True
            unresolved = unresolved or is_unresolved
            if is_unresolved:
                if basis.get("locator") is not None or basis.get("source_anchor") is not None:
                    errors.append(f"{rid}: unresolved basis must not invent locator/anchor")
                continue
            source_id = basis.get("source_id")
            anchor = basis.get("source_anchor")
            if source_id in manifest:
                owner = anchor_owner.get(anchor)
                if owner != source_id:
                    errors.append(f"{rid}: anchor ownership mismatch: {source_id} != {owner}: {anchor}")
                source_meta = manifest[source_id]
                if basis.get("official_url") != source_meta["canonical_url"]:
                    errors.append(f"{rid}: manifest URL mismatch for {source_id}")
                expected_date = source_meta.get("effective_at") or source_meta.get("published_at")
                if basis.get("effective_or_version_date") != expected_date:
                    errors.append(f"{rid}: manifest version date mismatch for {source_id}")
            elif source_id in jcia_sources:
                meta = jcia_sources[source_id]
                if basis.get("official_url") != meta["official_url"]:
                    errors.append(f"{rid}: JCIA guidance URL mismatch for {source_id}")
                if basis.get("effective_or_version_date") != meta["published_at"]:
                    errors.append(f"{rid}: JCIA guidance version mismatch for {source_id}")
            else:
                errors.append(f"{rid}: basis source not inventoried: {source_id}")
        if row.get("exact_basis_unresolved") != unresolved:
            errors.append(f"{rid}: top-level unresolved flag disagrees with basis")
        if unresolved and "상향" not in row.get("escalation", ""):
            errors.append(f"{rid}: unresolved basis requires expert escalation")

        for key in ("trigger_concepts", "review_questions", "allowed_context", "risky_context", "required_evidence"):
            for value in row.get(key, []):
                if len(value) > 300:
                    errors.append(f"{rid}: possible long source reproduction in {key}")

    conclusion = finding_schema["properties"]["conclusion"].get("const")
    if conclusion != "관련 조항과 충돌 가능성이 있는 문제 후보":
        errors.append("finding schema conclusion is not the required non-determinative phrase")
    if "담당자 검토 완료" in finding_schema["properties"]["ai_status"].get("enum", []):
        errors.append("human-only completion state leaked into ai_status")
    return errors


def main() -> int:
    try:
        rows = load_rows()
        errors = validate(rows)
    except (UnicodeError, ValueError, json.JSONDecodeError, yaml.YAMLError, jsonschema.SchemaError) as exc:
        rows, errors = [], [str(exc)]
    report = {
        "ok": not errors,
        "rule_count": len(rows),
        "source_counts": dict(Counter(row["source_document_id"] for row in rows)),
        "unresolved_rule_count": sum(bool(row["exact_basis_unresolved"]) for row in rows),
        "errors": errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
