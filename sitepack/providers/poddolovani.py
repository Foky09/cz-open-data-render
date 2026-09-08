"""ČGS poddolovaná území — LIVE PiP from open GeoJSON zip; stub fallback."""

from __future__ import annotations

from app.models import DataMode, LayerResult, PackRequest, ParcelIdentity, TrafficLight

from .base import country_code, is_demo_request
from .geo_cache import parcel_polygon_from_identity, query_intersects


class PoddolovaniProvider:
    layer_id = "poddolovani"

    def fetch(self, req: PackRequest, parcel: ParcelIdentity) -> LayerResult:
        cc = country_code(req, parcel)
        if cc != "CZ":
            return self._stub(req, reason=f"country={cc} not implemented (CZ-only v1)")

        if req.prefer_live:
            try:
                return self._live(req, parcel)
            except Exception as exc:  # noqa: BLE001 — soft fallback
                fb = self._stub_or_demo(req)
                fb.mode = DataMode.fallback
                fb.source_status = "FALLBACK"
                fb.blocker = f"live PiP failed: {exc!s}"
                fb.summary_lines = [f"FALLBACK po chybě live: {exc!s}", *fb.summary_lines]
                fb.is_mock = True
                return fb

        return self._stub_or_demo(req)

    def _live(self, req: PackRequest, parcel: ParcelIdentity) -> LayerResult:
        geom = parcel_polygon_from_identity(parcel)
        if geom is None:
            raise RuntimeError("parcel geometry missing (need geometry_wkt for PiP)")

        hits = query_intersects("poddolovani", geom, limit=15)
        # also check small buffer ~50 m for edge adjacency
        if not hits:
            from .geo_cache import deg_buffer_m

            buf = geom.buffer(deg_buffer_m(50, lat=geom.centroid.y))
            hits = query_intersects("poddolovani", buf, limit=15)

        hit = bool(hits)
        names = [h.get("nazev") or h.get("klic") or "?" for h in hits[:5]]
        if hit:
            light = TrafficLight.red if len(hits) >= 1 else TrafficLight.yellow
            lines = [
                f"Zásah: Ano ({len(hits)} záznamů v evidenci / 50 m buffer)",
                "Lokality: " + ", ".join(str(n) for n in names),
                "Doporučení: ověřit u ČGS / báňského úřadu před záměrem",
            ]
        else:
            light = TrafficLight.green
            lines = [
                "Zásah: Ne",
                "Bez záznamu v evidenci poddolovaných území (parcel + 50 m)",
            ]

        return LayerResult(
            layer_id=self.layer_id,
            title_cs="Poddolování",
            light=light,
            summary_lines=lines,
            detail={
                "hit": hit,
                "count": len(hits),
                "hits": hits[:10],
                "buffer_m": 50,
                "country": "CZ",
            },
            source="ČGS open data — poddolovane_uzemi.zip (od.geology.cz) · CC BY · LIVE PiP",
            is_mock=False,
            mode=DataMode.live,
            source_status="LIVE",
        )

    def _stub_or_demo(self, req: PackRequest) -> LayerResult:
        if is_demo_request(req):
            return self._demo()
        return self._stub(req)

    def _demo(self) -> LayerResult:
        return LayerResult(
            layer_id=self.layer_id,
            title_cs="Poddolování",
            light=TrafficLight.green,
            summary_lines=[
                "Zásah: Ne",
                "Bez záznamu v evidenci poddolovaných území v okolí 500 m",
            ],
            detail={"hit": False, "buffer_m": 500},
            source="Česká geologická služba (ČGS) · CC BY",
            is_mock=True,
            mode=DataMode.demo,
            source_status="DEMO",
        )

    def _stub(self, req: PackRequest, reason: str = "hook pending") -> LayerResult:
        return LayerResult(
            layer_id=self.layer_id,
            title_cs="Poddolování",
            light=TrafficLight.yellow,
            summary_lines=[f"Stub: {reason}", "Napojte ČGS poddolování PiP"],
            source="ČGS (stub)",
            is_mock=True,
            mode=DataMode.stub,
            source_status="STUB",
            blocker=reason,
        )
