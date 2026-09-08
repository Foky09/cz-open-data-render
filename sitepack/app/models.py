"""Structured layer results for SitePack Pro concierge / SaaS.

CZ ships first. Schema is country-ready (country=CZ default); AT/DE/IT later.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class TrafficLight(str, Enum):
    green = "green"
    yellow = "yellow"
    red = "red"

    @property
    def label_cs(self) -> str:
        return {"green": "zelená", "yellow": "žlutá", "red": "červená"}[self.value]


class DataMode(str, Enum):
    demo = "demo"
    stub = "stub"
    live = "live"
    fallback = "fallback"  # live attempted, stub used

    @property
    def status_badge(self) -> str:
        """Internal / live-joins badge (includes DEMO)."""
        return {
            "live": "LIVE",
            "stub": "STUB",
            "fallback": "FALLBACK",
            "demo": "DEMO",
        }[self.value]

    @property
    def badge(self) -> str:
        """Product UI badge: LIVE | STUB | FALLBACK (demo → FALLBACK)."""
        return {
            "live": "LIVE",
            "stub": "STUB",
            "fallback": "FALLBACK",
            "demo": "FALLBACK",
        }[self.value]

    @property
    def label_cs(self) -> str:
        return {
            "live": "Živá data",
            "stub": "Orientační",
            "demo": "Ukázka",
            "fallback": "Orientační",
        }[self.value]

    @property
    def human_badge_cs(self) -> str:
        return self.label_cs


class LayerResult(BaseModel):
    layer_id: str
    title_cs: str
    light: TrafficLight
    summary_lines: list[str] = Field(default_factory=list)
    detail: dict[str, Any] = Field(default_factory=dict)
    source: str = ""
    disclaimer_kind: Optional[str] = None
    disclaimer_title: Optional[str] = None
    disclaimer_body: Optional[str] = None
    is_mock: bool = True
    mode: DataMode = DataMode.demo
    source_status: str = "STUB"  # LIVE | STUB | FALLBACK | DEMO
    blocker: Optional[str] = None

    def ui_badge(self) -> str:
        """Prefer explicit source_status when LIVE/STUB/FALLBACK; else mode.badge."""
        ss = (self.source_status or "").upper()
        if ss in {"LIVE", "STUB", "FALLBACK"}:
            return ss
        if ss == "DEMO":
            return "FALLBACK"
        return self.mode.badge

    def human_badge_cs(self) -> str:
        b = self.ui_badge()
        return {"LIVE": "Živá data", "STUB": "Orientační", "FALLBACK": "Ukázka"}.get(b, b)


class ParcelIdentity(BaseModel):
    ruian_id: Optional[str] = None
    ku_code: Optional[str] = None
    ku_name: str = ""
    parcel_number: str = ""
    area_m2: Optional[float] = None
    parcel_type: str = ""
    obec: str = ""
    okres: str = ""
    geometry_wkt: Optional[str] = None
    geometry_note: str = "Mini mapa — placeholder"
    is_mock: bool = True
    mode: DataMode = DataMode.demo
    source_status: str = "DEMO"
    lookup_note: str = ""
    blocker: Optional[str] = None

    def ui_badge(self) -> str:
        ss = (self.source_status or "").upper()
        if ss in {"LIVE", "STUB", "FALLBACK"}:
            return ss
        if ss == "DEMO":
            return "FALLBACK"
        return self.mode.badge

    def human_badge_cs(self) -> str:
        b = self.ui_badge()
        return {"LIVE": "Živá data", "STUB": "Orientační", "FALLBACK": "Ukázka"}.get(b, b)


class PackRequest(BaseModel):
    country: str = "CZ"  # AT/DE/IT later — UI stays CZ-first
    ruian_id: Optional[str] = None
    ku: Optional[str] = None
    parcel_number: Optional[str] = None
    demo: bool = False
    force_live_ruian: bool = False
    prefer_live: bool = True  # try live joins; stub only as fallback


class SitePack(BaseModel):
    country: str = "CZ"
    generated_at: str
    template_version: str = "1.2-saas-cz"
    mode_label: str
    is_example: bool = True
    parcel: ParcelIdentity
    layers: dict[str, LayerResult]
    layer_status_table: list[dict[str, str]] = Field(default_factory=list)
    zoning_class: str = ""
    zoning_url: str = "https://www.uur.cz/mapovy-portal/"
    zoning_url_label: str = "ÚÚR mapový portál / evidence ÚP"
    sources_blurb: str = (
        "ČÚZK / RÚIAN (identita parcely, CC BY) · "
        "VÚV TGM HEIS (Qₙ + aktivní zóny, open WFS/REST) · "
        "ČGS open data (radon 1:50k, poddolování, svahové deformace, CC BY)."
    )
    no_ownership_note: str = (
        "Neobsahuje a neslibuje údaje o vlastnictví nemovitostí (katastr nemovitostí)."
    )

    def layer_badges_summary(self) -> dict[str, int]:
        counts = {"LIVE": 0, "STUB": 0, "FALLBACK": 0}
        counts[self.parcel.ui_badge()] = counts.get(self.parcel.ui_badge(), 0) + 1
        for layer in self.layers.values():
            b = layer.ui_badge()
            counts[b] = counts.get(b, 0) + 1
        return counts
