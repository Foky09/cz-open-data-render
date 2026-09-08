"""Download / cache ČGS open GeoJSON zips and load spatial indexes."""

from __future__ import annotations

import pickle
import zipfile
from functools import lru_cache
from pathlib import Path

from shapely import STRtree
from shapely.geometry import shape
from shapely.wkb import loads as wkb_loads

from .http_util import download_file

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache"

CGS_PODDOLOVANI_ZIP = "https://od.geology.cz/poddolovane_uzemi.zip"
CGS_SVAHY_ZIP = "https://od.geology.cz/svahove_deformace.zip"


def ensure_cgs_cache(*, force: bool = False) -> dict[str, Path]:
    """Ensure zips + extracted GeoJSON exist under data/cache/."""
    CACHE.mkdir(parents=True, exist_ok=True)
    out: dict[str, Path] = {}

    pod_zip = CACHE / "poddolovane_uzemi.zip"
    pod_gj = CACHE / "poddolovane_uzemi.geojson"
    if force or not pod_gj.exists():
        if force or not pod_zip.exists():
            download_file(CGS_PODDOLOVANI_ZIP, pod_zip)
        with zipfile.ZipFile(pod_zip) as zf:
            zf.extractall(CACHE)
    out["poddolovani_geojson"] = pod_gj

    sv_zip = CACHE / "svahove_deformace.zip"
    body = CACHE / "sesuvy_body.geojson"
    plochy = CACHE / "sesuvy_plochy.geojson"
    if force or not body.exists() or not plochy.exists():
        if force or not sv_zip.exists():
            download_file(CGS_SVAHY_ZIP, sv_zip)
        with zipfile.ZipFile(sv_zip) as zf:
            zf.extractall(CACHE)
    out["sesuvy_body_geojson"] = body
    out["sesuvy_plochy_geojson"] = plochy
    return out


def _build_idx(geojson_path: Path, pkl_path: Path, meta_keys: list[str]) -> None:
    import json

    with geojson_path.open(encoding="utf-8") as f:
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
    pkl_path.write_bytes(
        pickle.dumps({"wkb": [g.wkb for g in geoms], "meta": meta}, protocol=pickle.HIGHEST_PROTOCOL)
    )


def ensure_indexes(*, force: bool = False) -> None:
    ensure_cgs_cache(force=force)
    specs = [
        (
            CACHE / "poddolovane_uzemi.geojson",
            CACHE / "poddolovane_uzemi_idx.pkl",
            ["klic", "nazev", "okres", "surovina", "projevy", "stari"],
        ),
        (
            CACHE / "sesuvy_body.geojson",
            CACHE / "sesuvy_body_idx.pkl",
            ["id", "nazev", "aktivita", "obec", "katastr", "skupina"],
        ),
        (
            CACHE / "sesuvy_plochy.geojson",
            CACHE / "sesuvy_plochy_idx.pkl",
            ["id", "nazev", "aktivita", "obec", "katastr", "skupina"],
        ),
    ]
    for gj, pkl, keys in specs:
        if force or not pkl.exists():
            if gj.exists():
                _build_idx(gj, pkl, keys)


@lru_cache(maxsize=4)
def load_index(name: str) -> tuple[STRtree, list[dict]]:
    """Load named index: poddolovani | sesuvy_plochy | sesuvy_body."""
    ensure_indexes()
    mapping = {
        "poddolovani": CACHE / "poddolovane_uzemi_idx.pkl",
        "sesuvy_plochy": CACHE / "sesuvy_plochy_idx.pkl",
        "sesuvy_body": CACHE / "sesuvy_body_idx.pkl",
    }
    path = mapping[name]
    if not path.exists():
        raise FileNotFoundError(path)
    payload = pickle.loads(path.read_bytes())
    geoms = [wkb_loads(b) for b in payload["wkb"]]
    return STRtree(geoms), payload["meta"]


def parcel_polygon_from_identity(parcel) -> object | None:
    """Parse WKT / GeoJSON polygon from ParcelIdentity; return shapely geom or None."""
    from shapely import wkt as shapely_wkt
    from shapely.geometry import shape
    import json

    if parcel.geometry_wkt:
        text = parcel.geometry_wkt.strip()
        if text.upper().startswith(("POLYGON", "MULTIPOLYGON", "POINT", "LINESTRING")):
            return shapely_wkt.loads(text)
        if text.startswith("{"):
            return shape(json.loads(text))
    return None


def deg_buffer_m(meters: float, lat: float = 49.2) -> float:
    """Rough degrees buffer for WGS84 at given latitude."""
    import math

    m_per_deg_lat = 111_320.0
    m_per_deg_lon = 111_320.0 * max(0.2, math.cos(math.radians(lat)))
    return meters / min(m_per_deg_lat, m_per_deg_lon)


def query_intersects(index_name: str, geom, *, limit: int = 20) -> list[dict]:
    tree, meta = load_index(index_name)
    # shapely 2 STRtree.query returns ndarray of indices
    idxs = tree.query(geom, predicate="intersects")
    hits = []
    for i in idxs:
        hits.append({**meta[int(i)], "_geom_idx": int(i)})
        if len(hits) >= limit:
            break
    return hits


def query_nearest_within(index_name: str, geom, *, max_m: float, limit: int = 10) -> list[dict]:
    """Nearest features within max_m (approx degrees→m) using envelope prefilter."""
    tree, meta = load_index(index_name)
    cent = geom.centroid
    buf = geom.buffer(deg_buffer_m(max_m, lat=cent.y))
    idxs = tree.query(buf)
    geoms = list(tree.geometries)
    scored: list[tuple[float, dict]] = []
    for i in idxs:
        ii = int(i)
        other = geoms[ii]
        d_m = float(geom.distance(other)) * 111_320.0
        if d_m <= max_m:
            scored.append((d_m, {**meta[ii], "distance_m": round(d_m, 1)}))
    scored.sort(key=lambda x: x[0])
    return [m for _, m in scored[:limit]]
