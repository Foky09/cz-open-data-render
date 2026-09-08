"""RÚIAN parcel identity — LIVE via ČÚZK ArcGIS MapServer; stub/demo fallback.

No API keys. No KN ownership. Free browse service:
https://ags.cuzk.gov.cz/arcgis/rest/services/RUIAN/MapServer (layer 5 Parcela)
VFR/VDP UI still documented as bulk ingest path.
"""

from __future__ import annotations

import json
from pathlib import Path

from shapely.geometry import Polygon, MultiPolygon

from app.models import DataMode, ParcelIdentity, PackRequest

from .base import country_code, is_demo_request
from .http_util import http_get_query

DEMO_DATA = Path(__file__).resolve().parent.parent / "data" / "demo_parcel.json"

RUIAN_MAP = "https://ags.cuzk.gov.cz/arcgis/rest/services/RUIAN/MapServer"
LAYER_PARCELA = 5
LAYER_KU = 7
LAYER_OBEC = 12
VDP_UI = "https://vdp.cuzk.gov.cz/vdp/ruian"
VDP_PARCEL_HINT = "https://vdp.cuzk.gov.cz/vdp/ruian/parcely/{ruian_id}"

DRUH_POZEMKU = {
    2: "orná půda",
    3: "chmelnice",
    4: "vinice",
    5: "zahrada",
    6: "ovocný sad",
    7: "trvalý travní porost",
    8: "lesní pozemek",
    10: "vodní plocha",
    11: "zastavěná plocha a nádvoří",
    13: "ostatní plocha",
    14: "orná půda",
}


