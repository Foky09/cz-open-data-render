"""SitePack Pro — SaaS web UI (product surface).

CLI remains in app.cli for backend/dev only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.auth import authenticate, current_user, login_session, logout_session, register_user
from app.models import PackRequest
from app.orchestrator import ConciergeOrchestrator
from app.render import generate_pack_files

app = FastAPI(title="SitePack Pro", version="0.2.0", description="CZ parcelní rešerše SaaS")
app.add_middleware(
    SessionMiddleware,
    secret_key="sitepack-pro-dev-stub-not-secure",
    session_cookie="sp_session",
    same_site="lax",
)

STATIC = ROOT / "static"
TEMPLATES_DIR = ROOT / "templates"
OUTPUT = ROOT / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
orch = ConciergeOrchestrator()

# In-memory pack cache for results page (also persisted as HTML/PDF on disk)
_PACK_META: dict[str, dict] = {}


def _ctx(request: Request, **extra):
    user = current_user(request)
    base = {
        "request": request,
        "user": user,
        "product": "SitePack Pro",
        "country": "CZ",
        "demo_ruian": "680123456",
        "demo_ku": "Brno-město",
        "demo_parcel": "1234/5",
    }
    base.update(extra)
    return base


@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    return templates.TemplateResponse(request, "saas/landing.html", _ctx(request))


@app.get("/app", response_class=HTMLResponse)
def app_shell(request: Request):
    return templates.TemplateResponse(request, "saas/app.html", _ctx(request, error=None))


@app.post("/generate")
def generate(
    request: Request,
    ruian_id: str = Form(""),
    ku: str = Form(""),
    parcel_number: str = Form(""),
    demo: str = Form(""),
    force_live_ruian: str = Form(""),
):
    rid = ruian_id.strip()
    ku_s = ku.strip()
    pn = parcel_number.strip()
    # Friendly validation: partial k.ú. / parcel without demo → clear Czech error
    if not demo and not rid and ((ku_s and not pn) or (pn and not ku_s)):
        return templates.TemplateResponse(
            request,
            "saas/app.html",
            _ctx(
                request,
                error="Doplňte parcelní číslo a katastrální území — nebo zapněte ukázku.",
            ),
            status_code=400,
        )
    use_demo = bool(demo) or (not rid and not (ku_s and pn))
    req = PackRequest(
        country="CZ",
        ruian_id=rid or None,
        ku=ku_s or None,
        parcel_number=pn or None,
        demo=use_demo,
        force_live_ruian=bool(force_live_ruian),
    )
    try:
        pack = orch.build(req)
    except Exception as exc:  # noqa: BLE001
        return templates.TemplateResponse(
            request,
            "saas/app.html",
            _ctx(
                request,
                error=f"Rešerši se nepodařilo sestavit. Zkuste ukázku nebo to zkuste znovu. ({type(exc).__name__})",
            ),
            status_code=500,
        )
    stem = f"sitepack-{pack.parcel.ruian_id or 'custom'}"
    # Avoid collisions for stub custom parcels
    if not pack.parcel.ruian_id:
        safe_ku = (ku_s or "x").replace("/", "-").replace(" ", "_")[:40]
        safe_pn = (pn or "x").replace("/", "-").replace(" ", "_")[:40]
        stem = f"sitepack-{safe_ku}-{safe_pn}"
    try:
        html_path, pdf_path = generate_pack_files(pack, stem=stem)
    except Exception as exc:  # noqa: BLE001
        return templates.TemplateResponse(
            request,
            "saas/app.html",
            _ctx(
                request,
                error=f"Rešerši se nepodařilo uložit. Zkuste to znovu. ({type(exc).__name__})",
            ),
            status_code=500,
        )
    meta = {
        "stem": stem,
        "pack": pack.model_dump(mode="json"),
        "html": str(html_path),
        "pdf": str(pdf_path) if pdf_path else None,
    }
    _PACK_META[stem] = meta
    meta_path = OUTPUT / f"{stem}.meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return RedirectResponse(url=f"/results/{stem}", status_code=303)


@app.get("/results/{stem}", response_class=HTMLResponse)
def results(request: Request, stem: str):
    meta = _PACK_META.get(stem)
    if meta is None:
        meta_path = OUTPUT / f"{stem}.meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            _PACK_META[stem] = meta
    html_path = OUTPUT / f"{stem}.html"
    pdf_path = OUTPUT / f"{stem}.pdf"
    if meta is None or not html_path.exists():
        return templates.TemplateResponse(
            request,
            "saas/app.html",
            _ctx(request, error="Rešerše nenalezena. Spusťte novou."),
            status_code=404,
        )
    from app.models import SitePack

    pack = SitePack.model_validate(meta["pack"])
    return templates.TemplateResponse(request, "saas/results.html", _ctx(
            request,
            pack=pack,
            stem=stem,
            html_abs=str(html_path.resolve()),
            pdf_abs=str(pdf_path.resolve()) if pdf_path.exists() else None,
            pdf_ready=pdf_path.exists(),
            badges=pack.layer_badges_summary(),
        ),
    )


@app.get("/files/{name}")
def files(name: str):
    path = (OUTPUT / name).resolve()
    if not str(path).startswith(str(OUTPUT.resolve())) or not path.exists():
        return HTMLResponse("Not found", status_code=404)
    if path.suffix == ".pdf":
        return FileResponse(
            path,
            media_type="application/pdf",
            filename=path.name,
            headers={"Content-Disposition": f'attachment; filename="{path.name}"'},
        )
    media = "application/json" if path.suffix == ".json" else "text/html; charset=utf-8"
    return FileResponse(path, media_type=media, filename=path.name)


@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    if current_user(request):
        return RedirectResponse("/app", status_code=303)
    return templates.TemplateResponse(request, "saas/login.html", _ctx(request, error=None))


@app.post("/login")
async def login_post(request: Request, email: str = Form(""), password: str = Form("")):
    ok, msg, user = authenticate(email, password)
    if not ok or user is None:
        return templates.TemplateResponse(
            request,
            "saas/login.html",
            _ctx(request, error=msg),
            status_code=400,
        )
    login_session(request, user)
    return RedirectResponse("/app", status_code=303)


@app.get("/register", response_class=HTMLResponse)
def register_get(request: Request):
    if current_user(request):
        return RedirectResponse("/app", status_code=303)
    return templates.TemplateResponse(request, "saas/register.html", _ctx(request, error=None))


@app.post("/register")
async def register_post(
    request: Request,
    email: str = Form(""),
    password: str = Form(""),
    name: str = Form(""),
):
    ok, msg, user = register_user(email, password, name)
    if not ok or user is None:
        return templates.TemplateResponse(
            request,
            "saas/register.html",
            _ctx(request, error=msg),
            status_code=400,
        )
    login_session(request, user)
    return RedirectResponse("/app", status_code=303)


@app.post("/logout")
@app.get("/logout")
def logout(request: Request):
    logout_session(request)
    return RedirectResponse("/", status_code=303)


@app.get("/healthz")
def healthz():
    return health()


@app.get("/health")
def health():
    return {
        "ok": True,
        "product": "SitePack Pro",
        "country": "CZ",
        "surface": "saas-web",
        "ownership": False,
        "outreach": False,
    }

if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", "8787"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
