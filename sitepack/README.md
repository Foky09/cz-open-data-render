# SitePack Pro — Concierge (live open-data joins)

Lokální / SaaS backend concierge: identifikátor parcely → **HTML + PDF** feasibility snapshot.

**Produkt:** CZ parcelní rešerše (web app SaaS). CLI je backend-only runner.  
**Záměrně NE:** vlastnictví / LV / KN scrape.

Concierge root: `/workspace/sitepack/concierge/`

---

## Quick start

```bash
cd /workspace/sitepack/concierge
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Refresh ČGS open-data cache (poddolování + sesuvy) + spatial indexes
./scripts/refresh_open_data.sh   # or skip if data/cache already populated

# One-shot demo (UKÁZKA identity + LIVE joins on demo polygon)
.venv/bin/python run_demo.py

# CLI (backend)
.venv/bin/python -m app.cli --demo
.venv/bin/python -m app.cli --ruian 680123456
.venv/bin/python -m app.cli --ku "Brno-město" --parcel 1234/5

# Web UI (SaaS shell)
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8787
```

PDF: Chrome/Chromium headless (viz `app/render.py`).

---

## Layer status (v1)

| Layer | Status | Live source | License / notes |
|-------|--------|-------------|-----------------|
| **RÚIAN** | **LIVE** (real Id) / **DEMO** (fiktivní 680123456) | ČÚZK ArcGIS RUIAN/MapServer layer 5 Parcela | CC BY; no KN ownership |
| **Flood Q100 + AZ** | **LIVE** | VÚV `ags.vuv.cz` ISVS-VODA MapServer layers 13 + 11 | Open; HEIS https://heis.vuv.cz/isvs/zapluz/ · not ČHMÚ |
| **Radon 1:50k** | **LIVE** | ČGS `mapy.geology.cz` Geohazardy/radon50 identify | CC BY |
| **Poddolování** | **LIVE** | ČGS https://od.geology.cz/poddolovane_uzemi.zip → PiP | CC BY |
| **Svahové deformace** | **LIVE** | ČGS https://od.geology.cz/svahove_deformace.zip → PiP/distance | CC BY |
| **Zoning light** | **LIVE** (link) | ÚÚR mapový portál / evidence ÚP by obec | Light only — no nationwide ÚP vector |

On live failure/timeout → **FALLBACK** to stub/demo for that layer (report marked partial).  
`PackRequest.country` defaults to `CZ` (pluggable hook; non-CZ → STUB).

---

## Cache

Path: `/workspace/sitepack/concierge/data/cache/` (gitignored except `.gitkeep`).

| File | Role |
|------|------|
| `poddolovane_uzemi.zip` / `.geojson` / `_idx.pkl` | ČGS poddolování |
| `svahove_deformace.zip`, `sesuvy_*.geojson`, `*_idx.pkl` | ČGS sesuvy |
| Refresh | `./scripts/refresh_open_data.sh` |

---

## Architecture

```
concierge/
  app/           # FastAPI + CLI + orchestrator + Jinja/PDF
  providers/     # live-first joins; stub fallback
  data/cache/    # open-data downloads + indexes
  templates/     # report shell with LIVE/STUB/FALLBACK badges
  output/        # generated HTML/PDF
```

Each provider: **try live → on failure FALLBACK stub**. Loud CZ disclaimers stay in the report.

---

## Disclaimers (loud, Czech)

- **Povodně** — orientační, nenahrazuje vodoprávní úřad  
- **Radon** — pouze mapa 1:50k; měření na pozemku povinné  
- **Zoning** — light; nenahrazuje ÚR / stanovisko  
- **Patička** — informativní; **bez KN ownership**

---

## Absolute paths

| What | Path |
|------|------|
| Concierge | `/workspace/sitepack/concierge/` |
| Demo output HTML | `/workspace/sitepack/concierge/output/sitepack-demo.html` |
| Demo output PDF | `/workspace/sitepack/concierge/output/sitepack-demo.pdf` |
| Cache | `/workspace/sitepack/concierge/data/cache/` |
