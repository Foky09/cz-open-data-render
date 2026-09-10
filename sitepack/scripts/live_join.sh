#!/usr/bin/env bash
# SitePack one-click live concierge join (demo parcel polygon → live layer statuses).
# Usage:
#   bash scripts/live_join.sh
#   bash scripts/live_join.sh --ruian 123456789
#   bash scripts/live_join.sh --ku "Brno-město" --parcel 1234/5 --live-ruian
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${ROOT}/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt requests
  PY="${ROOT}/.venv/bin/python"
fi
# Default: demo identity + prefer_live joins (polygon drives VÚV/ČGS/…)
if [[ $# -eq 0 ]]; then
  exec "$PY" -m app.cli --demo --json --no-files
else
  exec "$PY" -m app.cli --json --no-files "$@"
fi
