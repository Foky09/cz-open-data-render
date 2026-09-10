#!/usr/bin/env python3
"""DeskaRadar web app — live JMK OFN leads (FastAPI + browser UI).

Reuses parent daily_digest.py FEEDS / fetch / classify; no eDesky scrape.
Login is a demo stub (cookie session). Alert prefs stored in SQLite.
"""

from __future__ import annotations

import json
import secrets
import sqlite3
import sys
import threading
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import Cookie, FastAPI, Query, Request, Response
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Monorepo: classify_notice + daily_digest live beside main.py
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from daily_digest import classify_leads  # noqa: E402

from providers import active_providers, list_providers  # noqa: E402

TZ = ZoneInfo("Europe/Prague")
CACHE_TTL_S = 20 * 60
FORCE_REFRESH_COOLDOWN_S = 60
# Background re-warm interval: only hits network when cache is stale (_cache_fresh gate).
REWARM_INTERVAL_S = 5 * 60
# Soft UI auto-refresh of leads list (uses /api/leads → cache; does not force feeds).
UI_SOFT_REFRESH_S = 3 * 60
APP_DIR = Path(__file__).resolve().parent
STATIC = APP_DIR / "static"
DATA_DIR = APP_DIR / "data"
DB_PATH = DATA_DIR / "deskaradar.db"
FIXTURE_LEADS_PATH = DATA_DIR / "fixtures" / "leads-fixture.json"
ATTRIBUTION_CS = (
    "Zdroj: úřední desky obcí JMK (otevřená data) · Brno CC BY 4.0 (MMB)."
)


def _load_fixture_payload() -> dict[str, Any]:
    """CI / offline sample leads — clearly labeled fixture."""
    if FIXTURE_LEADS_PATH.exists():
        return json.loads(FIXTURE_LEADS_PATH.read_text(encoding="utf-8"))
    return {
        "meta": {"sampleLabel": "Ukázková data (inline fixture)", "exportDate": "2026-09-09"},
        "feeds": [],
        "leads": [],
    }


def _apply_fixture_cache() -> dict[str, Any]:
    """Load fixture into cache; sets data_mode=fixture."""
    global _refreshing
    payload = _load_fixture_payload()
    feeds = payload.get("feeds") or []
    leads_raw = payload.get("leads") or []
    statuses = [
        {
            "id": f.get("id"),
            "name": f.get("name"),
            "url": "",
            "ok": bool(f.get("ok", True)),
            "http": f.get("http"),
            "items": f.get("items"),
            "error": None,
            "tls_note": "fixture",
            "fetched_at": datetime.now(TZ).isoformat(timespec="seconds"),
            "provider": "fixture",
            "country": "CZ",
        }
        for f in feeds
    ]
    leads = []
    for L in leads_raw:
        leads.append(
            {
                "id": L.get("id"),
                "title": L.get("title"),
                "municipality": L.get("municipality"),
                "category": L.get("category"),
                "confidence": L.get("confidence"),
                "posted": L.get("posted"),
                "url": L.get("url"),
                "label": "stavebni_zamer",
            }
        )
    with _lock:
        _cache["fetched_at"] = _now_utc()
        _cache["statuses"] = statuses
        _cache["leads"] = leads
        _cache["notices_count"] = len(leads)
        _cache["error"] = None
        _cache["data_mode"] = "fixture"
        _cache["sample_label"] = (payload.get("meta") or {}).get(
            "sampleLabel", "Ukázková data (fixture)"
        )
        _refreshing = False
    return _snapshot()


# Demo auth — any email + password "demo" OR hardcoded pair
DEMO_EMAIL = "demo@deskaradar.local"
DEMO_PASSWORD = "demo"
SESSION_COOKIE = "dr_session"
SESSION_TTL_S = 7 * 24 * 3600

app = FastAPI(title="DeskaRadar", version="0.3.0")
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")

_lock = threading.RLock()  # reentrant: _refresh_feeds early-returns call _snapshot under the same lock
_sessions: dict[str, dict[str, Any]] = {}
_cache: dict[str, Any] = {
    "fetched_at": None,
    "statuses": [],
    "leads": [],
    "notices_count": 0,
    "error": None,
    "data_mode": None,  # "fixture" | "live"
    "sample_label": None,
}
_refreshing = False
_last_force: float = 0.0


# --- SQLite alert prefs ---


