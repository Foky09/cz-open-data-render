"""VÚV TGM Q100 + aktivní zóna — LIVE ArcGIS REST intersect; stub fallback."""

from __future__ import annotations

from app.models import DataMode, LayerResult, PackRequest, ParcelIdentity, TrafficLight

from .base import country_code, is_demo_request
from .geo_cache import parcel_polygon_from_identity
from .http_util import http_get_query

# Documented endpoints (ags.vuv.cz is the live host; ags2 often 500)
VUV_MAPSERVER = "https://ags.vuv.cz/arcgis/rest/services/isvs_voda/isvs_voda/MapServer"
VUV_WFS = "https://ags.vuv.cz/arcgis/services/isvs_voda/isvs_voda/MapServer/WFSServer"
LAYER_Q100 = 13
LAYER_AZ = 11


class FloodProvider:
    layer_id = "flood"

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
                fb.blocker = f"live VÚV query failed: {exc!s}"
                fb.summary_lines = [f"FALLBACK po chybě live: {exc!s}", *fb.summary_lines]
                fb.is_mock = True
                return fb
        return self._stub_or_demo(req)

    def _live(self, parcel: ParcelIdentity) -> LayerResult:
        geom = parcel_polygon_from_identity(parcel)
        if geom is None:
            raise RuntimeError("parcel geometry missing for flood intersect")

        minx, miny, maxx, maxy = geom.bounds
        # slight pad
        pad = 0.0003
        envelope = f"{minx - pad},{miny - pad},{maxx + pad},{maxy + pad}"

        q100 = self._query_layer(LAYER_Q100, envelope)
        az = self._query_layer(LAYER_AZ, envelope)

        # refine: if envelope hit, still report as edge/hit (geometry return optional)
        q100_hit = len(q100) > 0
        az_hit = len(az) > 0
        tok = ", ".join(
            sorted(
                {
                    str(f.get("attributes", {}).get("NAZ_TOK") or "").strip()
                    for f in q100
                    if (f.get("attributes") or {}).get("NAZ_TOK")
                }
            )
        ) or "—"

        if az_hit:
            light = TrafficLight.red
            q_label = "zásah záplavového území Q₁₀₀"
        elif q100_hit:
            light = TrafficLight.yellow
            q_label = "zásah / blízkost Q₁₀₀ (obálka parcely)"
        else:
            light = TrafficLight.green
            q_label = "mimo Q₁₀₀ (v obálce parcely)"

        lines = [
            f"Q₁₀₀ (VÚV LIVE): {q_label}" + (f" · toky: {tok}" if q100_hit else ""),
            f"Aktivní zóna: {'zásah / blízkost' if az_hit else 'mimo aktivní zónu (obálka)'}",
            "Doporučení: ověřit u vodoprávního úřadu a projektanta",
        ]

        return LayerResult(
            layer_id=self.layer_id,
            title_cs="Povodně",
            light=light,
            summary_lines=lines,
            detail={
                "q100": "hit" if q100_hit else "none",
                "aktivni_zona": az_hit,
                "q100_features": [
                    {k: (f.get("attributes") or {}).get(k) for k in ("NAZ_TOK", "REC_NAZ", "OBJECTID")}
                    for f in q100[:5]
                ],
                "az_count": len(az),
                "endpoint": VUV_MAPSERVER,
                "wfs_hook": VUV_WFS,
                "country": "CZ",
            },
            source="VÚV TGM ISVS-VODA · ZaplavUzemi_Q100 + AktivniZony · ArcGIS REST · LIVE",
            disclaimer_kind="warn",
            disclaimer_title="⚠ Orientační podklad — povodně",
            disclaimer_body=(
                "Semafor a vrstvy Q₁₀₀ / aktivní zóny jsou orientační. "
                "Nenahrazují stanovisko vodoprávního úřadu, podrobný hydrotechnický výpočet "
                "ani projektovou dokumentaci. Vždy ověřte aktuální data u VÚV TGM a příslušného úřadu. "
                "Zdroj: HEIS / ISVS-VODA (ne ČHMÚ)."
            ),
            is_mock=False,
            mode=DataMode.live,
            source_status="LIVE",
        )

    def _query_layer(self, layer_id: int, envelope: str) -> list[dict]:
        data = http_get_query(
            f"{VUV_MAPSERVER}/{layer_id}/query",
            {
                "geometry": envelope,
                "geometryType": "esriGeometryEnvelope",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "OBJECTID,NAZ_TOK,REC_NAZ,TOK_ID",
                "returnGeometry": "false",
                "resultRecordCount": "15",
                "f": "pjson",
            },
            timeout=25.0,
        )
        if data.get("error"):
            raise RuntimeError(str(data["error"]))
        return list(data.get("features") or [])

    def _stub_or_demo(self, req: PackRequest) -> LayerResult:
        if is_demo_request(req):
            return LayerResult(
                layer_id=self.layer_id,
                title_cs="Povodně",
                light=TrafficLight.yellow,
                summary_lines=[
                    "Q₁₀₀ (VÚV): okrajový zásah záplavového území",
                    "Aktivní zóna: mimo aktivní zónu",
                    "Doporučení: ověřit u vodoprávního úřadu a projektanta",
                ],
                detail={"q100": "edge", "aktivni_zona": False},
                source="VÚV TGM — Dig. povodňový plán / vrstvy Qₙ · CC BY",
                disclaimer_kind="warn",
                disclaimer_title="⚠ Orientační podklad — povodně",
                disclaimer_body=(
                    "Semafor a vrstvy Q₁₀₀ / aktivní zóny jsou orientační. "
                    "Nenahrazují stanovisko vodoprávního úřadu."
                ),
                is_mock=True,
                mode=DataMode.demo,
                source_status="DEMO",
            )
        return self._stub()

    def _stub(self, reason: str = "VÚV WFS/REST hook pending") -> LayerResult:
        return LayerResult(
            layer_id=self.layer_id,
            title_cs="Povodně",
            light=TrafficLight.yellow,
            summary_lines=[f"Stub: {reason}", "Bez live join — výsledek není vyhodnocen"],
            detail={"wfs": VUV_WFS, "mapserver": VUV_MAPSERVER},
            source="VÚV TGM (stub)",
            disclaimer_kind="warn",
            disclaimer_title="⚠ Orientační podklad — povodně",
            disclaimer_body="Semafor a vrstvy Q₁₀₀ / aktivní zóny jsou orientační.",
            is_mock=True,
            mode=DataMode.stub,
            source_status="STUB",
            blocker=reason,
        )
