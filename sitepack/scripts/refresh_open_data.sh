#!/usr/bin/env bash
# Re-download ČGS open zips and rebuild spatial indexes.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
.venv/bin/python - <<'PY'
from providers.geo_cache import ensure_cgs_cache, ensure_indexes
ensure_cgs_cache(force=True)
ensure_indexes(force=True)
print("OK cache refreshed under data/cache/")
PY
