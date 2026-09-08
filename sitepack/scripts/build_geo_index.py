#!/usr/bin/env python3
"""Build pickled WKB+meta spatial indexes from cached ČGS GeoJSON."""
from __future__ import annotations

import json
import pickle
from pathlib import Path

from shapely.geometry import shape

CACHE = Path(__file__).resolve().parent.parent / "data" / "cache"


def build(src_name: str, out_name: str, meta_keys: list[str]) -> None:
    src = CACHE / src_name
    out = CACHE / out_name
    print(f"loading {src} ...")
    with src.open(encoding="utf-8") as f:
        data = json.load(f)
    geoms = []
    meta = []
    for feat in data.get("features", []):
        geom = feat.get("geometry")
        if not geom:
            continue
        g = shape(geom)
        if g.is_empty:
            continue
        geoms.append(g)
        props = feat.get("properties") or {}
        meta.append({k: props.get(k) for k in meta_keys})
    payload = {"wkb": [g.wkb for g in geoms], "meta": meta}
    out.write_bytes(pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL))
    print(f"wrote {out} n={len(geoms)} bytes={out.stat().st_size}")


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    build(
        "poddolovane_uzemi.geojson",
        "poddolovane_uzemi_idx.pkl",
        ["klic", "nazev", "okres", "surovina", "projevy", "stari"],
    )
    build(
        "sesuvy_body.geojson",
        "sesuvy_body_idx.pkl",
        ["id", "nazev", "aktivita", "obec", "katastr", "skupina"],
    )
    # plochy is large — build if present (preferred for PiP)
    plochy = CACHE / "sesuvy_plochy.geojson"
    if plochy.exists():
        build(
            "sesuvy_plochy.geojson",
            "sesuvy_plochy_idx.pkl",
            ["id", "nazev", "aktivita", "obec", "katastr", "skupina"],
        )


if __name__ == "__main__":
    main()
