"""CapexPulse movers dashboard — static UI + FastAPI for Railway wave 1."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

app = FastAPI(title="CapexPulse", docs_url=None, redoc_url=None)
app.mount("/data", StaticFiles(directory=str(DATA)), name="data")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "product": "capexpulse"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(ROOT / "index.html")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8877"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
