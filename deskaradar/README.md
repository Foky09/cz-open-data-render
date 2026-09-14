# DeskaRadar web app (JMK)

Browser UI + FastAPI backend for **live OFN úřední deska** leads in Jihomoravský kraj.

- Reuses `../daily_digest.py` (FEEDS, fetch, parse) and `../classify_notice.py` via pluggable **`providers/cz_ofn`**
- AT / DE / IT provider stubs registered for later country packs (not live)
- **No eDesky HTML scrape**
- Demo login stub, leads feed, filters, daily digest view, alert prefs (SQLite), feed health
- Soft UI auto-refresh (cache-only) + background re-warm that respects cache TTL

## Requirements

- Python 3.10+
- Virtualenv (included setup below)

## Run

```bash
cd /workspace/deskaradar/app
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8765
```

Open: **http://127.0.0.1:8765/**

Login stub: any email + password **`demo`**  
(or `demo@deskaradar.local` / `demo`)

## Ports

| Service | Port |
|---------|------|
| Web UI + API | **8765** |

## Screens

1. **Login** — `/login`
2. **Leady** — classified `stavebni_zamer` high/medium; filters: obec, jistota, datum, kategorie; lead cards with confidence badge + municipality chip
3. **Denní digest** — grouped by municipality or by day
4. **Alerty & nastavení** — 24h alerts respecting prefs; prefs persisted in `data/deskaradar.db`
5. **Stav feedů** — last fetch OK/fail per municipality + JMK kraj

## API (session cookie required except `/api/health`)

- `GET /api/leads` — filtered leads (+ cache / soft-refresh meta)
- `GET /api/digest` — digest groups
- `GET /api/alerts` — prefs-aware 24h alerts
- `GET/PUT /api/alert-prefs` — alert preferences
- `GET /api/alerts/status` — `{ email_configured, provider }` (resend|smtp|null)
- `POST /api/alerts/send-test` — send one test email to prefs.email (503 if no key)
- `GET /api/feeds` — feed health
- `GET /api/providers` — ingest providers (CZ live; AT/DE/IT stubs)
- `POST /api/refresh` — force refetch (60s cooldown)
- `POST /api/login` / `POST /api/logout` / `GET /api/me`

## Caching / freshness / politeness

| Knob | Value |
|------|-------|
| In-memory cache TTL | **20 minutes** |
| Server background re-warm | every **5 min**, only when cache is **stale** |
| UI soft auto-refresh | every **3 min** via `/api/leads` (cache only — no feed hammering) |
| Force refresh cooldown | **60 s** |
| Feed GETs | sequential, 25s timeout, DeskaRadar User-Agent (from `daily_digest.py`) |

Brno uses `tls_insecure` (incomplete CA chain) as in Day-1 research.

## Providers (`app/providers/`)

| id | country | live |
|----|---------|------|
| `cz_ofn` | CZ | **yes** — wraps `daily_digest.FEEDS` / `fetch_feed` |
| `at_stub` | AT | no |
| `de_stub` | DE | no |
| `it_stub` | IT | no |



## Alert e-mail (Resend / SMTP)

Outbound alerts run when prefs have `enabled=true` and a non-empty `email`, after a successful **live** refresh (deduped in SQLite `alert_sent`).

| Env | Required | Notes |
|-----|----------|-------|
| `RESEND_API_KEY` | preferred | [Resend](https://resend.com) API key |
| `ALERT_FROM_EMAIL` | no | default `alerts@deskaradar.onrender.com` (must be allowed in Resend) |
| `PUBLIC_APP_URL` | no | default `https://deskaradar.onrender.com` |
| `SMTP_HOST` | fallback | if Resend unset |
| `SMTP_PORT` | no | default `587` |
| `SMTP_USER` / `SMTP_PASS` | if SMTP auth | |
| `SMTP_TLS` | no | default on (`1`); set `0` to disable STARTTLS |

Without a key the app still runs; `/api/alerts/send-test` and delivery return **503** with an actionable message. See `ALERT-EMAIL.md`.

UI badge DoD: **Živá data** / **Ukázka** only — no fixture/OFN/TLS jargon in user-facing strings.

## Attribution

Brno CC BY 4.0 (MMB). Other feeds per NKOD / OFN. Deep-link `url` is source of truth.


## Fixture vs live

| Path | How | Label |
|------|-----|-------|
| **Fixture** | UI „Ukázková data“ → `POST /api/refresh?mode=fixture` · `data/fixtures/leads-fixture.json` | Ukázka |
| **Live** | UI „Obnovit živá data“ → `POST /api/refresh?mode=live` · `CzOfnProvider` / `daily_digest.py` | Živá data |
| **Digest CLI** | `python3 daily_digest.py` | writes `digests/YYYY-MM-DD-jmk.md` |

No eDesky HTML scrape. Connector id `ofn-jmk` in `@od/connectors` — see CONNECTIVITY.md.
