#!/usr/bin/env python3
"""Extract UTF-8 NFC Japanese text, translate to Korean, and align segments."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader
from pypdf import __version__ as pypdf_version

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.jsonl"
TRANSLATION_WARNING = (
    "본 문서는 일본어 공식 원문을 기반으로 기계 번역한 비공식 한국어 참고본입니다. "
    "해석이 다른 경우 일본어 원문이 우선하며, 본 번역은 법률 자문이나 적법성 판정이 아닙니다. "
    "검수 상태: machine_unreviewed."
)
TRANSLATION_POLICY = (
    "Translate Japanese legal and regulatory text to Korean without changing article numbers, "
    "notice numbers, dates, figures, or citations. Preserve ambiguity and do not add a legal conclusion."
)
TRANSLATION_POLICY_SHA = hashlib.sha256(TRANSLATION_POLICY.encode()).hexdigest()
TRANSLATION_BUILD_ID = "ko-draft-v1"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
    text = text.replace("\u00ad", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_manifest() -> list[dict]:
    return [json.loads(line) for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()]


def split_text(text: str, limit: int = 1800) -> list[str]:
    text = normalize(text)
    if len(text) <= limit:
        return [text] if text else []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    chunks, current = [], ""
    for line in lines:
        pieces = [line[i : i + limit] for i in range(0, len(line), limit)]
        for piece in pieces:
            if current and len(current) + 1 + len(piece) > limit:
                chunks.append(current)
                current = piece
            else:
                current = f"{current}\n{piece}".strip()
    if current:
        chunks.append(current)
    return chunks


def xml_segments(row: dict, data: bytes) -> list[dict]:
    if row.get("metadata_only"):
        return []
    root = ET.fromstring(data)
    targets = set(row.get("target_articles", []))
    segments = []
    main_provision = root.find("./LawBody/MainProvision")
    if main_provision is None:
        raise RuntimeError(f"{row['id']}: MainProvision not found")
    for article in main_provision.iter("Article"):
        number = article.attrib.get("Num")
        if number not in targets:
            continue
        text = normalize("".join(article.itertext()))
        anchor = f"{row['id']}@{row['version_id']}#Article-{number}"
        segments.append(
            {
                "segment_id": f"{row['id']}-article-{int(number):03d}",
                "source_anchor": anchor,
                "page": None,
                "ja": text,
            }
        )
    missing = targets - {s["segment_id"].split("-")[-1].lstrip("0") for s in segments}
    if missing:
        raise RuntimeError(f"{row['id']}: missing requested articles {sorted(missing)}")
    return segments


def pdf_segments(row: dict, path: Path) -> tuple[list[dict], dict]:
    reader = PdfReader(path)
    segments = []
    empty_pages = []
    low_text_pages = []
    page_counts = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = normalize(page.extract_text() or "")
        page_counts.append(len(text.replace(" ", "").replace("\n", "")))
        if not text:
            empty_pages.append(page_number)
        elif page_counts[-1] < 100:
            low_text_pages.append(page_number)
        for part_number, part in enumerate(split_text(text), start=1):
            segment_id = f"{row['id']}-p{page_number:03d}-s{part_number:03d}"
            segments.append(
                {
                    "segment_id": segment_id,
                    "source_anchor": f"{row['id']}@{row['version_id']}#page={page_number:03d}&segment={part_number:03d}",
                    "page": page_number,
                    "ja": part,
                }
            )
    report = {
        "page_count": len(reader.pages),
        "page_nonspace_character_counts": page_counts,
        "empty_pages": empty_pages,
        "low_text_pages": low_text_pages,
        "ocr_used": False,
        "ocr_candidates": sorted(set(empty_pages + low_text_pages)),
    }
    return segments, report


def html_segments(row: dict, data: bytes) -> list[dict]:
    soup = BeautifulSoup(data, "html.parser")
    for element in soup(["script", "style", "nav", "header", "footer"]):
        element.decompose()
    text = normalize(soup.get_text("\n"))
    marker = "○化粧品における特定成分の特記表示について"
    start = text.find(marker)
    if start >= 0:
        text = text[start:]
    segments = []
    for part_number, part in enumerate(split_text(text), start=1):
        segments.append(
            {
                "segment_id": f"{row['id']}-html-s{part_number:03d}",
                "source_anchor": f"{row['id']}@{row['version_id']}#html-segment={part_number:03d}",
                "page": None,
                "ja": part,
            }
        )
    return segments


def translate_ja_ko(text: str) -> str:
    endpoint = "https://translate.googleapis.com/translate_a/single"
    payload = urllib.parse.urlencode(
        {"client": "gtx", "sl": "ja", "tl": "ko", "dt": "t", "q": text}
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"User-Agent": "GSG-jp-yakki-corpus/1.0", "Content-Type": "application/x-www-form-urlencoded"},
    )
    last_error = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                result = json.loads(response.read().decode("utf-8"))
            translated = "".join(item[0] for item in result[0] if item and item[0])
            if translated.strip():
                return normalize(translated)
        except Exception as exc:  # recorded by caller
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"translation failed: {last_error}")


def write_outputs(row: dict, segments: list[dict], base_report: dict) -> dict:
    source_dir = ROOT / "sources" / row["id"]
    derived = source_dir / "derived"
    aligned = source_dir / "aligned"
    qa = source_dir / "qa"
    derived.mkdir(parents=True, exist_ok=True)
    aligned.mkdir(parents=True, exist_ok=True)
    qa.mkdir(parents=True, exist_ok=True)

    if row.get("metadata_only"):
        ja_text = (
            f"[[{row['id']}#metadata-only]]\n{row['title_ja']}\n"
            "本コーパスではメタデータと公式XML原本のみ保存し、本文抽出・翻訳は対象外とする。\n"
        )
        ko_md = f"# {row['title_ko']}\n\n> {TRANSLATION_WARNING}\n\n현재 버전은 메타데이터와 공식 XML 원본만 보존하며 전문 번역은 범위에서 제외했습니다.\n"
        aligned_rows = []
        failures = []
    else:
        ja_parts = []
        ko_parts = [f"# {row['title_ko']}", "", f"> {TRANSLATION_WARNING}", ""]
        aligned_rows = []
        failures = []
        for index, segment in enumerate(segments, start=1):
            ja_parts.extend([f"[[{segment['source_anchor']}]]", segment["ja"], ""])
            try:
                ko = translate_ja_ko(segment["ja"])
            except Exception as exc:
                ko = "[MACHINE_TRANSLATION_FAILED]"
                failures.append({"segment_id": segment["segment_id"], "error": str(exc)})
            ko_parts.extend([f"## {segment['segment_id']}", "", f"`{segment['source_anchor']}`", "", ko, ""])
            aligned_rows.append(
                {
                    "segment_id": segment["segment_id"],
                    "source_id": row["id"],
                    "version_id": row["version_id"],
                    "source_anchor": segment["source_anchor"],
                    "page": segment["page"],
                    "ja": segment["ja"],
                    "ko": ko,
                    "source_text_sha256": sha_text(segment["ja"]),
                    "translation_text_sha256": sha_text(ko),
                    "translation_method": "machine_translation",
                    "translation_model": "Google Translate web endpoint (client=gtx; undocumented)",
                    "translation_policy_sha256": TRANSLATION_POLICY_SHA,
                    "translation_status": "machine_unreviewed",
                    "translation_build_id": f"{TRANSLATION_BUILD_ID}-{row['sha256'][:12]}",
                    "source_sha256": row["sha256"],
                    "generated_at": now_iso(),
                }
            )
            if index % 10 == 0:
                print(f"  translated {index}/{len(segments)}", flush=True)
            time.sleep(0.12)
        ja_text = "\n".join(ja_parts)
        ko_md = "\n".join(ko_parts)

    ja_text = normalize(ja_text) + "\n"
    ko_md = unicodedata.normalize("NFC", ko_md).rstrip() + "\n"
    (derived / "original.ja.txt").write_text(ja_text, encoding="utf-8", newline="\n")
    (derived / "translation.ko.md").write_text(ko_md, encoding="utf-8", newline="\n")
    aligned_text = "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in aligned_rows)
    (aligned / "segments.jsonl").write_text(unicodedata.normalize("NFC", aligned_text), encoding="utf-8", newline="\n")

    report = {
        "source_id": row["id"],
        "version_id": row["version_id"],
        "extracted_at": now_iso(),
        "extractor": "xml.etree.ElementTree" if row["source_format"] == "application/xml" else (f"pypdf {pypdf_version}" if row["source_format"] == "application/pdf" else "beautifulsoup4 4.15.0"),
        "normalization": "UTF-8, LF, Unicode NFC; no NFKC",
        "scope": row["scope"],
        "segment_count": len(segments),
        "aligned_translation_count": len(aligned_rows),
        "japanese_character_count": len(ja_text),
        "translation_failures": failures,
        **base_report,
    }
    (qa / "extraction-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    row["extraction"] = {
        "original_ja_path": str((derived / "original.ja.txt").relative_to(ROOT)),
        "tool": report["extractor"],
        "normalized_text_sha256": sha_text(ja_text),
        "ocr_used": report.get("ocr_used", False),
        "scope": row["scope"],
    }
    row["translation"] = {
        "path": str((derived / "translation.ko.md").relative_to(ROOT)),
        "model": "Google Translate web endpoint (client=gtx; undocumented)",
        "prompt_policy": TRANSLATION_POLICY,
        "prompt_sha256": TRANSLATION_POLICY_SHA,
        "generated_at": now_iso(),
        "review_status": "machine_unreviewed",
        "scope": row["scope"],
        "failure_count": len(failures),
        "source_sha256": row["sha256"],
        "translation_build_id": f"{TRANSLATION_BUILD_ID}-{row['sha256'][:12]}",
    }
    if row.get("metadata_only"):
        row["corpus_status"] = "supporting_original_only"
    elif row.get("search_enabled") is False:
        row["corpus_status"] = "supporting_reference"
    else:
        row["corpus_status"] = "active"
    row["translation_ready"] = bool(not row.get("metadata_only") and aligned_rows and not failures)
    row["translation_requirement"] = "not_applicable_supporting_original_only" if row.get("metadata_only") else "required"
    row["aligned_segments_path"] = str((aligned / "segments.jsonl").relative_to(ROOT))
    row["qa_report_path"] = str((qa / "extraction-report.json").relative_to(ROOT))
    return row


def main() -> int:
    rows = load_manifest()
    requested_ids = set(sys.argv[1:])
    unknown_ids = requested_ids - {row["id"] for row in rows}
    if unknown_ids:
        raise RuntimeError(f"Unknown source IDs: {sorted(unknown_ids)}")
    updated = []
    for row in rows:
        if requested_ids and row["id"] not in requested_ids:
            updated.append(row)
            continue
        print(f"Extracting {row['id']} ...", flush=True)
        original_path = ROOT / row["original_path"]
        data = original_path.read_bytes()
        base_report = {"ocr_used": False, "ocr_candidates": []}
        if row.get("metadata_only"):
            segments = []
        elif row["source_format"] == "application/xml":
            segments = xml_segments(row, data)
        elif row["source_format"] == "application/pdf":
            segments, base_report = pdf_segments(row, original_path)
        elif row["source_format"] == "text/html":
            segments = html_segments(row, data)
        else:
            raise RuntimeError(f"Unsupported format: {row['source_format']}")
        updated.append(write_outputs(row, segments, base_report))

    manifest_text = "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in updated) + "\n"
    MANIFEST.write_text(unicodedata.normalize("NFC", manifest_text), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
