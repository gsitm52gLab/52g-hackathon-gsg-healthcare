#!/usr/bin/env python3
"""Permission-gated JCIA downloader. Do not run without documented permission."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "JP-JCIA-001": "https://www.jcia.org/user/common/download/business/advertising/JCIA20200615_ADguide.pdf",
    "JP-JCIA-002": "https://www.jcia.org/user/common/download/business/advertising/JCIA20200615_ADguide_comparison_table.pdf",
    "JP-JCIA-003": "https://www.jcia.org/user/common/download/business/advertising/JCIA20200622_ADguide_correctness_table.pdf",
}


def main() -> int:
    if os.environ.get("JCIA_CONTENT_PERMISSION_ACK") != "I_HAVE_PERMISSION":
        print("Refused: documented JCIA permission is required. Set JCIA_CONTENT_PERMISSION_ACK=I_HAVE_PERMISSION only after approval.", file=sys.stderr)
        return 3
    if len(sys.argv) != 2 or sys.argv[1] not in SOURCES:
        print(f"usage: {sys.argv[0]} {'|'.join(SOURCES)}", file=sys.stderr)
        return 2
    source_id = sys.argv[1]
    request = urllib.request.Request(SOURCES[source_id], headers={"User-Agent": "GSG-jp-yakki-corpus/1.0"})
    with urllib.request.urlopen(request, timeout=90) as response:
        data = response.read()
        final_url = response.geturl()
    digest = hashlib.sha256(data).hexdigest()
    output_dir = ROOT / "restricted" / source_id / "original"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{digest[:12]}-official.pdf"
    if not output.exists():
        output.write_bytes(data)
    receipt = {
        "source_id": source_id,
        "permission_acknowledged": True,
        "permission_evidence_path": "REQUIRED_BEFORE_COMMIT",
        "requested_url": SOURCES[source_id],
        "final_url": final_url,
        "retrieved_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "sha256": digest,
        "path": str(output.relative_to(ROOT)),
    }
    (output_dir.parent / "permission-and-fetch-receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

