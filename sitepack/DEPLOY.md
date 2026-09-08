# SitePack Pro (concierge) — Railway deploy

## Service
- Suggested name: `sitepack`
- Stack: FastAPI + Uvicorn + Jinja2

## Railway settings
- **Root Directory:** `sitepack/concierge`
- **Dockerfile path:** `Dockerfile`

## Start command
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Port
- Env: `PORT` (Railway injects)
- Local fallback default: **8787**

## Health
- `GET /health`

## Notes
- Binds `0.0.0.0` (was `127.0.0.1` in `scripts/run_web.sh` — fixed).
- Open-data cache under `data/cache/` is copied into the image (zips + linie geojson excluded to shrink layers).
- CZ open-data attribution / disclaimers in report templates unchanged.
- No KN ownership scrape.
