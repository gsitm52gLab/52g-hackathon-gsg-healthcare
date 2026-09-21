#!/usr/bin/env python3
"""Download immutable originals from official Japanese government sources."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
import unicodedata
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.jsonl"
USER_AGENT = "GSG-jp-yakki-corpus/1.0 (research; official-public-documents)"

SOURCES = [
    {
        "id": "JP-LAW-001",
        "title_ja": "医薬品、医療機器等の品質、有効性及び安全性の確保等に関する法律",
        "title_ko": "의약품·의료기기 등의 품질·유효성 및 안전성 확보 등에 관한 법률",
        "issuer": "デジタル庁 / e-Gov法令検索",
        "authority_type": "statute",
        "official_document_no": "昭和三十五年法律第百四十五号",
        "url": "https://laws.e-gov.go.jp/api/2/law_file/xml/335AC0000000145",
        "canonical_url": "https://laws.e-gov.go.jp/law/335AC0000000145",
        "metadata_url": "https://laws.e-gov.go.jp/api/2/law_revisions/335AC0000000145?response_format=json",
        "ext": "xml",
        "source_language": "ja",
        "promulgated_at": "1960-08-10",
        "scope": "full_xml; derived_and_translation_articles=2,59,61,66,67,68",
        "target_articles": ["2", "59", "61", "66", "67", "68"],
    },
    {
        "id": "JP-AD-001",
        "title_ja": "医薬品等適正広告基準の改正について",
        "title_ko": "의약품 등 적정광고기준 개정",
        "issuer": "厚生労働省",
        "authority_type": "mhlw_notice",
        "official_document_no": "薬生発0929第4号",
        "url": "https://www.mhlw.go.jp/file/06-Seisakujouhou-11120000-Iyakushokuhinkyoku/0000179264.pdf",
        "canonical_url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iyakuhin/koukokukisei/index.html",
        "ext": "pdf",
        "source_language": "ja",
        "published_at": "2017-09-29",
        "effective_at": "2017-09-29",
        "scope": "full_document",
    },
    {
        "id": "JP-AD-002",
        "title_ja": "医薬品等適正広告基準の解説及び留意事項等について",
        "title_ko": "의약품 등 적정광고기준 해설 및 유의사항",
        "issuer": "厚生労働省",
        "authority_type": "mhlw_official_explanation",
        "official_document_no": "薬生監麻発0929第5号",
        "url": "https://www.mhlw.go.jp/file/06-Seisakujouhou-11120000-Iyakushokuhinkyoku/0000179263.pdf",
        "canonical_url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iyakuhin/koukokukisei/index.html",
        "ext": "pdf",
        "source_language": "ja",
        "published_at": "2017-09-29",
        "effective_at": "2017-09-29",
        "scope": "full_document",
    },
    {
        "id": "JP-AD-003",
        "title_ja": "薬事法における医薬品等の広告の該当性について",
        "title_ko": "약사법상 의약품 등 광고 해당성",
        "issuer": "厚生労働省",
        "authority_type": "mhlw_notice",
        "official_document_no": "医薬監第148号",
        "url": "https://www.mhlw.go.jp/bunya/iyakuhin/koukokukisei/dl/index_d.pdf",
        "canonical_url": "https://www.mhlw.go.jp/web/t_doc?dataId=00tb5413&dataType=1&pageNo=1",
        "ext": "pdf",
        "source_language": "ja",
        "published_at": "1998-09-29",
        "effective_at": "1998-09-29",
        "scope": "full_document",
    },
    {
        "id": "JP-EFF-001",
        "title_ja": "化粧品の効能の範囲の改正について",
        "title_ko": "화장품 효능 범위 개정(56개 효능)",
        "issuer": "厚生労働省",
        "authority_type": "mhlw_notice",
        "official_document_no": "薬食発0721第1号",
        "url": "https://www.mhlw.go.jp/file/06-Seisakujouhou-11120000-Iyakushokuhinkyoku/kesyouhin_hanni_20111.pdf",
        "canonical_url": "https://www.mhlw.go.jp/web/t_doc?dataId=00tb7518&dataType=1",
        "ext": "pdf",
        "source_language": "ja",
        "published_at": "2011-07-21",
        "effective_at": "2011-07-21",
        "scope": "full_document",
    },
    {
        "id": "JP-EFF-002",
        "title_ja": "化粧品の効能の範囲の改正に係る取扱いについて",
        "title_ko": "화장품 효능 범위 개정 취급(건조에 의한 잔주름)",
        "issuer": "厚生労働省",
        "authority_type": "mhlw_notice",
        "official_document_no": "薬食審査発0721第1号 / 薬食監麻発0721第1号",
        "url": "https://www.mhlw.go.jp/file/06-Seisakujouhou-11120000-Iyakushokuhinkyoku/kesyouhin_hanni_20112.pdf",
        "canonical_url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iyakuhin/keshouhin/index.html",
        "ext": "pdf",
        "source_language": "ja",
        "published_at": "2011-07-21",
        "effective_at": "2011-07-21",
        "scope": "full_document",
    },
    {
        "id": "JP-AD-006",
        "title_ja": "化粧品における特定成分の特記表示について",
        "title_ko": "화장품의 특정 성분 특기 표시",
        "issuer": "厚生労働省",
        "authority_type": "mhlw_notice",
        "official_document_no": "医薬監麻発0310第3号",
        "url": "https://www.mhlw.go.jp/web/t_doc?dataId=00tc9762&dataType=1&pageNo=1",
        "canonical_url": "https://www.mhlw.go.jp/web/t_doc?dataId=00tc9762&dataType=1&pageNo=1",
        "ext": "html",
        "source_language": "ja",
        "published_at": "2025-03-10",
        "effective_at": "2025-03-10",
        "scope": "full_document",
    },
    {
        "id": "JP-EXEC-001",
        "title_ja": "医薬品、医療機器等の品質、有効性及び安全性の確保等に関する法律施行令",
        "title_ko": "약기법 시행령",
        "issuer": "デジタル庁 / e-Gov法令検索",
        "authority_type": "cabinet_order",
        "official_document_no": "昭和三十六年政令第十一号",
        "url": "https://laws.e-gov.go.jp/api/2/law_file/xml/336CO0000000011",
        "canonical_url": "https://laws.e-gov.go.jp/law/336CO0000000011",
        "metadata_url": "https://laws.e-gov.go.jp/api/2/law_revisions/336CO0000000011?response_format=json",
        "ext": "xml",
        "source_language": "ja",
        "promulgated_at": "1961-01-26",
        "scope": "metadata_and_full_xml_only",
        "metadata_only": True,
    },
    {
        "id": "JP-PMDA-001",
        "title_ja": "医薬部外品・化粧品の各種関連通知",
        "title_ko": "의약부외품·화장품 관련 통지 안내",
        "issuer": "独立行政法人 医薬品医療機器総合機構 (PMDA)",
        "authority_type": "pmda_official_index",
        "official_document_no": None,
        "url": "https://www.pmda.go.jp/review-services/drug-reviews/about-reviews/q-drugs/0002.html",
        "canonical_url": "https://www.pmda.go.jp/review-services/drug-reviews/about-reviews/q-drugs/0002.html",
        "ext": "html",
        "source_language": "ja",
        "published_at": None,
        "effective_at": None,
        "scope": "full_page_reference_index",
        "search_enabled": False,
    },
    {
        "id": "JP-REG-001",
        "title_ja": "医薬品、医療機器等の品質、有効性及び安全性の確保等に関する法律施行規則",
        "title_ko": "약기법 시행규칙",
        "issuer": "デジタル庁 / e-Gov法令検索",
        "authority_type": "ministerial_ordinance",
        "official_document_no": "昭和三十六年厚生省令第一号",
        "url": "https://laws.e-gov.go.jp/api/2/law_file/xml/336M50000100001",
        "canonical_url": "https://laws.e-gov.go.jp/law/336M50000100001",
        "metadata_url": "https://laws.e-gov.go.jp/api/2/law_revisions/336M50000100001?response_format=json",
        "ext": "xml",
        "source_language": "ja",
        "promulgated_at": "1961-02-01",
        "scope": "metadata_and_full_xml_only",
        "metadata_only": True,
    },
]


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def fetch(url: str) -> tuple[bytes, dict[str, str], str]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=90) as response:
        return response.read(), dict(response.headers.items()), response.geturl()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".tmp-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def previous_by_id() -> dict[str, dict]:
    if not MANIFEST.exists():
        return {}
    rows = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            rows[row["id"]] = row
    return rows


def current_revision(metadata: dict) -> dict | None:
    revisions = metadata.get("revisions") or []
    for revision in revisions:
        if revision.get("current_revision_status") == "CurrentEnforced":
            return revision
    # Some e-Gov history responses expose the served current text as
    # PreviousEnforced when future consolidated revisions already exist.
    # The list is newest first, so select the newest revision that is not
    # explicitly un-enforced instead of accidentally choosing a future text.
    for revision in revisions:
        if revision.get("current_revision_status") != "UnEnforced":
            return revision
    return revisions[0] if revisions else None


def main() -> int:
    previous = previous_by_id()
    requested_ids = set(sys.argv[1:])
    known_ids = {source["id"] for source in SOURCES}
    unknown_ids = requested_ids - known_ids
    if unknown_ids:
        raise RuntimeError(f"Unknown source IDs: {sorted(unknown_ids)}")
    rows = []
    retrieved_at = now_iso()
    for source in SOURCES:
        if requested_ids and source["id"] not in requested_ids:
            if source["id"] in previous:
                rows.append(previous[source["id"]])
            continue
        data, headers, final_url = fetch(source["url"])
        digest = sha256(data)
        source_dir = ROOT / "sources" / source["id"] / "original"
        original_path = source_dir / f"{digest[:12]}-official.{source['ext']}"
        if not original_path.exists():
            write_atomic(original_path, data)

        metadata = None
        revision = None
        metadata_path = None
        if source.get("metadata_url"):
            metadata_bytes, metadata_headers, metadata_final_url = fetch(source["metadata_url"])
            metadata = json.loads(metadata_bytes.decode("utf-8"))
            revision = current_revision(metadata)
            meta_digest = sha256(metadata_bytes)
            metadata_path = source_dir / f"{meta_digest[:12]}-law-revisions.json"
            if not metadata_path.exists():
                write_atomic(metadata_path, metadata_bytes)
            headers["Metadata-Final-URL"] = metadata_final_url
            headers["Metadata-SHA256"] = meta_digest

        header_payload = {
            "requested_url": source["url"],
            "final_url": final_url,
            "retrieved_at": retrieved_at,
            "headers": headers,
        }
        header_path = source_dir / f"headers-{digest[:12]}.json"
        if not header_path.exists():
            write_atomic(
                header_path,
                json.dumps(header_payload, ensure_ascii=False, indent=2).encode("utf-8"),
            )

        old = previous.get(source["id"], {})
        row = {k: v for k, v in source.items() if k not in {"url", "ext"}}
        row.update(
            {
                "download_url": source["url"],
                "final_url": final_url,
                "source_format": {"pdf": "application/pdf", "xml": "application/xml", "html": "text/html"}[source["ext"]],
                "retrieved_at": retrieved_at,
                "original_path": str(original_path.relative_to(ROOT)),
                "headers_path": str(header_path.relative_to(ROOT)),
                "byte_size": len(data),
                "sha256": digest,
                "version_id": revision.get("law_revision_id") if revision else source.get("published_at", digest[:12]),
                "amended_at": revision.get("amendment_promulgate_date") if revision else source.get("published_at"),
                "effective_at": revision.get("amendment_enforcement_date") if revision else source.get("effective_at"),
                "metadata_path": str(metadata_path.relative_to(ROOT)) if metadata_path else None,
                "status": "current",
                "supersedes": old.get("version_id") if old and old.get("sha256") != digest else old.get("supersedes"),
                "license": {
                    "policy": "PDL-1.0",
                    "terms_url": "https://www.e-gov.go.jp/terms" if "e-Gov" in source["issuer"] else "https://www.mhlw.go.jp/chosakuken/",
                    "attribution_required": True,
                },
            }
        )
        if old.get("sha256") == digest:
            for key in ("extraction", "translation", "aligned_segments_path", "qa_report_path", "corpus_status", "translation_ready"):
                if key in old:
                    row[key] = old[key]
        else:
            row["translation_ready"] = False
            if not source.get("metadata_only"):
                row["translation_status"] = "stale_pending_rebuild"
        rows.append(row)
        print(f"{source['id']}\t{len(data)} bytes\t{digest}")

    manifest_text = "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n"
    manifest_text = unicodedata.normalize("NFC", manifest_text)
    write_atomic(MANIFEST, manifest_text.encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
