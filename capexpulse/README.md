# CapexPulse dashboard (Railway wave 1)

Static Weekly ICT capex movers UI (MONITOR položka 6125, metric v2.1).

## Local
```bash
cd /workspace/capexpulse/dashboard
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
PORT=8877 python main.py
# open http://127.0.0.1:8877/
```

Or: `python3 -m http.server 8877` (static only).

## Data
- `data/movers-2026006.json` — rebuild via `python3 ../scripts/build_movers.py` then copy from `../app/public/data/`.

## Railway
- Root directory: `/workspace/capexpulse/dashboard` (or repo subpath `capexpulse/dashboard`)
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health: `GET /healthz`

Attribution footer is mandatory (MFČR MONITOR + ToU). No outbound/CRM in this app.


## Render
- Service name: `capexpulse`
- Blueprint: `render.yaml` in this folder
- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health: `GET /healthz`
