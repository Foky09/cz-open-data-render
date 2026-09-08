# WasteGate — Railway deploy

## Service
- Suggested name: `wastegate`
- Stack: FastAPI + Uvicorn + Jinja2

## Railway settings
- **Root Directory:** `wastegate` (parent of `app/` — needed for `day1/` snapshot seed)
- Use parent config: `wastegate/railway.toml` (dockerfilePath = `app/Dockerfile`)
- Or build locally: `docker build -f app/Dockerfile -t wastegate .` from `wastegate/`

## Start command
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```
(WORKDIR in image is `/srv/app`)

## Port
- Env: `PORT` (Railway injects)
- Local fallback default: **3460**

## Health
- `GET /health`

## Notes
- Demo auth unchanged: `demo@wastegate.cz` / `demo1234`.
- MZP / VISOH2 footer attribution unchanged.
- Do not touch od-platform WasteGate AuthPanel / connectors.