class RuianProvider:
    layer_id = "ruian"

    def resolve(self, req: PackRequest) -> ParcelIdentity:
        cc = country_code(req)
        if cc != "CZ":
            return ParcelIdentity(
                ruian_id=req.ruian_id,
                ku_name=(req.ku or "—").strip(),
                parcel_number=(req.parcel_number or "—").strip(),
                is_mock=True,
                mode=DataMode.stub,
                source_status="STUB",
                blocker=f"country={cc} not implemented (CZ-only v1)",
                lookup_note=f"RÚIAN is CZ-only. country={cc}",
            )

        # Demo identity (fictional Id) — keep DEMO; polygon still drives live joins
        if is_demo_request(req) and not req.force_live_ruian:
            return self._demo()

        if req.prefer_live or req.force_live_ruian:
            try:
                if req.ruian_id and req.ruian_id.strip():
                    return self._live_by_id(req.ruian_id.strip())
                if req.ku and req.parcel_number:
                    return self._live_by_ku_parcel(req.ku.strip(), req.parcel_number.strip())
            except Exception as exc:  # noqa: BLE001
                stub = self._stub(req, reason=str(exc))
                stub.mode = DataMode.fallback
                stub.source_status = "FALLBACK"
                stub.blocker = f"live RÚIAN MapServer failed: {exc!s}"
                stub.lookup_note = (
                    f"FALLBACK after live error: {exc!s}. "
                    f"Service: {RUIAN_MAP}/{LAYER_PARCELA}. VDP UI: {VDP_UI}"
                )
                return stub

        return self._stub(req)

    def _demo(self) -> ParcelIdentity:
        raw = json.loads(DEMO_DATA.read_text(encoding="utf-8"))
        p = raw["parcel"]
        return ParcelIdentity(
            ruian_id=p["ruian_id"],
            ku_code=p.get("ku_code"),
            ku_name=p["ku_name"],
            parcel_number=p["parcel_number"],
            area_m2=p["area_m2"],
            parcel_type=p["parcel_type"],
            obec=p["obec"],
            okres=p["okres"],
            geometry_wkt=p.get("geometry_wkt"),
            geometry_note=p.get("geometry_note", "Mini mapa — placeholder"),
            is_mock=True,
            mode=DataMode.demo,
            source_status="DEMO",
            lookup_note=(
                "Demo identita (fiktivní RÚIAN Id) + WGS84 polygon pro LIVE open-data joins. "
                f"Produkční LIVE: {RUIAN_MAP} layer Parcela. Žádné KN ownership."
            ),
        )

    def _stub(self, req: PackRequest, reason: str = "need ruian_id or ku+parcel") -> ParcelIdentity:
        return ParcelIdentity(
            ruian_id=req.ruian_id or None,
            ku_name=(req.ku or "—").strip(),
            parcel_number=(req.parcel_number or "—").strip(),
            parcel_type="Neznámý (stub)",
            geometry_note="Mini mapa — placeholder (žádná live geometrie)",
            is_mock=True,
            mode=DataMode.stub,
            source_status="STUB",
            blocker=reason,
            lookup_note=(
                f"Stub: {reason}. LIVE hook: {RUIAN_MAP}/{LAYER_PARCELA} (id / cisloparcely). "
                f"VDP UI: {VDP_UI}. Žádné KN ownership."
            ),
        )

    def _live_by_id(self, ruian_id: str) -> ParcelIdentity:
        # id is numeric in RÚIAN
        rid = ruian_id.replace(" ", "")
        data = http_get_query(
            f"{RUIAN_MAP}/{LAYER_PARCELA}/query",
            {
                "where": f"id={rid}",
                "outFields": "id,cisloparcely,vymeraparcely,katastralniuzemi,druhpozemkukod,kmenovecislo,poddelenicisla",
                "returnGeometry": "true",
                "outSR": "4326",
                "resultRecordCount": "1",
                "f": "pjson",
            },
            timeout=25.0,
        )
        if data.get("error"):
            raise RuntimeError(str(data["error"]))
        feats = data.get("features") or []
        if not feats:
            raise RuntimeError(f"no Parcela feature for id={rid}")
        return self._from_feature(feats[0])

    def _live_by_ku_parcel(self, ku: str, parcel_number: str) -> ParcelIdentity:
        ku_code = self._resolve_ku_code(ku)
        cislo = parcel_number.replace(" ", "")
        where = f"katastralniuzemi={ku_code} AND cisloparcely='{cislo}'"
        data = http_get_query(
            f"{RUIAN_MAP}/{LAYER_PARCELA}/query",
            {
                "where": where,
                "outFields": "id,cisloparcely,vymeraparcely,katastralniuzemi,druhpozemkukod,kmenovecislo,poddelenicisla",
                "returnGeometry": "true",
                "outSR": "4326",
                "resultRecordCount": "3",
                "f": "pjson",
            },
            timeout=25.0,
        )
        if data.get("error"):
            raise RuntimeError(str(data["error"]))
        feats = data.get("features") or []
        if not feats:
            raise RuntimeError(f"no Parcela for k.ú.={ku_code} číslo={cislo}")
        return self._from_feature(feats[0])

    def _resolve_ku_code(self, ku: str) -> int:
        if ku.isdigit():
            return int(ku)
        # escape single quotes
        safe = ku.replace("'", "''")
        data = http_get_query(
            f"{RUIAN_MAP}/{LAYER_KU}/query",
            {
                "where": f"nazev='{safe}'",
                "outFields": "kod,nazev,obec",
                "returnGeometry": "false",
                "resultRecordCount": "5",
                "f": "pjson",
            },
            timeout=20.0,
        )
        feats = data.get("features") or []
        if not feats:
            # try LIKE
            data = http_get_query(
                f"{RUIAN_MAP}/{LAYER_KU}/query",
                {
                    "where": f"nazev LIKE '%{safe}%'",
                    "outFields": "kod,nazev,obec",
                    "returnGeometry": "false",
                    "resultRecordCount": "5",
                    "f": "pjson",
                },
                timeout=20.0,
            )
            feats = data.get("features") or []
        if not feats:
            raise RuntimeError(f"k.ú. not found: {ku}")
        return int(feats[0]["attributes"]["kod"])

    def _from_feature(self, feat: dict) -> ParcelIdentity:
        attrs = feat.get("attributes") or {}
        geom = feat.get("geometry") or {}
        rings = geom.get("rings") or []
        if not rings:
            raise RuntimeError("Parcela feature missing geometry rings")
        polys = [Polygon(r) for r in rings if len(r) >= 4]
        if not polys:
            raise RuntimeError("invalid parcel rings")
        shape = polys[0] if len(polys) == 1 else MultiPolygon(polys)
        wkt = shape.wkt

        ku_code = attrs.get("katastralniuzemi")
        ku_name, obec_name = self._ku_obec_names(ku_code)
        druh = attrs.get("druhpozemkukod")
        parcel_type = DRUH_POZEMKU.get(int(druh) if druh is not None else -1, f"kód druhu {druh}")

        rid = attrs.get("id")
        rid_s = str(int(rid)) if rid is not None else None

        return ParcelIdentity(
            ruian_id=rid_s,
            ku_code=str(ku_code) if ku_code is not None else None,
            ku_name=ku_name or (str(ku_code) if ku_code else "—"),
            parcel_number=str(attrs.get("cisloparcely") or "—"),
            area_m2=float(attrs["vymeraparcely"]) if attrs.get("vymeraparcely") is not None else None,
            parcel_type=parcel_type,
            obec=obec_name or "",
            okres="",
            geometry_wkt=wkt,
            geometry_note="RÚIAN LIVE polygon (WGS84)",
            is_mock=False,
            mode=DataMode.live,
            source_status="LIVE",
            lookup_note=(
                f"LIVE ČÚZK RÚIAN MapServer layer Parcela ({RUIAN_MAP}/{LAYER_PARCELA}). "
                "Bez KN ownership."
            ),
        )

    def _ku_obec_names(self, ku_code) -> tuple[str, str]:
        if ku_code is None:
            return "", ""
        try:
            ku_data = http_get_query(
                f"{RUIAN_MAP}/{LAYER_KU}/query",
                {
                    "where": f"kod={int(ku_code)}",
                    "outFields": "kod,nazev,obec",
                    "returnGeometry": "false",
                    "resultRecordCount": "1",
                    "f": "pjson",
                },
                timeout=15.0,
            )
            feats = ku_data.get("features") or []
            if not feats:
                return str(ku_code), ""
            a = feats[0]["attributes"]
            ku_name = str(a.get("nazev") or ku_code)
            obec_kod = a.get("obec")
            obec_name = ""
            if obec_kod is not None:
                o = http_get_query(
                    f"{RUIAN_MAP}/{LAYER_OBEC}/query",
                    {
                        "where": f"kod={int(obec_kod)}",
                        "outFields": "kod,nazev",
                        "returnGeometry": "false",
                        "resultRecordCount": "1",
                        "f": "pjson",
                    },
                    timeout=15.0,
                )
                of = o.get("features") or []
                if of:
                    obec_name = str(of[0]["attributes"].get("nazev") or "")
            return ku_name, obec_name
        except Exception:  # noqa: BLE001
            return str(ku_code), ""
