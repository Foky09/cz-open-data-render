"""CLI: python -m app.cli --demo | --ruian ID | --ku NAME --parcel 123/4"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow `python -m app.cli` from concierge root
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models import PackRequest
from app.orchestrator import ConciergeOrchestrator
from app.render import generate_pack_files


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="SitePack Pro concierge — generate feasibility PDF pack")
    p.add_argument("--demo", action="store_true", help="Hardcoded UKÁZKA demo parcel")
    p.add_argument("--ruian", dest="ruian_id", help="RÚIAN parcel Id")
    p.add_argument("--ku", help="Katastrální území (kód nebo název)")
    p.add_argument("--parcel", dest="parcel_number", help="Parcelní číslo, např. 123/4")
    p.add_argument("--live-ruian", action="store_true", help="Probe public VDP URL (usually fails gracefully)")
    p.add_argument("--stem", help="Output filename stem under output/")
    args = p.parse_args(argv)

    req = PackRequest(
        ruian_id=args.ruian_id,
        ku=args.ku,
        parcel_number=args.parcel_number,
        demo=args.demo or (not args.ruian_id and not (args.ku and args.parcel_number)),
        force_live_ruian=args.live_ruian,
    )
    pack = ConciergeOrchestrator().build(req)
    html_path, pdf_path = generate_pack_files(pack, stem=args.stem)
    print("mode:", pack.mode_label)
    print("parcel:", pack.parcel.ku_name, pack.parcel.parcel_number, "RÚIAN", pack.parcel.ruian_id)
    print("html:", html_path)
    print("pdf:", pdf_path)
    print("--- layer status ---")
    for row in pack.layer_status_table:
        print(f"  {row['layer']:12} {row['status']:10} {row.get('blocker') or ''}")
    print("NOTE: No ownership / KN data. LIVE layers are not mock; DEMO identity may still be UKÁZKA.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
