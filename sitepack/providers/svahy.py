"""ČGS svahové deformace — LIVE PiP (plochy) + nearest body; stub fallback."""

from __future__ import annotations

from app.models import DataMode, LayerResult, PackRequest, ParcelIdentity, TrafficLight

from .base import country_code, is_demo_request
from .geo_cache import parcel_polygon_from_identity, query_intersects, query_nearest_within


class SvahyProvider:
    layer_id = "svahy"

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
                fb.blocker = f"live PiP failed: {exc!s}"
                fb.summary_lines = [f"FALLBACK po chybě live: {exc!s}", *fb.summary_lines]
                fb.is_mock = True
                return fb

        return self._stub_or_demo(req)

    def _live(self, parcel: ParcelIdentity) -> LayerResult:
        geom = parcel_polygon_from_identity(parcel)
        if geom is None:
            raise RuntimeError("parcel geometry missing (need geometry_wkt for PiP)")

        poly_hits = query_intersects("sesuvy_plochy", geom, limit=10)
        near = query_nearest_within("sesuvy_body", geom, max_m=500, limit=8)

        hit_poly = bool(poly_hits)
        nearest_m = near[0]["distance_m"] if near else None
        hit_near = nearest_m is not None and nearest_m <= 150

        if hit_poly:
            light = TrafficLight.red
            akt = poly_hits[0].get("aktivita") or "?"
            lines = [
                f"Zásah: Ano — průnik s plochou svahové deformace ({len(poly_hits)})",
                f"Aktivita (1. hit): {akt}; obec: {poly_hits[0].get('obec') or '—'}",
            ]
        elif hit_near:
            light = TrafficLight.yellow
            lines = [
                "Zásah: Ano — blízkost",
                f"Do {nearest_m:.0f} m evidovaný bod svahové deformace "
                f"({near[0].get('nazev') or '?'}, {near[0].get('aktivita') or '?'})",
            ]
        elif near:
            light = TrafficLight.green
            lines = [
                "Zásah: Ne (bez průniku plochy)",
                f"Nejbližší bod: {nearest_m:.0f} m ({near[0].get('obec') or '—'}) — mimo 150 m práh",
            ]
        else:
            light = TrafficLight.green
            lines = [
                "Zásah: Ne",
                "Bez záznamu svahových deformací v okolí 500 m",
            ]

        return LayerResult(
            layer_id=self.layer_id,
            title_cs="Svahové deformace",
            light=light,
            summary_lines=lines,
            detail={
                "hit": bool(hit_poly or hit_near),
                "poly_hits": poly_hits[:5],
                "nearest": near[:5],
                "distance_m": nearest_m,
                "country": "CZ",
            },
            source="ČGS open data — svahove_deformace.zip (plochy+body) · CC BY · LIVE PiP",
            is_mock=False,
            mode=DataMode.live,
            source_status="LIVE",
        )

    def _stub_or_demo(self, req: PackRequest) -> LayerResult:
        if is_demo_request(req):
            return LayerResult(
                layer_id=self.layer_id,
                title_cs="Svahové deformace",
                light=TrafficLight.yellow,
                summary_lines=[
                    "Zásah: Ano — blízkost",
                    "Do 150 m evidovaná svahová deformace (stabilizovaná / dořešit)",
                ],
                detail={"hit": True, "distance_m": 150, "status": "stabilizovaná"},
                source="Česká geologická služba (ČGS) · CC BY",
                is_mock=True,
                mode=DataMode.demo,
                source_status="DEMO",
            )
        return self._stub()

    def _stub(self, reason: str = "hook pending") -> LayerResult:
        return LayerResult(
            layer_id=self.layer_id,
            title_cs="Svahové deformace",
            light=TrafficLight.yellow,
            summary_lines=[f"Stub: {reason}"],
            source="ČGS (stub)",
            is_mock=True,
            mode=DataMode.stub,
            source_status="STUB",
            blocker=reason,
        )
