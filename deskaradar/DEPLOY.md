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
- Attribution (Brno CC BY / otevřená data JMK) unchanged.


## Render env (alert e-mail)

Preferred:
- `RESEND_API_KEY` — Resend API key
- `ALERT_FROM_EMAIL` — verified sender (default `alerts@deskaradar.onrender.com`)
- `PUBLIC_APP_URL` — optional, default `https://deskaradar.onrender.com`

SMTP fallback (if Resend unset):
- `SMTP_HOST`, `SMTP_PORT` (587), `SMTP_USER`, `SMTP_PASS`, `SMTP_TLS` (default on)

Health: `GET /api/health` · Alert mail status (auth): `GET /api/alerts/status`

Without keys the service boots; test send returns 503 until configured. Details: `ALERT-EMAIL.md`.
