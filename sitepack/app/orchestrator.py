"""Assemble SitePack from providers (live-first, stub fallback)."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.models import DataMode, PackRequest, SitePack
from providers.base import is_demo_request
from providers.flood import FloodProvider
from providers.poddolovani import PoddolovaniProvider
from providers.radon import RadonProvider
from providers.ruian import RuianProvider
from providers.svahy import SvahyProvider
from providers.zoning import ZoningProvider

PRAGUE = ZoneInfo("Europe/Prague")


class ConciergeOrchestrator:
    def __init__(self) -> None:
        self.ruian = RuianProvider()
        self.flood = FloodProvider()
        self.radon = RadonProvider()
        self.poddolovani = PoddolovaniProvider()
        self.svahy = SvahyProvider()
        self.zoning = ZoningProvider()

    def build(self, req: PackRequest) -> SitePack:
        parcel = self.ruian.resolve(req)
        layers = {
            "flood": self.flood.fetch(req, parcel),
            "radon": self.radon.fetch(req, parcel),
            "poddolovani": self.poddolovani.fetch(req, parcel),
            "svahy": self.svahy.fetch(req, parcel),
            "zoning": self.zoning.fetch(req, parcel),
        }
        zoning = layers["zoning"]

        status_table = [
            {
                "layer": "ruian",
                "status": parcel.source_status,
                "mode": parcel.mode.value,
                "blocker": parcel.blocker or "",
            }
        ]
        for key, lr in layers.items():
            status_table.append(
                {
                    "layer": key,
                    "status": lr.source_status,
                    "mode": lr.mode.value,
                    "blocker": lr.blocker or "",
                }
            )

        live_n = sum(1 for r in status_table if r["status"] == "LIVE")
        fb_n = sum(1 for r in status_table if r["status"] == "FALLBACK")
        demo_identity = is_demo_request(req) and not req.force_live_ruian

        if live_n and fb_n:
            mode_label = f"LIVE partial ({live_n} live / {fb_n} fallback)"
        elif live_n:
            mode_label = f"LIVE joins ({live_n} layers)"
        elif demo_identity:
            mode_label = "UKÁZKA / DEMO (no live)"
        else:
            mode_label = "STUB / PARTIAL"

        # Example badge if identity is demo OR any layer still mock
        is_example = demo_identity or any(lr.is_mock for lr in layers.values()) or parcel.is_mock

        now = datetime.now(PRAGUE)
        return SitePack(
            country=(req.country or "CZ").upper(),
            generated_at=now.strftime("%-d. %-m. %Y %H:%M") + " PT",
            mode_label=mode_label,
            is_example=is_example,
            parcel=parcel,
            layers=layers,
            layer_status_table=status_table,
            zoning_class=str(zoning.detail.get("class_label", "")),
            zoning_url=str(zoning.detail.get("url", "https://www.uur.cz/mapovy-portal/")),
            zoning_url_label=str(zoning.detail.get("url_label", "ÚÚR / evidence ÚP")),
        )
