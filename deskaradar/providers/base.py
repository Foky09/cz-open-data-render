"""Provider interface — country packs implement fetch() + metadata."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypedDict


class FeedStatus(TypedDict, total=False):
    id: str
    name: str
    url: str
    ok: bool
    http: int | None
    items: int
    error: str | None
    tls_note: str | None
    fetched_at: str
    provider: str
    country: str


# Normalized notice dict (same shape as daily_digest.parse_informace output)
Notice = dict[str, Any]


class Provider(ABC):
    """Ingest adapter for one country / data standard."""

    country: str  # ISO-ish code, e.g. "CZ"
    id: str  # stable provider id, e.g. "cz_ofn"
    name: str
    live: bool = False  # False = stub / not wired yet

    @abstractmethod
    def feeds(self) -> list[dict[str, Any]]:
        """Feed descriptors this provider will attempt (may be empty for stubs)."""

    @abstractmethod
    def fetch_all(self, *, pause_s: float = 0.4) -> tuple[list[FeedStatus], list[Notice]]:
        """Sequential fetch of all feeds; returns (statuses, notices)."""

    def describe(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "country": self.country,
            "live": self.live,
            "feed_count": len(self.feeds()),
        }
