# DeskaRadar — Railway deploy

## Service
- Suggested name: `deskaradar`
- Stack: FastAPI + Uvicorn

## Railway settings
- **Root Directory:** `deskaradar` (parent of `app/` — needed for `daily_digest.py` / `classify_notice.py`)
- Use parent config: `deskaradar/railway.toml` (dockerfilePath = `app/Dockerfile`)
- Or build locally: `docker build -f app/Dockerfile -t deskaradar .` from `deskaradar/`

## Start command
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```
(WORKDIR in image is `/srv/app`)

## Port
- Env: `PORT` (Railway injects)
- Local fallback default: **8765**

## Health
- `GET /api/health`

## Notes
- Binds `0.0.0.0`; no localhost hardcodes in server bind.
- Demo login unchanged (any email + password `demo`).
- Attribution (Brno CC BY / OFN) unchanged.
