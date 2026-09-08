#!/usr/bin/env python3
"""One-shot demo: UKÁZKA identity + LIVE open-data joins → HTML+PDF."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app.models import PackRequest
from app.orchestrator import ConciergeOrchestrator
from app.render import generate_pack_files


def main() -> int:
    pack = ConciergeOrchestrator().build(
        PackRequest(demo=True, prefer_live=True, country="CZ")
    )
    html_path, pdf_path = generate_pack_files(pack, stem="sitepack-demo")
    print("OK demo pack")
    print("mode:", pack.mode_label)
    print("html:", html_path)
    print("pdf:", pdf_path)
    print("--- layer status ---")
    for row in pack.layer_status_table:
        print(f"  {row['layer']:12} {row['status']:10} {row.get('blocker') or ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
