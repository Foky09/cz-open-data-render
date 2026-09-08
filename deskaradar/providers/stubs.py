"""Non-CZ country stubs — plug later (AT Amtstafel / DE Bekanntmachung / IT albo pretore).

These providers are registered but not live: fetch_all returns empty so the
refresh loop can iterate all active_providers() safely.
"""

from __future__ import annotations

from typing import Any

from providers.base import FeedStatus, Notice, Provider


class _StubProvider(Provider):
    live = False

    def feeds(self) -> list[dict[str, Any]]:
        return []

    def fetch_all(self, *, pause_s: float = 0.4) -> tuple[list[FeedStatus], list[Notice]]:
        # Intentionally no network — placeholder for future country packs.
        return [], []


class AtStubProvider(_StubProvider):
    country = "AT"
    id = "at_stub"
    name = "Österreich — stub (Amtstafel / open data TBD)"


class DeStubProvider(_StubProvider):
    country = "DE"
    id = "de_stub"
    name = "Deutschland — stub (Bekanntmachung / open data TBD)"


class ItStubProvider(_StubProvider):
    country = "IT"
    id = "it_stub"
    name = "Italia — stub (albo pretorio / open data TBD)"
