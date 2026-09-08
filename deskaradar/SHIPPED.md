# DeskaRadar app — SHIPPED

**Date:** 2026-09-08 (Europe/Prague)  
**Stack:** FastAPI + static HTML (login + SPA tabs) — fastest path reusing Python classifier/feeds.  
**Version:** 0.2.1 (polish + freshness hardening)

## DoD checklist

| # | Requirement | Status |
|---|-------------|--------|
| 1 | **Login stub** gates the app (cookie session) | DONE — `/login`; any email + `demo` |
| 2 | **JMK leads feed** in browser (live OFN) | DONE — Leady tab + `/api/leads` |
| 3 | **Filters** municipality, confidence, date, category | DONE |
| 4 | **Daily digest view** grouped by municipality/day | DONE — Denní digest tab + `/api/digest` |
| 5 | **Alert prefs** UI + persist + wire to alerts | DONE — SQLite `data/deskaradar.db`; `/api/alert-prefs` + `/api/alerts` |
| — | Feed health table | DONE |
| — | No eDesky scrape | DONE — OFN only via `providers/cz_ofn` → `daily_digest.FEEDS` |
| — | Reuse `classify_notice` / FEEDS | DONE |
| — | Cache 15–30 min | DONE — 20 min |
| — | README how to run | DONE |

## Polish (0.2.1) — what changed

1. **Pluggable ingest** — `app/providers/` with `Provider` interface; **CZ OFN live** (`cz_ofn` wraps existing `FEEDS`/`fetch_feed`); AT/DE/IT stubs registered, not live. `GET /api/providers`.
2. **UI polish** — Czech labels consistency (Jistota, Odhlásit, Stav feedů, …); prominent **Poslední obnovení** stamp; clearer empty states; tighter lead cards (confidence badge + obec chip).
3. **Freshness** — background re-warm every 5 min **only if cache stale**; UI soft auto-refresh every 3 min from cache (documented in footer + header hint); force refresh still 60s cooldown.
4. Login stub, filters, digest, alert prefs unchanged in behaviour.

## What works

- Demo auth (`dr_session` httponly cookie)
- Background warm-fetch of 10 municipalities + JMK kraj on startup
- Classification → default high+medium `stavebni_zamer` leads with redacted titles
- Digest-shaped UI (not only raw table)
- Alert prefs: high-only, municipalities of interest, email stub, enabled toggle
- Force refresh with 60s cooldown
- Soft UI refresh + cache-respecting server re-warm

## Run

```bash
cd /workspace/deskaradar/app
.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8765
```

URL: http://127.0.0.1:8765/

## Not in scope / stubs

- No real email delivery (email field is stub only)
- No real IdP / password hashing beyond demo gate
- No outbound/marketing
- No eDesky / HTML board scrape
- AT/DE/IT ingest not implemented (stubs only)

## Smoke test (2026-09-08 ~19:07 CEST / PT — polish pass)

| Metric | Result |
|--------|--------|
| Feeds OK/fail | **11 / 0** |
| Notices parsed | 5308 |
| Leads (high+medium stavebni_zamer) | **82** |
| Digest groups (by municipality) | 11 |
| Alerts (high, 24h, prefs default) | 12 |
| Providers | cz_ofn live; at/de/it stubs |
| Login + app HTML | HTTP 200 |
| `/api/providers` / prefs PUT | OK |
| Blockers | none |

Server left running: `uvicorn` on **0.0.0.0:8765**.
