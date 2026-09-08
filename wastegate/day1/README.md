# WasteGate Day-1 — VISOH2 concierge MVP

Local day-1 scripts (DeskaRadar-style): normalize today’s VISOH2 registry export → watchlist → diff → email-ready alert (markdown + pasteable `.email.txt`).

**Not** under `od-platform` yet. Outbound/GTM is frozen — product only.

## Layout

| Path | Role |
|------|------|
| `normalize.py` | Stream-parse `export-zarizeni.xml` → `snapshots/YYYY-MM-DD.jsonl` |
| `diff_watch.py` | Watchlist × snapshot (+ optional previous) → `alerts/alert-YYYY-MM-DD.md` **and** `alerts/alert-YYYY-MM-DD.email.txt` |
| `render_email.py` | Optional alias — same command as `diff_watch.py` |
| `fetch_export.py` | Download current ZIP from MŽP, unzip, run normalize |
| `watchlist.example.yaml` | Example IČZ / IČOB watchlist |
| `samples/registry-current/export-zarizeni.xml` | Full current export (~552 MB) |
| `notes/SCHEMA.md` | Schema / ingest notes |

Namespace: `http://mzp.cz/visoh2registrv1.xsd`

## Quick start (offline — data already on disk)

```bash
cd /workspace/wastegate/day1

# 1) Normalize full export (iterparse — safe for 552 MB)
python3 normalize.py
# → snapshots/2026-09-08.jsonl

# 2) Baseline alert for example watchlist (no previous snapshot)
python3 diff_watch.py --watchlist watchlist.example.yaml
# → alerts/alert-2026-09-08.md
# → alerts/alert-2026-09-08.email.txt
```

Nightly with previous day:

```bash
python3 diff_watch.py \
  --watchlist watchlist.example.yaml \
  --current snapshots/2026-09-08.jsonl \
  --previous snapshots/2026-09-07.jsonl
```

## Alert outputs

One run writes **both**:

1. **`alerts/alert-YYYY-MM-DD.md`** — markdown report  
2. **`alerts/alert-YYYY-MM-DD.email.txt`** — `Subject:` + plain-text body (paste/send; no SMTP yet)

Subject patterns:

- Baseline: `WasteGate: baseline watchlist (YYYY-MM-DD)`
- Diff: `WasteGate: N změn na watchlistu (YYYY-MM-DD)`

**PII / body hygiene:** show IČZ/IČOB id, optional watchlist label, status, operator **IČO only** (prefer watchlist label over registry `operator_name`). Waste codes: count + first 5 max.

Every alert ends with attribution:

> Zdroj: MŽP ČR – VISOH2 Registr zařízení (veřejný denní export). MŽP produkt nepodporuje. Data mohou obsahovat osobní údaje.

## Fetch latest export

```bash
python3 fetch_export.py
# GET https://visoh2.mzp.cz/Zarizeni/Zarizeni/ExportRegistry
# User-Agent: WasteGate/0.1
```

## Snapshot record shape

One JSON object per device / trader / storage:

```json
{
  "id": "CZK00551",
  "kind": "zarizeni",
  "status": "aktivni",
  "operator_ico": "64357571",
  "operator_name": "BOTEP PLUS spol. s r.o.",
  "waste_codes": ["8_2021_190805"],
  "export_date": "2026-09-08T03:00:00.801276+02:00"
}
```

- `id`: IČZ (`zarizeni` / `sklad`) or IČOB (`obchodnik`)
- `waste_codes`: from `historie/Verze` with `aktualni=true`, codes with no `do` or `do` in the future / open-ended (`9999-…`)

## Diff signals

1. Current `status` flip  
2. `operator_ico` change  
3. `waste_codes` set change  

If `--previous` is omitted, writes a **baseline initial status report** (first concierge email).

## License / ToU

Public anonymous download of the registry export works. Commercial reuse terms (Provozní řád / MŽP) are **not** confirmed here — do not invent license claims.
