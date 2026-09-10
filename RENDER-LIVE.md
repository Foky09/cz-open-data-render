# RENDER-LIVE — connector product sync

Synced **2026-09-10** (PT) from live connector trees into this Render monorepo.
Ready to commit/deploy; no `node_modules` / `.venv` included.

## What went live

| Service | Source → dest | Highlights |
|---------|---------------|------------|
| **deskaradar** | `/workspace/deskaradar/app` → `deskaradar/` | `main.py` (fixture leads + `RLock`), `providers/`, `static/`, `classify_notice.py`, `data/fixtures/leads-fixture.json`, `daily_digest.py` |
| **sitepack** | `/workspace/sitepack/concierge` → `sitepack/` | `app/`, `providers/`, `templates/`, `static/`, `scripts/` (incl. `live_join.sh`), `data/fixtures/`; **not** `data/cache` large zips/geojson |
| **spectrum** | `/workspace/spectrum/app/src` → `spectrum/src` | `lib/parseFile.ts`, `lib/domain.ts`, `components/Workspace`, `@/` import on app page |
| **wastegate** | `/workspace/wastegate/app` → `wastegate/` | `main.py`, `templates/`, `static/`; `day1/` meta + small `_test.jsonl`; kept existing `2026-09-08.jsonl`; **skipped** huge newer daily snapshots (~12MB each) |
| **capexpulse** | `/workspace/capexpulse/dashboard` → `capexpulse/` | `main.py`, `index.html`, `landing.html`, `data/movers-*.json`; **skipped** `shots/` |

## Connectivity / deploy notes

- All five apps bind `0.0.0.0` + `PORT`; health: `/healthz` (see root `render.yaml`).
- **deskaradar**: OFN JSON-LD providers + fixture mode for offline/CI; `daily_digest.py` beside app for digest jobs.
- **sitepack**: live join scripts present; geo cache stays local/runtime (`data/cache/` gitignored except `.gitkeep`).
- **spectrum**: Next.js CTU CZ upload connector path in `src/lib/connectors/`.
- **wastegate**: watchlist/alerts UI; large day1 snapshots not expanded to avoid repo bloat.
- **capexpulse**: movers JSON dashboard + landing; screenshots omitted.

## Explicitly excluded

- `.venv/`, `node_modules/`, `__pycache__/`, `Dockerfile`, `railway.toml` (per-app)
- sitepack `data/cache` large artifacts; capexpulse `shots/`
- wastegate day1 snapshots `2026-09-09.jsonl`, `2026-09-10.jsonl` (too large for git sync)
