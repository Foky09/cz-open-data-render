# WasteGate (CZ MVP web app)

Standalone SaaS stub: login, watchlist CRUD, status dashboard, in-app email alerts.
Day-1 VISOH2 scripts under `../day1/` remain backend-only.

## Run

```bash
cd /workspace/wastegate/app
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn main:app --host 0.0.0.0 --port 3460
```

Open http://127.0.0.1:3460

Demo: `demo@wastegate.cz` / `demo1234`

## Domain

Partners use `country` + `localId` (CZ: IČZ/IČOB). Ready for AT/DE/IT later.
