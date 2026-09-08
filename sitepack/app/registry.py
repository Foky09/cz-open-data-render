"""Pluggable layer registry — country-ready, CZ registered now; AT/DE/IT later.

Does not change CZ UX. Orchestrator picks providers by country code.
"""

from __future__ import annotations

from typing import Callable, Protocol

from app.models import LayerResult, ParcelIdentity, PackRequest


class LayerProvider(Protocol):
    layer_id: str

    def fetch(self, req: PackRequest, parcel: ParcelIdentity) -> LayerResult: ...


class IdentityProvider(Protocol):
    layer_id: str

    def resolve(self, req: PackRequest) -> ParcelIdentity: ...


# country -> ordered list of (layer_id, factory)
_LAYER_REGISTRY: dict[str, list[tuple[str, Callable[[], LayerProvider]]]] = {}
_IDENTITY_REGISTRY: dict[str, Callable[[], IdentityProvider]] = {}


def register_layers(country: str, entries: list[tuple[str, Callable[[], LayerProvider]]]) -> None:
    _LAYER_REGISTRY[country.upper()] = list(entries)


def register_identity(country: str, factory: Callable[[], IdentityProvider]) -> None:
    _IDENTITY_REGISTRY[country.upper()] = factory


def get_identity_factory(country: str = "CZ") -> Callable[[], IdentityProvider]:
    key = (country or "CZ").upper()
    if key not in _IDENTITY_REGISTRY:
        raise KeyError(f"No identity provider for country={key} (CZ ships first)")
    return _IDENTITY_REGISTRY[key]


def get_layer_entries(country: str = "CZ") -> list[tuple[str, Callable[[], LayerProvider]]]:
    key = (country or "CZ").upper()
    if key not in _LAYER_REGISTRY:
        raise KeyError(f"No layer registry for country={key} (CZ ships first)")
    return _LAYER_REGISTRY[key]


def supported_countries() -> list[str]:
    return sorted(_LAYER_REGISTRY.keys())


def _register_cz() -> None:
    from providers.flood import FloodProvider
    from providers.poddolovani import PoddolovaniProvider
    from providers.radon import RadonProvider
    from providers.ruian import RuianProvider
    from providers.svahy import SvahyProvider
    from providers.zoning import ZoningProvider

    register_identity("CZ", RuianProvider)
    register_layers(
        "CZ",
        [
            ("flood", FloodProvider),
            ("radon", RadonProvider),
            ("poddolovani", PoddolovaniProvider),
            ("svahy", SvahyProvider),
            ("zoning", ZoningProvider),
        ],
    )


_register_cz()
