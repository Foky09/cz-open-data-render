"""Zoning light — NGÚP / ÚÚR portal link by obec (no full ÚP vector)."""

from __future__ import annotations

import urllib.parse

from app.models import DataMode, LayerResult, PackRequest, ParcelIdentity, TrafficLight

from .base import country_code, is_demo_request

# Light deep-links (no nationwide vector). uzemniplanovani.gov.cz often blocks bots → ÚÚR portals.
UUR_MAP = "https://www.uur.cz/mapovy-portal/"
UUR_EVIDENCE = "https://www.uur.cz/uzemni-planovani/evidence-uzemne-planovaci-cinnosti/"
PORTAL_UUR = "https://portal.uur.cz/"


class ZoningProvider:
    layer_id = "zoning"

    def fetch(self, req: PackRequest, parcel: ParcelIdentity) -> LayerResult:
        cc = country_code(req, parcel)
        if cc != "CZ":
            return self._stub(parcel, reason=f"country={cc} not implemented (CZ-only v1)")

        if req.prefer_live:
            try:
                return self._live(req, parcel)
            except Exception as exc:  # noqa: BLE001
                fb = self._stub_or_demo(req, parcel)
                fb.mode = DataMode.fallback
                fb.source_status = "FALLBACK"
                fb.blocker = str(exc)
                fb.is_mock = True
                return fb
        return self._stub_or_demo(req, parcel)

    def _live(self, req: PackRequest, parcel: ParcelIdentity) -> LayerResult:
        obec = (parcel.obec or req.ku or "").strip() or "—"
        # Search-style link on ÚÚR evidence + map portal (honest light layer)
        q = urllib.parse.quote(obec)
        url = f"{UUR_EVIDENCE}?q={q}"
        label = f"Evidence ÚP · obec {obec}"

        # Demo identity still fictional class — live only resolves portal URL
        class_label = "nevyhodnoceno (light — bez vektoru ÚP)"
        if is_demo_request(req):
            class_label = "plocha bydlení / smíšená obytná (orientační DEMO label)"

        return LayerResult(
            layer_id=self.layer_id,
            title_cs="Územní plán",
            light=TrafficLight.yellow,
            summary_lines=[
                f"Orientační třída využití: {class_label}",
                f"Odkaz: {label}",
                f"Mapový portál ÚÚR: {UUR_MAP}",
            ],
            detail={
                "class_label": class_label,
                "url": url,
                "url_label": label,
                "map_portal": UUR_MAP,
                "info_portal": PORTAL_UUR,
                "obec": obec,
                "country": "CZ",
                "note": "Light only — no nationwide ÚP polygon join",
            },
            source="ÚÚR mapový portál / evidence ÚP (NGÚP-light) · LIVE link",
            disclaimer_kind="info",
            disclaimer_title="ℹ Územní plán (orientační)",
            disclaimer_body=(
                "Tento výstup nenahrazuje územní rozhodnutí, územní souhlas ani závazné stanovisko. "
                "Semafor „žlutá“ znamená: ověřte aktuální ÚP / změny ÚP a regulativy u příslušného "
                "úřadu územního plánování. SitePack Pro neposkytuje právní výklad regulativů. "
                "Není napojen celostátní vektor ÚP."
            ),
            is_mock=is_demo_request(req),
            mode=DataMode.live,
            source_status="LIVE",
        )

    def _stub_or_demo(self, req: PackRequest, parcel: ParcelIdentity) -> LayerResult:
        if is_demo_request(req):
            return LayerResult(
                layer_id=self.layer_id,
                title_cs="Územní plán",
                light=TrafficLight.yellow,
                summary_lines=[
                    "Orientační třída využití: plocha bydlení / smíšená obytná",
                    "Odkaz: NGÚP / ÚP obce (placeholder)",
                ],
                detail={
                    "class_label": "plocha bydlení / smíšená obytná",
                    "url": UUR_MAP,
                    "url_label": "ÚÚR mapový portál",
                },
                source="NGÚP / ÚP obce · light vrstva",
                disclaimer_kind="info",
                disclaimer_title="ℹ Územní plán (orientační)",
                disclaimer_body=(
                    "Tento výstup nenahrazuje územní rozhodnutí, územní souhlas ani závazné stanovisko."
                ),
                is_mock=True,
                mode=DataMode.demo,
                source_status="DEMO",
            )
        return self._stub(parcel)

    def _stub(self, parcel: ParcelIdentity, reason: str = "NGÚP link pending") -> LayerResult:
        return LayerResult(
            layer_id=self.layer_id,
            title_cs="Územní plán",
            light=TrafficLight.yellow,
            summary_lines=[f"Stub: {reason}"],
            detail={
                "class_label": "nevyhodnoceno (stub)",
                "url": UUR_MAP,
                "url_label": "ÚÚR mapový portál",
            },
            source="NGÚP (stub)",
            disclaimer_kind="info",
            disclaimer_title="ℹ Územní plán (orientační)",
            disclaimer_body="Tento výstup nenahrazuje územní rozhodnutí ani závazné stanovisko.",
            is_mock=True,
            mode=DataMode.stub,
            source_status="STUB",
            blocker=reason,
        )
