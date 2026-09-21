# Corpus build report

- Generated: 2026-09-21T16:02:12+09:00
- Canonical root: `/Users/jiisuniui/Documents/GS-Hackathon/jp-yakkiho-corpus`
- Included official sources: 10
- Inventoried files excluding `.venv` and report self-files: 88
- Validation: `qa/validation-report.json` reports `ok: true`
- Runtime translation: disabled; pre-generated JA/KO/aligned artifacts only

## Sources

| ID | Version | Raw bytes | Segments | Scope/status | Translation ready | SHA-256 |
|---|---|---:|---:|---|---|---|
| JP-LAW-001 | 335AC0000000145_20260521_505AC0000000063 | 1480372 | 6 | full_xml; derived_and_translation_articles=2,59,61,66,67,68 / active | true | `ecb7acd3958203a9e08a4e505e3554a7adaae5670ae575fe7af6812a05215f8a` |
| JP-AD-001 | 2017-09-29 | 133475 | 6 | full_document / active | true | `e0a48779966e1b142051632d8f488865a6b6a17546a920458830e3c19499779d` |
| JP-AD-002 | 2017-09-29 | 394997 | 32 | full_document / active | true | `1d3b8ccd3c188dde573bd4f383cd61b7aa6315504d26200568fe905c9d181162` |
| JP-AD-003 | 1998-09-29 | 97159 | 1 | full_document / active | true | `803c843309505b63ea2ba6e856cc0f4e772d3a849062662b03c363f945937b0c` |
| JP-EFF-001 | 2011-07-21 | 111865 | 3 | full_document / active | true | `47d5a1734b1f2ac03a6a6cbc806a461eb27b666b3ba33cfbc96cb2858112663b` |
| JP-EFF-002 | 2011-07-21 | 227015 | 4 | full_document / active | true | `fbbee56b1e7c88b4d20f0985e4f76221146b59e33cc01770fd9973c02fc6631c` |
| JP-AD-006 | 2025-03-10 | 21982 | 2 | full_document / active | true | `1ede329f3a1b410d19441341b53c254daca86683e4e8fbd72a00ef8d60acc2fb` |
| JP-EXEC-001 | 336CO0000000011_20260501_507CO0000000362 | 729371 | 0 | metadata_and_full_xml_only / supporting_original_only | false | `b7ae8a7aaa36d084a7c2adedc91cade0d6cae742b03ffa7e70a669114a3e1e77` |
| JP-PMDA-001 | - | 127459 | 3 | full_page_reference_index / supporting_reference | true | `31d373299e1ddffb0f8b4d21b96da6f287a647d8e53aad306418fc25168d4b7e` |
| JP-REG-001 | 336M50000100001_20260824_508M60000100133 | 4460061 | 0 | metadata_and_full_xml_only / supporting_original_only | false | `7166665a91fa17b6212c54c2b3e8f7d6e74ef375a187a86f6695496caf996a2a` |

## Build outcome

- Active search sources: 7
- Japanese search chunks: 54
- Korean search chunks: 54
- Translation failures: 0
- OCR candidates: 0; all included PDFs had usable text layers
- JP-LAW-001 translation scope: Articles 2, 59, 61, 66, 67, 68; the complete official XML is preserved
- JP-EXEC-001 and JP-REG-001: complete official XML and revision metadata preserved; full-text translation intentionally outside the active advertising MVP
- JP-PMDA-001: full official index page extracted and translated as a supporting reference; excluded from the default search index
- JCIA: no PDF/full text/translation stored; only restricted manifest, source locators, team-authored rule cards, and a permission-gated downloader

## Rebuild

```bash
cd /Users/jiisuniui/Documents/GS-Hackathon/jp-yakkiho-corpus
scripts/fetch_sources
scripts/extract
scripts/validate
scripts/build_search_index
scripts/build_report
```

If a source hash changes, `fetch_sources` makes `translation_ready` false. Do not publish until extraction, translation, alignment, and validation succeed again.
