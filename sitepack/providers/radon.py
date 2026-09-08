"""ČGS radon 1:50k — LIVE WMS/MapServer identify; stub fallback."""

from __future__ import annotations

from app.models import DataMode, LayerResult, PackRequest, ParcelIdentity, TrafficLight

from .base import country_code, is_demo_request
from .geo_cache import parcel_polygon_from_identity
from .http_util import http_get_query

RADON50 = "https://mapy.geology.cz/arcgis/rest/services/Geohazardy/radon50/MapServer"

# Převažující radonový index: 1=nízký, 2=střední, 3=vysoký (ČGS legend)
INDEX_CS = {"1": "nízké", "2": "střední", "3": "vysoké", 1: "nízké", 2: "střední", 3: "vysoké"}


class RadonProvider:
    layer_id = "radon"

    def fetch(self, req: PackRequest, parcel: ParcelIdentity) -> LayerResult:
        cc = country_code(req, parcel)
        if cc != "CZ":
            return self._stub(reason=f"country={cc} not implemented (CZ-only v1)")

        if req.prefer_live:
            try:
                return self._live(parcel)
            except Exception as exc:  # noqa: BLE001
                fb = self._stub_or_demo(req)
                fb.mode = DataMode.fallback
                fb.source_status = "FALLBACK"
                fb.blocker = f"live radon identify failed: {exc!s}"
                fb.summary_lines = [f"FALLBACK po chybě live: {exc!s}", *fb.summary_lines]
                fb.is_mock = True
                return fb
        return self._stub_or_demo(req)

    def _live(self, parcel: ParcelIdentity) -> LayerResult:
        geom = parcel_polygon_from_identity(parcel)
        if geom is None:
            raise RuntimeError("parcel geometry missing for radon identify")
        c = geom.centroid
        minx, miny, maxx, maxy = geom.bounds
        pad = 0.01
        data = http_get_query(
            f"{RADON50}/identify",
            {
                "geometry": f"{c.x},{c.y}",
                "geometryType": "esriGeometryPoint",
                "sr": "4326",
                "layers": "all:1,2",
                "tolerance": "3",
                "mapExtent": f"{minx - pad},{miny - pad},{maxx + pad},{maxy + pad}",
                "imageDisplay": "400,400,96",
                "returnGeometry": "false",
                "f": "pjson",
            },
            timeout=25.0,
        )
        if data.get("error"):
            raise RuntimeError(str(data["error"]))
        results = list(data.get("results") or [])
        if not results:
            raise RuntimeError("radon identify returned no results")

        # Prefer layer 1 (1:50k) then layer 2 overview
        primary = next((r for r in results if r.get("layerId") == 1), results[0])
        attrs = primary.get("attributes") or {}
        raw_idx = attrs.get("Převažující radonový index") or attrs.get("Prevazujici radonovy index")
        cat = INDEX_CS.get(raw_idx) or INDEX_CS.get(str(raw_idx)) or attrs.get("radonový index popis") or "neznámé"
        popis = attrs.get("Radonový index - popis") or attrs.get("radonový index popis") or ""

        if cat.startswith("vysok"):
            light = TrafficLight.red
        elif cat.startswith("střed") or cat.startswith("stred"):
            light = TrafficLight.yellow
        else:
            light = TrafficLight.green

        return LayerResult(
            layer_id=self.layer_id,
            title_cs="Radon",
            light=light,
            summary_lines=[
                f"Mapa ČGS 1:50 000 (LIVE identify): {cat} radonové riziko",
                f"Kategorie: {cat}" + (f" — {popis}" if popis else ""),
                "Před výstavbou: povinné měření radonového indexu pozemku",
            ],
            detail={
                "category": cat,
                "raw_index": raw_idx,
                "scale": "1:50000",
                "attributes": {k: attrs.get(k) for k in list(attrs)[:12]},
                "endpoint": RADON50,
                "country": "CZ",
            },
            source="ČGS Geohazardy/radon50 MapServer · identify · CC BY · LIVE",
            disclaimer_kind="danger",
            disclaimer_title="⚠ POVINNÉ UPOZORNĚNÍ — radon",
            disclaimer_body=(
                "Údaj je pouze regionální (mapa 1:50 000). Nenahrazuje měření na pozemku. "
                "Před výstavbou / kolaudací je nutné provést měření radonového indexu pozemku "
                "oprávněnou osobou dle platné legislativy. SitePack Pro nevydává závazné posudky."
            ),
            is_mock=False,
            mode=DataMode.live,
            source_status="LIVE",
        )

    def _stub_or_demo(self, req: PackRequest) -> LayerResult:
        if is_demo_request(req):
            return LayerResult(
                layer_id=self.layer_id,
                title_cs="Radon",
                light=TrafficLight.red,
                summary_lines=[
                    "Mapa ČGS 1:50 000: vysoké radonové riziko",
                    "Kategorie: vysoké (regionální vrstva)",
                    "Před výstavbou: povinné měření radonového indexu pozemku",
                ],
                detail={"category": "vysoké", "scale": "1:50000"},
                source="ČGS — mapa radonového indexu 1:50k · CC BY",
                disclaimer_kind="danger",
                disclaimer_title="⚠ POVINNÉ UPOZORNĚNÍ — radon",
                disclaimer_body=(
                    "Údaj je pouze regionální (mapa 1:50 000). Nenahrazuje měření na pozemku."
                ),
                is_mock=True,
                mode=DataMode.demo,
                source_status="DEMO",
            )
        return self._stub()

    def _stub(self, reason: str = "ČGS radon identify pending") -> LayerResult:
        return LayerResult(
            layer_id=self.layer_id,
            title_cs="Radon",
            light=TrafficLight.yellow,
            summary_lines=[f"Stub: {reason}"],
            source="ČGS (stub)",
            disclaimer_kind="danger",
            disclaimer_title="⚠ POVINNÉ UPOZORNĚNÍ — radon",
            disclaimer_body="Údaj je pouze regionální (mapa 1:50 000). Nenahrazuje měření na pozemku.",
            is_mock=True,
            mode=DataMode.stub,
            source_status="STUB",
            blocker=reason,
        )