def _db() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    with _db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alert_prefs (
                user_key TEXT PRIMARY KEY,
                high_only INTEGER NOT NULL DEFAULT 1,
                municipalities TEXT NOT NULL DEFAULT '[]',
                email TEXT NOT NULL DEFAULT '',
                enabled INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _default_prefs() -> dict[str, Any]:
    return {
        "high_only": True,
        "municipalities": [],
        "email": "",
        "enabled": True,
    }


def _load_prefs(user_key: str) -> dict[str, Any]:
    with _db() as conn:
        row = conn.execute(
            "SELECT high_only, municipalities, email, enabled FROM alert_prefs WHERE user_key=?",
            (user_key,),
        ).fetchone()
    if not row:
        return _default_prefs()
    try:
        munis = json.loads(row["municipalities"] or "[]")
    except json.JSONDecodeError:
        munis = []
    return {
        "high_only": bool(row["high_only"]),
        "municipalities": munis if isinstance(munis, list) else [],
        "email": row["email"] or "",
        "enabled": bool(row["enabled"]),
    }


def _save_prefs(user_key: str, prefs: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(TZ).isoformat(timespec="seconds")
    munis = prefs.get("municipalities") or []
    if not isinstance(munis, list):
        munis = []
    payload = {
        "high_only": bool(prefs.get("high_only", True)),
        "municipalities": [str(m) for m in munis],
        "email": str(prefs.get("email") or "")[:200],
        "enabled": bool(prefs.get("enabled", True)),
    }
    with _db() as conn:
        conn.execute(
            """
            INSERT INTO alert_prefs (user_key, high_only, municipalities, email, enabled, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_key) DO UPDATE SET
              high_only=excluded.high_only,
              municipalities=excluded.municipalities,
              email=excluded.email,
              enabled=excluded.enabled,
              updated_at=excluded.updated_at
            """,
            (
                user_key,
                1 if payload["high_only"] else 0,
                json.dumps(payload["municipalities"], ensure_ascii=False),
                payload["email"],
                1 if payload["enabled"] else 0,
                now,
            ),
        )
        conn.commit()
    return payload


# --- session helpers ---


def _user_from_cookie(session: str | None) -> dict[str, Any] | None:
    if not session:
        return None
    with _lock:
        data = _sessions.get(session)
        if not data:
            return None
        if data["expires"] < time.time():
            _sessions.pop(session, None)
            return None
        return data


def _require_user(session: str | None) -> dict[str, Any] | None:
    return _user_from_cookie(session)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _cache_age_s() -> float | None:
    fa = _cache.get("fetched_at")
    if not fa:
        return None
    return (_now_utc() - fa).total_seconds()


def _cache_fresh() -> bool:
    age = _cache_age_s()
    return age is not None and age < CACHE_TTL_S


def _refresh_feeds(*, force: bool = False) -> dict[str, Any]:
    global _refreshing, _last_force

    with _lock:
        if _cache_fresh() and not force:
            return _snapshot()
        if force:
            now_m = time.monotonic()
            if now_m - _last_force < FORCE_REFRESH_COOLDOWN_S and _cache.get("fetched_at"):
                return _snapshot()
            _last_force = now_m
        if _refreshing:
            return _snapshot()
        _refreshing = True

    statuses: list[dict[str, Any]] = []
    all_notices: list[dict[str, Any]] = []

    try:
        # Live providers only (CZ OFN today). Stubs (AT/DE/IT) stay registered
        # but inactive so country packs can plug later without breaking FEEDS reuse.
        for provider in active_providers(live_only=True):
            p_statuses, p_notices = provider.fetch_all()
            statuses.extend(p_statuses)
            all_notices.extend(p_notices)
        leads = classify_leads(all_notices)
        with _lock:
            _cache["fetched_at"] = _now_utc()
            _cache["statuses"] = statuses
            _cache["leads"] = leads
            _cache["notices_count"] = len(all_notices)
            _cache["error"] = None
            _cache["data_mode"] = "live"
            # Platform contract: omit sample_label on real live ingest
            _cache["sample_label"] = None
    except Exception as exc:  # noqa: BLE001
        with _lock:
            _cache["error"] = f"{type(exc).__name__}: {exc}"
            if not _cache.get("fetched_at"):
                _cache["statuses"] = statuses
                _cache["leads"] = []
                _cache["notices_count"] = 0
                _cache["fetched_at"] = _now_utc()
                _cache["data_mode"] = None
        # Offline / network blocker → serve clearly labeled fixture
        if not _cache.get("leads"):
            try:
                return _apply_fixture_cache()
            except Exception:
                pass
    finally:
        with _lock:
            _refreshing = False

    return _snapshot()



def _meta_fields(snap: dict[str, Any]) -> dict[str, Any]:
    """data_mode + attribution; sample_label only when fixture/ukázka."""
    out: dict[str, Any] = {
        "data_mode": snap.get("data_mode"),
        "attribution": snap.get("attribution"),
    }
    sl = snap.get("sample_label")
    if sl:
        out["sample_label"] = sl
    return out

def _snapshot() -> dict[str, Any]:
    with _lock:
        fa = _cache.get("fetched_at")
        out: dict[str, Any] = {
            "fetched_at": fa.isoformat() if fa else None,
            "fetched_at_pt": fa.astimezone(TZ).strftime("%Y-%m-%d %H:%M:%S %Z") if fa else None,
            "cache_ttl_s": CACHE_TTL_S,
            "cache_age_s": round(_cache_age_s() or 0, 1) if fa else None,
            "fresh": _cache_fresh(),
            "notices_count": _cache.get("notices_count", 0),
            "statuses": list(_cache.get("statuses") or []),
            "leads": list(_cache.get("leads") or []),
            "error": _cache.get("error"),
            "refreshing": _refreshing,
            "rewarm_interval_s": REWARM_INTERVAL_S,
            "ui_soft_refresh_s": UI_SOFT_REFRESH_S,
            "providers": [p.describe() for p in list_providers()],
            "data_mode": _cache.get("data_mode"),
            "attribution": ATTRIBUTION_CS,
        }
        # Fixture/ukázka only — omit key entirely on live
        sl = _cache.get("sample_label")
        if sl:
            out["sample_label"] = sl
        return out



def _ensure_data(*, force: bool = False) -> dict[str, Any]:
    if force or not _cache_fresh():
        return _refresh_feeds(force=force)
    return _snapshot()


def date_from_iso(s: str) -> date:
    return date.fromisoformat(s[:10])


def _filter_leads(
    leads: list[dict[str, Any]],
    *,
    confidence: str | None = None,
    municipality: str | None = None,
    category: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    query: str | None = None,
) -> list[dict[str, Any]]:
    out = leads
    if confidence:
        wanted = {c.strip().lower() for c in confidence.split(",") if c.strip()}
        out = [L for L in out if (L.get("confidence") or "").lower() in wanted]
    if municipality:
        m = municipality.strip().lower()
        out = [L for L in out if m in (L.get("municipality") or "").lower()]
    if category:
        c = category.strip().lower()
        out = [L for L in out if (L.get("category") or "").lower() == c]
    if query:
        q = query.strip().lower()
        if q:
            def _hit(L: dict[str, Any]) -> bool:
                hay = " ".join(
                    [
                        str(L.get("title_redacted") or ""),
                        str(L.get("municipality") or ""),
                        str(L.get("category") or ""),
                        " ".join(L.get("matched_terms") or []),
                    ]
                ).lower()
                return q in hay
            out = [L for L in out if _hit(L)]
    df = date_from_iso(date_from) if date_from else None
    dt = date_from_iso(date_to) if date_to else None
    if df or dt:
        filtered: list[dict[str, Any]] = []
        for L in out:
            pub = L.get("published_at")
            if not pub:
                continue
            try:
                d = date_from_iso(pub)
            except ValueError:
                continue
            if df and d < df:
                continue
            if dt and d > dt:
                continue
            filtered.append(L)
        out = filtered
    return out


def _lead_public(L: dict[str, Any]) -> dict[str, Any]:
    return {
        "municipality": L.get("municipality"),
        "published_at": L.get("published_at"),
        "category": L.get("category"),
        "confidence": L.get("confidence"),
        "confidence_score": L.get("confidence_score"),
        "title_redacted": L.get("title_redacted"),
        "url": L.get("url") or "",
        "matched_terms": L.get("matched_terms") or [],
        "flags": L.get("flags") or {},
    }


def _alerts_for_prefs(leads: list[dict[str, Any]], prefs: dict[str, Any]) -> list[dict[str, Any]]:
    if not prefs.get("enabled", True):
        return []
    cutoff = (datetime.now(TZ) - timedelta(hours=24)).date()
    today = datetime.now(TZ).date()
    munis = [m.lower() for m in (prefs.get("municipalities") or [])]
    high_only = bool(prefs.get("high_only", True))
    out: list[dict[str, Any]] = []
    for L in leads:
        conf = L.get("confidence")
        if high_only and conf != "high":
            continue
        if not high_only and conf not in ("high", "medium"):
            continue
        if munis:
            name = (L.get("municipality") or "").lower()
            if not any(m in name for m in munis):
                continue
        pub = L.get("published_at")
        if not pub:
            continue
        try:
            d = date_from_iso(pub)
        except ValueError:
            continue
        if cutoff <= d <= today:
            out.append(L)
    return out


def _auth_error() -> JSONResponse:
    return JSONResponse({"error": "unauthorized", "login": "/login"}, status_code=401)


# --- pages ---


@app.get("/")
def index(dr_session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    """Public landing; logged-in users go straight to the app."""
    if _require_user(dr_session):
        return RedirectResponse("/app", status_code=302)
    return FileResponse(STATIC / "landing.html")


@app.get("/app")
def app_page(dr_session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    if not _require_user(dr_session):
        return RedirectResponse("/login", status_code=302)
    return FileResponse(STATIC / "app.html")


@app.get("/login")
def login_page(dr_session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    if _require_user(dr_session):
        return RedirectResponse("/app", status_code=302)
    return FileResponse(STATIC / "login.html")


# --- auth API ---


class LoginBody(BaseModel):
    email: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=1, max_length=200)


@app.post("/api/login")
def api_login(body: LoginBody, response: Response):
    email = body.email.strip().lower()
    password = body.password
    # Stub: accept demo@… / demo, OR any email with password "demo"
    ok = (email == DEMO_EMAIL and password == DEMO_PASSWORD) or (
        "@" in email and password == DEMO_PASSWORD
    )
    if not ok:
        return JSONResponse(
            {"ok": False, "error": "Invalid credentials. Use any email + password demo"},
            status_code=401,
        )
    token = secrets.token_urlsafe(32)
    with _lock:
        _sessions[token] = {
            "email": email,
            "expires": time.time() + SESSION_TTL_S,
        }
    response = JSONResponse({"ok": True, "email": email})
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_TTL_S,
        path="/",
    )
    return response


@app.post("/api/logout")
def api_logout(response: Response, dr_session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    if dr_session:
        with _lock:
            _sessions.pop(dr_session, None)
    response = JSONResponse({"ok": True})
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@app.get("/api/me")
def api_me(dr_session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    user = _require_user(dr_session)
    if not user:
        return _auth_error()
    return {"ok": True, "email": user["email"]}


# --- data APIs (auth-gated) ---


@app.get("/healthz")
def healthz():
    """Render/load-balancer health — thin alias of /api/health."""
    return api_health()


@app.get("/api/health")
def api_health():
    snap = _snapshot()
    ok_n = sum(1 for s in snap["statuses"] if s.get("ok"))
    fail_n = len(snap["statuses"]) - ok_n
    return {
        "ok": True,
        "feeds_ok": ok_n,
        "feeds_fail": fail_n,
        "fetched_at_pt": snap["fetched_at_pt"],
        "fresh": snap["fresh"],
        "cache_ttl_s": snap["cache_ttl_s"],
        "rewarm_interval_s": snap["rewarm_interval_s"],
        "ui_soft_refresh_s": snap["ui_soft_refresh_s"],
        "leads": len(snap["leads"]),
        "providers": snap["providers"],
        "error": snap["error"],
        **_meta_fields(snap),
    }


@app.get("/api/feeds")
def api_feeds(
    refresh: bool = Query(False),
    dr_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    if not _require_user(dr_session):
        return _auth_error()
    snap = _ensure_data(force=refresh)
    return {
        "fetched_at": snap["fetched_at"],
        "fetched_at_pt": snap["fetched_at_pt"],
        "cache_ttl_s": snap["cache_ttl_s"],
        "cache_age_s": snap["cache_age_s"],
        "fresh": snap["fresh"],
        "refreshing": snap["refreshing"],
        "error": snap["error"],
        "feeds": [
            {
                "id": s.get("id"),
                "name": s.get("name"),
                "url": s.get("url"),
                "ok": s.get("ok"),
                "http": s.get("http"),
                "items": s.get("items"),
                "error": s.get("error"),
                "tls_note": s.get("tls_note"),
                "fetched_at": s.get("fetched_at"),
            }
            for s in snap["statuses"]
        ],
    }


@app.get("/api/leads")
def api_leads(
    confidence: str | None = Query("high,medium"),
    municipality: str | None = None,
    category: str | None = None,
    date_from: str | None = Query(None, description="YYYY-MM-DD"),
    date_to: str | None = Query(None, description="YYYY-MM-DD"),
    q: str | None = Query(None, description="Fulltext query (title/obec/kategorie)"),
    refresh: bool = Query(False),
    dr_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    if not _require_user(dr_session):
        return _auth_error()
    snap = _ensure_data(force=refresh)
    filtered = _filter_leads(
        snap["leads"],
        confidence=confidence,
        municipality=municipality,
        category=category,
        date_from=date_from,
        date_to=date_to,
        query=q,
    )
    munis = sorted({L.get("municipality") or "" for L in snap["leads"] if L.get("municipality")})
    cats = sorted({L.get("category") or "" for L in snap["leads"] if L.get("category")})
    return {
        "fetched_at": snap["fetched_at"],
        "fetched_at_pt": snap["fetched_at_pt"],
        "cache_ttl_s": snap["cache_ttl_s"],
        "cache_age_s": snap["cache_age_s"],
        "fresh": snap["fresh"],
        "rewarm_interval_s": snap["rewarm_interval_s"],
        "ui_soft_refresh_s": snap["ui_soft_refresh_s"],
        "notices_count": snap["notices_count"],
        "total_leads": len(snap["leads"]),
        "count": len(filtered),
        "filters": {
            "confidence": confidence,
            "municipality": municipality,
            "category": category,
            "date_from": date_from,
            "date_to": date_to,
            "q": q,
        },
        "municipalities": munis,
        "categories": cats,
        "leads": [_lead_public(L) for L in filtered],
        "error": snap["error"],
        **_meta_fields(snap),
    }


@app.get("/api/leads.csv")
def api_leads_csv(
    confidence: str | None = Query("high,medium"),
    municipality: str | None = None,
    category: str | None = None,
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    q: str | None = Query(None),
    dr_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    """Export currently filtered leads as CSV (UTF-8 BOM for Excel)."""
    import csv
    import io

    if not _require_user(dr_session):
        return _auth_error()
    snap = _ensure_data(force=False)
    filtered = _filter_leads(
        snap["leads"],
        confidence=confidence,
        municipality=municipality,
        category=category,
        date_from=date_from,
        date_to=date_to,
        query=q,
    )
    buf = io.StringIO()
    buf.write("\ufeff")
    w = csv.writer(buf, delimiter=";")
    w.writerow(
        [
            "obec",
            "publikovano",
            "kategorie",
            "jistota",
            "skore",
            "titulek",
            "url",
            "matched_terms",
        ]
    )
    for L in filtered:
        pub = _lead_public(L)
        w.writerow(
            [
                pub.get("municipality") or "",
                pub.get("published_at") or "",
                pub.get("category") or "",
                pub.get("confidence") or "",
                pub.get("confidence_score") or "",
                pub.get("title_redacted") or "",
                pub.get("url") or "",
                ", ".join(pub.get("matched_terms") or []),
            ]
        )
    from fastapi.responses import Response as FastResponse

    return FastResponse(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="deskaradar-leads.csv"'},
    )


@app.get("/api/digest")
def api_digest(
    group_by: str = Query("municipality", pattern="^(municipality|day)$"),
    confidence: str | None = Query("high,medium"),
    date_from: str | None = None,
    date_to: str | None = None,
    refresh: bool = Query(False),
    dr_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    """Digest-shaped payload: leads grouped by municipality or by published day."""
    if not _require_user(dr_session):
        return _auth_error()
    snap = _ensure_data(force=refresh)
    filtered = _filter_leads(
        snap["leads"],
        confidence=confidence,
        date_from=date_from,
        date_to=date_to,
    )
    groups: dict[str, list[dict[str, Any]]] = {}
    for L in filtered:
        if group_by == "day":
            key = L.get("published_at") or "unknown"
        else:
            key = L.get("municipality") or "unknown"
        groups.setdefault(key, []).append(_lead_public(L))

    # sort groups: by date desc for day, alpha for municipality
    if group_by == "day":
        keys = sorted(groups.keys(), reverse=True)
    else:
        keys = sorted(groups.keys())

    ok_n = sum(1 for s in snap["statuses"] if s.get("ok"))
    fail_n = len(snap["statuses"]) - ok_n
    today_s = datetime.now(TZ).date().isoformat()

    return {
        "title": f"DeskaRadar — JMK denní digest",
        "digest_date": today_s,
        "generated_pt": datetime.now(TZ).strftime("%Y-%m-%d %H:%M %Z"),
        "fetched_at_pt": snap["fetched_at_pt"],
        "feeds_ok": ok_n,
        "feeds_fail": fail_n,
        "lead_count": len(filtered),
        "group_by": group_by,
        "groups": [{"key": k, "count": len(groups[k]), "leads": groups[k]} for k in keys],
        "statuses": [
            {
                "name": s.get("name"),
                "ok": s.get("ok"),
                "http": s.get("http"),
                "items": s.get("items"),
                "error": s.get("error"),
                "tls_note": s.get("tls_note"),
            }
            for s in snap["statuses"]
        ],
    }


@app.get("/api/alerts")
def api_alerts(
    refresh: bool = Query(False),
    dr_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    if not _require_user(dr_session):
        return _auth_error()
    user = _require_user(dr_session)
    assert user
    snap = _ensure_data(force=refresh)
    prefs = _load_prefs(user["email"])
    alerts = _alerts_for_prefs(snap["leads"], prefs)
    return {
        "window": "24h",
        "criterion": "prefs-aware (high_only / municipalities) + published last 24h PT",
        "fetched_at_pt": snap["fetched_at_pt"],
        "prefs": prefs,
        "count": len(alerts),
        "alerts": [_lead_public(L) for L in alerts],
    }


class AlertPrefsBody(BaseModel):
    high_only: bool = True
    municipalities: list[str] = Field(default_factory=list)
    email: str = ""
    enabled: bool = True


@app.get("/api/alert-prefs")
def get_alert_prefs(dr_session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    if not _require_user(dr_session):
        return _auth_error()
    user = _require_user(dr_session)
    assert user
    return {"ok": True, "prefs": _load_prefs(user["email"])}


@app.put("/api/alert-prefs")
def put_alert_prefs(
    body: AlertPrefsBody,
    dr_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    if not _require_user(dr_session):
        return _auth_error()
    user = _require_user(dr_session)
    assert user
    saved = _save_prefs(
        user["email"],
        {
            "high_only": body.high_only,
            "municipalities": body.municipalities,
            "email": body.email,
            "enabled": body.enabled,
        },
    )
    return {"ok": True, "prefs": saved}


@app.get("/api/providers")
def api_providers(dr_session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    """List ingest providers (CZ live; AT/DE/IT stubs for future packs)."""
    if not _require_user(dr_session):
        return _auth_error()
    return {
        "ok": True,
        "providers": [p.describe() for p in list_providers()],
        "active": [p.describe() for p in active_providers(live_only=True)],
    }


@app.post("/api/refresh")
def api_refresh(
    mode: str = Query("live", description="live | fixture"),
    dr_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    if not _require_user(dr_session):
        return _auth_error()
    m = (mode or "live").strip().lower()
    if m in ("fixture", "sample", "demo", "ukazka"):
        snap = _apply_fixture_cache()
    else:
        snap = _refresh_feeds(force=True)
    return {
        "ok": True,
        **_meta_fields(snap),
        "fetched_at_pt": snap["fetched_at_pt"],
        "leads": len(snap["leads"]),
        "feeds_ok": sum(1 for s in snap["statuses"] if s.get("ok")),
        "feeds_fail": sum(1 for s in snap["statuses"] if not s.get("ok")),
        "fresh": snap["fresh"],
        "error": snap["error"],
    }


@app.on_event("startup")
def _startup():
    _init_db()

    def warm():
        try:
            _refresh_feeds(force=True)
        except Exception:
            pass

    def rewarm_loop():
        # Sleep first — initial warm already ran. Only refetch when cache is stale.
        while True:
            time.sleep(REWARM_INTERVAL_S)
            try:
                if not _cache_fresh() and not _refreshing:
                    _refresh_feeds(force=False)
            except Exception:
                pass

    threading.Thread(target=warm, daemon=True, name="deskaradar-warm").start()
    threading.Thread(target=rewarm_loop, daemon=True, name="deskaradar-rewarm").start()


if __name__ == "__main__":
    import uvicorn

    import os
    port = int(os.environ.get("PORT", "8765"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
