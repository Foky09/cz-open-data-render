"""Pluggable ingest providers for DeskaRadar.

CZ OFN is the only live provider today. AT / DE / IT are stubs so country
packs can plug in later without changing the FastAPI refresh loop.
"""

from __future__ import annotations

from providers.base import FeedStatus, Notice, Provider
from providers.registry import active_providers, get_provider, list_providers

__all__ = [
    "FeedStatus",
    "Notice",
    "Provider",
    "active_providers",
    "get_provider",
    "list_providers",
]
