"""Czech Republic — OFN úřední deska JSON-LD (live).

Reuses parent daily_digest.FEEDS / fetch_feed so the Day-1 feed list stays
the single source of truth. No eDesky HTML scrape.
"""

from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from providers.base import FeedStatus, Notice, Provider

# providers/ -> app dir (deskaradar/) where daily_digest.py lives
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from daily_digest import (  # noqa: E402
    FEEDS,
    PAUSE_BETWEEN_FEEDS_S,
    fetch_feed,
)

TZ = ZoneInfo("Europe/Prague")


class CzOfnProvider(Provider):
    country = "CZ"
    id = "cz_ofn"
    name = "Česko — OFN úřední deska"
    live = True

    def feeds(self) -> list[dict[str, Any]]:
        # Shallow copy so callers cannot mutate the shared FEEDS list
        return [dict(f) for f in FEEDS]

    def fetch_all(self, *, pause_s: float | None = None) -> tuple[list[FeedStatus], list[Notice]]:
        pause = PAUSE_BETWEEN_FEEDS_S if pause_s is None else pause_s
        statuses: list[FeedStatus] = []
        notices: list[Notice] = []
        for i, feed in enumerate(self.feeds()):
            if i:
                time.sleep(pause)
            status, items = fetch_feed(feed)
            enriched: FeedStatus = {
                **status,  # type: ignore[misc]
                "fetched_at": datetime.now(TZ).isoformat(timespec="seconds"),
                "provider": self.id,
                "country": self.country,
            }
            statuses.append(enriched)
            if status.get("ok"):
                notices.extend(items)
        return statuses, notices
