"""Small HTTP helpers (stdlib urllib) with timeouts — no invented credentials."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

DEFAULT_UA = "SitePackPro-Concierge/0.2 (+https://sitepack.local; open-data joins)"


def http_get(
    url: str,
    *,
    timeout: float = 20.0,
    headers: dict[str, str] | None = None,
    max_bytes: int | None = 8_000_000,
) -> tuple[int, bytes, str]:
    """Return (status, body, final_url). Raises on network failure."""
    hdrs = {"User-Agent": DEFAULT_UA, "Accept": "*/*"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read(max_bytes + 1 if max_bytes else -1) if max_bytes else resp.read()
        if max_bytes and len(raw) > max_bytes:
            raw = raw[:max_bytes]
        return int(resp.status), raw, resp.geturl()


def http_get_json(url: str, *, timeout: float = 20.0) -> Any:
    status, body, _ = http_get(url, timeout=timeout, headers={"Accept": "application/json"})
    if status >= 400:
        raise urllib.error.HTTPError(url, status, f"HTTP {status}", hdrs=None, fp=None)  # type: ignore[arg-type]
    return json.loads(body.decode("utf-8", errors="replace"))


def http_get_query(base: str, params: dict[str, Any], *, timeout: float = 25.0) -> Any:
    qs = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    return http_get_json(f"{base}?{qs}", timeout=timeout)


def download_file(url: str, dest_path, *, timeout: float = 300.0) -> None:
    dest_path = __import__("pathlib").Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest_path.with_suffix(dest_path.suffix + ".part")
    status, body, _ = http_get(url, timeout=timeout, max_bytes=None)
    if status >= 400:
        raise RuntimeError(f"download failed HTTP {status} for {url}")
    tmp.write_bytes(body)
    tmp.replace(dest_path)
