"""CLI: python -m app.cli --demo | --ruian ID | --ku NAME --parcel 123/4 [--json]"""

from __future__ import annotations

import argparse
import json
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
    p.add_argument("--demo", action="store_true", help="Hardcoded UKÁZKA demo parcel (live joins via polygon)")
    p.add_argument("--ruian", dest="ruian_id", help="RÚIAN parcel Id")
    p.add_argument("--ku", help="Katastrální území (kód nebo název)")
    p.add_argument("--parcel", dest="parcel_number", help="Parcelní číslo, např. 123/4")
    p.add_argument("--live-ruian", action="store_true", help="Force live RÚIAN MapServer identity")
    p.add_argument("--stem", help="Output filename stem under output/")
    p.add_argument(
        "--json",
        action="store_true",
        help="Print pack summary JSON to stdout (no PDF unless --stem also set)",
    )
    p.add_argument("--no-files", action="store_true", help="Skip HTML/PDF generation")
    args = p.parse_args(argv)

    req = PackRequest(
        ruian_id=args.ruian_id,
        ku=args.ku,
        parcel_number=args.parcel_number,
        demo=args.demo or (not args.ruian_id and not (args.ku and args.parcel_number)),
        force_live_ruian=args.live_ruian,
        prefer_live=True,
    )
    pack = ConciergeOrchestrator().build(req)

    title_cs = {
        "ruian": "Identita parcely (RÚIAN)",
        "flood": "Povodně (VÚV Q₁₀₀)",
        "radon": "Radon (ČGS 1:50k)",
        "poddolovani": "Poddolování (ČGS)",
        "svahy": "Sesuvy / svahy (ČGS)",
        "zoning": "Územní plán (ÚÚR)",
    }
    layers = []
    for row in pack.layer_status_table:
        layers.append(
            {
                "layer": row["layer"],
                "status": row["status"],
                "mode": row.get("mode") or "",
                "blocker": row.get("blocker") or "",
                "titleCs": title_cs.get(row["layer"], row["layer"]),
            }
        )

    payload = {
        "ok": True,
        "mode_label": pack.mode_label,
        "is_example": pack.is_example,
        "generated_at": pack.generated_at,
        "parcel": {
            "ruian_id": pack.parcel.ruian_id,
            "ku_name": pack.parcel.ku_name,
            "parcel_number": pack.parcel.parcel_number,
            "obec": pack.parcel.obec,
            "mode": pack.parcel.mode.value,
            "source_status": pack.parcel.source_status,
        },
        "layers": layers,
        "live_layers": sum(1 for L in layers if str(L["status"]).upper() == "LIVE"),
        "attribution": pack.sources_blurb + " " + pack.no_ownership_note,
    }

    html_path = pdf_path = None
    if not args.no_files and (args.stem or not args.json):
        html_path, pdf_path = generate_pack_files(pack, stem=args.stem)
        payload["html"] = str(html_path)
        payload["pdf"] = str(pdf_path)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("mode:", pack.mode_label)
        print("parcel:", pack.parcel.ku_name, pack.parcel.parcel_number, "RÚIAN", pack.parcel.ruian_id)
        if html_path:
            print("html:", html_path)
            print("pdf:", pdf_path)
        print("--- layer status ---")
        for row in pack.layer_status_table:
            print(f"  {row['layer']:12} {row['status']:10} {row.get('blocker') or ''}")
        print("NOTE: No ownership / KN data. LIVE layers are not mock; DEMO identity may still be UKÁZKA.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
