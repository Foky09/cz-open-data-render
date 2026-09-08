"""Provider protocol and shared helpers (CZ-first; country-pluggable hook)."""

from __future__ import annotations

from typing import Protocol

from app.models import DataMode, LayerResult, ParcelIdentity, PackRequest

# Default market — keep lookups country-aware where cheap; no multi-country work yet.
DEFAULT_COUNTRY = "CZ"


class LayerProvider(Protocol):
    layer_id: str

    def fetch(self, req: PackRequest, parcel: ParcelIdentity) -> LayerResult: ...


DEMO_RUAIN_ID = "680123456"
DEMO_KU = "Brno-město"
DEMO_PARCEL = "1234/5"


def country_code(req: PackRequest | None = None, parcel: ParcelIdentity | None = None) -> str:
    """Cheap pluggable country hook (default CZ)."""
    if req is not None:
        cc = getattr(req, "country", None)
        if isinstance(cc, str) and cc.strip():
            return cc.strip().upper()
    if parcel is not None:
        detail = getattr(parcel, "detail", None)
        if isinstance(detail, dict) and detail.get("country"):
            return str(detail["country"]).strip().upper()
    return DEFAULT_COUNTRY


def is_demo_request(req: PackRequest) -> bool:
    if req.demo:
        return True
    if req.ruian_id and req.ruian_id.strip() == DEMO_RUAIN_ID:
        return True
    if (
        req.ku
        and req.parcel_number
        and req.ku.strip().lower() in {DEMO_KU.lower(), "610952", "brno-mesto", "brno město"}
        and req.parcel_number.strip().replace(" ", "") == DEMO_PARCEL
    ):
        return True
    if not req.ruian_id and not (req.ku and req.parcel_number):
        return True
    return False


def mock_mark(text: str) -> str:
    return f'{text} <span class="example-mark">UKÁZKA</span>'


def status_for(mode: DataMode) -> str:
    return mode.status_badge
