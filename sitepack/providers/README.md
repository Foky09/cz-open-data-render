# Providers (CZ-first, country-pluggable)

`PackRequest.country` defaults to `CZ`. Non-CZ returns honest STUB (`country=… not implemented`).

| Layer | Live path | Fallback |
|-------|-----------|----------|
| ruian | VDP/VFR hook documented; no free JSON API | DEMO identity + WGS84 polygon / STUB |
| flood | VÚV ArcGIS REST Q100 + aktivní zóna envelope intersect | STUB/DEMO |
| radon | ČGS `Geohazardy/radon50` identify | STUB/DEMO |
| poddolovani | ČGS `poddolovane_uzemi.zip` GeoJSON PiP | STUB/DEMO |
| svahy | ČGS `svahove_deformace.zip` plochy PiP + body distance | STUB/DEMO |
| zoning | ÚÚR evidence/map portal URL by obec | STUB/DEMO |

Cache: `data/cache/` (gitignored). Refresh: `scripts/refresh_open_data.sh` or `python scripts/build_geo_index.py`.


## Fixture vs live

| Path | How | Label in UI |
|------|-----|-------------|
| **Fixture / ukázka** | Checkbox „Použít ukázkovou parcelu“ or empty form → `demo_parcel.json` | Ukázka / DEMO |
| **Live joins** | Uncheck demo + optional „Zkusit živá data parcely“; `prefer_live` | Živá / Orientační / Ukázka (fallback) |
| **Refresh ČGS cache** | `scripts/refresh_open_data.sh` or `python scripts/build_geo_index.py` | local GeoJSON under `data/cache/` |

Connector (od-platform): `sitepack-layers` — `mode: fixture` \| `live` (endpoint HEAD probe + sample layer table). See `packages/connectors/CONNECTIVITY.md`.
