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
