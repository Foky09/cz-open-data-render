# SpectrumDeadline (Web MVP)

Kalendář obnov a alerty pro ČTÚ RLAN stanice (CZ WISP). **Upload → bucket calendar → actionable alerts** v prohlížeči.

**Bez auto-prodloužení / no auto-renew.** Obnovu provádíte vy v portálu ČTÚ.

## Run

```bash
cd /workspace/spectrum/app
npm install
npm run dev
```

Otevřete http://localhost:3000 — pracovní plocha: `/app`.

Produkční build:

```bash
npm run build && npm start
```

## Product boundary

| Ano | Ne |
|-----|----|
| Upload CSV/XLSX stanic | Auto-renew / auto-prodloužení |
| Bucket kalendář + actionable alerty | Přihlášení do ČTÚ API (MVP je upload-only) |
| Export CSV/JSON | Zápis do ČTÚ |
| localStorage session cache | Server-side persistence |

## Doménová pravidla

Shodná s CLI v `../concierge/`:

- Cyklus: **12 měsíců platnost + 6 měsíců ochrana = 18 měsíců**
- Bucket podle dní do `valid_to` (Europe/Prague): `overdue` / `≤30` / `≤60` / `≤90` / `later`
- **Actionable** = overdue ∪ ≤30 (portál typicky dovolí renew při <1 měsíci)
- Datumy: unix int nebo ISO `YYYY-MM-DD`; sloupce `valid_to` (povinný), `protected_to`, `callsign`/`station_id`/`id`, `name`, `frequency_mhz`/`frequency`/`freq`

Ukázková data: `public/sample_stations.csv` (kopie z concierge).

## Architecture (thin)

- `RegulatorConnector` (`src/lib/connectors/`) — parse regulator export → `{id, name, valid_to, protected_to, …}`
- MVP implementation: **ČTÚ CZ upload** only (`ctuCzUpload.ts`). DE BNetzA / AT / IT can plug in later; not in UI yet.
- Calendar/alerts core (`src/lib/domain.ts`) consumes `NormalizedStation` only — no ČTÚ column names in bucket logic.

## Stack

Next.js (App Router) + TypeScript + plain CSS. Doménová logika: `src/lib/domain.ts` (TS port `concierge.py`).

## Related

- CLI podpora: `../concierge/` (`python concierge.py sample_stations.csv`)
