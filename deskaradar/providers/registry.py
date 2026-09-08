"""Provider registry — CZ live; AT/DE/IT stubs registered but inactive for fetch."""

from __future__ import annotations

from providers.base import Provider
from providers.cz_ofn import CzOfnProvider
from providers.stubs import AtStubProvider, DeStubProvider, ItStubProvider

_PROVIDERS: dict[str, Provider] = {}


def _ensure() -> None:
    if _PROVIDERS:
        return
    for p in (
        CzOfnProvider(),
        AtStubProvider(),
        DeStubProvider(),
        ItStubProvider(),
    ):
        _PROVIDERS[p.id] = p


def list_providers() -> list[Provider]:
    _ensure()
    return list(_PROVIDERS.values())


def get_provider(provider_id: str) -> Provider | None:
    _ensure()
    return _PROVIDERS.get(provider_id)


def active_providers(*, live_only: bool = True) -> list[Provider]:
    """Providers used by the refresh loop. Default: live only (CZ OFN)."""
    _ensure()
    if live_only:
        return [p for p in _PROVIDERS.values() if p.live]
    return list(_PROVIDERS.values())
