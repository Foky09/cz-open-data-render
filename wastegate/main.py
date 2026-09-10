"""WasteGate SaaS MVP — FastAPI."""
from __future__ import annotations

import os
import json
import re
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from passlib.hash import pbkdf2_sha256
from starlette.middleware.sessions import SessionMiddleware

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
STORE_PATH = DATA / "store.json"
OUTBOX = DATA / "outbox"
DAY1 = ROOT / "day1"
# Prefer workspace Day-1 snapshots (live normalize), then local day1/
_SNAPSHOT_CANDIDATES = [
    Path("/workspace/wastegate/day1/snapshots"),
    DAY1 / "snapshots",
]
WATCHLIST_YAML = DAY1 / "watchlist.example.yaml"
if not WATCHLIST_YAML.exists():
    WATCHLIST_YAML = Path("/workspace/wastegate/day1/watchlist.example.yaml")


def resolve_snapshot() -> Path | None:
    """Newest YYYY-MM-DD.jsonl across known snapshot dirs."""
    best: Path | None = None
    for d in _SNAPSHOT_CANDIDATES:
        if not d.is_dir():
            continue
        for p in d.glob("????-??-??.jsonl"):
            if best is None or p.name > best.name:
                best = p
    return best


SNAPSHOT = resolve_snapshot() or (DAY1 / "snapshots" / "2026-09-08.jsonl")


def snapshot_label_cs(path: Path | None) -> str:
    """Human Czech live-data label — no .jsonl / snapshot jargon."""
    if path is None:
        return "Data registru zatím chybí"
    stem = path.stem  # YYYY-MM-DD
    try:
        d = datetime.strptime(stem, "%Y-%m-%d").date()
        stamp = f"{d.day}. {d.month}. {d.year}"
    except ValueError:
        stamp = stem
    return f"Živá data z registru · aktualizováno {stamp}"

FOOTER = (
    "Zdroj: MŽP ČR – VISOH2 Registr zařízení (veřejný denní export). "
    "MŽP produkt nepodporuje. Data mohou obsahovat osobní údaje."
)
SECRET = "wastegate-dev-secret-change-me"

app = FastAPI(title="WasteGate")
app.add_middleware(SessionMiddleware, secret_key=SECRET, session_cookie="wg_session")
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")
templates = Jinja2Templates(directory=str(ROOT / "templates"))
templates.env.globals["FOOTER"] = FOOTER

def kind_cs(kind: str | None) -> str:
    k = (kind or "").lower()
    return {"facility": "Zařízení", "trader": "Obchodník", "zarizeni": "Zařízení", "obchodnik": "Obchodník"}.get(k, kind or "—")


def status_cs(status: str | None) -> str:
    s = (status or "").strip().lower()
    mapping = {
        "aktivni": "aktivní",
        "active": "aktivní",
        "ukonceno": "ukončeno",
        "ukoncen": "ukončeno",
        "not_found": "nenalezeno",
        "missing": "nenalezeno",
        "unknown": "neznámý",
        "nenalezeno": "nenalezeno",
        "aktivní": "aktivní",
        "ukončeno": "ukončeno",
    }
    return mapping.get(s, status or "—")


def change_cs(summary: str | None) -> str:
    s = (summary or "").strip().lower()
    mapping = {
        "baseline": "Výchozí stav",
        "missing in snapshot": "nenalezeno",
        "status change": "Změna statusu",
        "no change": "Bez změny",
        "unchanged": "Bez změny",
    }
    return mapping.get(s, summary or "—")


def alert_kind_cs(kind: str | None) -> str:
    k = (kind or "").lower()
    return {
        "baseline": "Výchozí přehled",
        "manual": "Výchozí přehled",
        "status_change": "Změna statusu",
        "diff": "Změna statusu",
    }.get(k, kind or "—")

templates.env.filters["kind_cs"] = kind_cs
templates.env.filters["status_cs"] = status_cs
templates.env.filters["change_cs"] = change_cs
templates.env.filters["alert_kind_cs"] = alert_kind_cs


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def empty_store() -> dict[str, Any]:
    return {"users": [], "watchlist": [], "statuses": [], "alerts": [], "seeded": False}


def read_store() -> dict[str, Any]:
    if not STORE_PATH.exists():
        return empty_store()
    return json.loads(STORE_PATH.read_text(encoding="utf-8"))


def write_store(store: dict[str, Any]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_watchlist_yaml(path: Path) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    in_list = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if re.match(r"^watchlist\s*:\s*$", line):
            in_list = True
            continue
        if not in_list:
            continue
        m_id = re.match(r"^\s*-\s*id\s*:\s*(.+)\s*$", line)
        if m_id:
            if current and current.get("id"):
                items.append(current)
            current = {"id": m_id.group(1).strip().strip("\"'")}
            continue
        m_lab = re.match(r"^\s*label\s*:\s*(.+)\s*$", line)
        if m_lab and current is not None:
            val = m_lab.group(1).strip()
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            current["label"] = val
    if current and current.get("id"):
        items.append(current)
    return items


def infer_kind(local_id: str) -> str:
    u = local_id.upper()
    if u.startswith("COP") or u.startswith("CO"):
        return "trader"
    return "facility"


def lookup_statuses(local_ids: list[str], country: str = "CZ") -> dict[str, dict[str, Any]]:
    wanted = {i.upper() for i in local_ids}
    out: dict[str, dict[str, Any]] = {}
    snap = resolve_snapshot() or SNAPSHOT
    if not snap or not Path(snap).exists():
        return out
    with Path(snap).open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            rid = str(row.get("id") or "").upper()
            if rid not in wanted or rid in out:
                continue
            codes = row.get("waste_codes") or []
            out[rid] = {
                "localId": row.get("id"),
                "country": country,
                "kind": "trader" if row.get("kind") == "obchodnik" else infer_kind(rid),
                "status": row.get("status") or "unknown",
                "operatorIco": row.get("operator_ico"),
                "wasteCodeCount": len(codes),
                "wasteCodesSample": codes[:5],
                "exportDate": row.get("export_date"),
                "lastChange": row.get("export_date"),
                "changeSummary": "Výchozí stav",
            }
            if len(out) >= len(wanted):
                break
    return out


def ensure_seeded() -> dict[str, Any]:
    store = read_store()
    if store.get("seeded"):
        return store
    demo_id = str(uuid.uuid4())
    ts = now_iso()
    store["users"] = [{
        "id": demo_id,
        "email": "demo@wastegate.cz",
        "passwordHash": pbkdf2_sha256.hash("demo1234"),
        "createdAt": ts,
    }]
    seeds = parse_watchlist_yaml(WATCHLIST_YAML) if WATCHLIST_YAML.exists() else []
    items = []
    for s in seeds:
        items.append({
            "id": str(uuid.uuid4()),
            "userId": demo_id,
            "country": "CZ",
            "localId": s["id"],
            "kind": infer_kind(s["id"]),
            "label": s.get("label") or s["id"],
            "createdAt": ts,
            "updatedAt": ts,
        })
    store["watchlist"] = items
    found = lookup_statuses([i["localId"] for i in items], "CZ")
    statuses = []
    for item in items:
        st = found.get(item["localId"].upper())
        if st:
            statuses.append(st)
        else:
            statuses.append({
                "localId": item["localId"],
                "country": "CZ",
                "kind": item["kind"],
                "status": "not_found",
                "operatorIco": None,
                "wasteCodeCount": 0,
                "wasteCodesSample": [],
                "exportDate": None,
                "lastChange": None,
                "changeSummary": "nenalezeno",
            })
    store["statuses"] = statuses
    subject = "WasteGate: stav partnerů (2026-09-08)"
    body_lines = [
        "WasteGate alert — 2026-09-08",
        "",
        "Výchozí přehled partnerů",
        "",
    ]
    for item in items:
        st = next((x for x in statuses if x["localId"].upper() == item["localId"].upper()), None)
        body_lines.append(f"{item['localId']} — {item['label']}")
        body_lines.append(f"Status: {status_cs(st['status'] if st else 'unknown')}")
        body_lines.append(f"IČO provozovatele: {(st or {}).get('operatorIco') or '—'}")
        body_lines.append(f"Kódy odpadu: {(st or {}).get('wasteCodeCount', 0)}")
        body_lines.append("")
    body_lines.append("---")
    body_lines.append(FOOTER)
    body = "\n".join(body_lines)
    alert = {
        "id": str(uuid.uuid4()),
        "userId": demo_id,
        "createdAt": "2026-09-08T16:51:00+00:00",
        "subject": subject,
        "body": body,
        "kind": "baseline",
        "partnerIds": [i["localId"] for i in items],
    }
    store["alerts"] = [alert]
    OUTBOX.mkdir(parents=True, exist_ok=True)
    (OUTBOX / f"alert-{alert['id']}.eml.txt").write_text(
        f"To: demo@wastegate.cz\nFrom: alerts@wastegate.local\nSubject: {subject}\n\n{body}\n",
        encoding="utf-8",
    )
    store["seeded"] = True
    write_store(store)
    return store


def current_user(request: Request) -> dict[str, Any] | None:
    uid = request.session.get("user_id")
    if not uid:
        return None
    store = read_store()
    return next((u for u in store["users"] if u["id"] == uid), None)


def require_user(request: Request) -> dict[str, Any] | RedirectResponse:
    user = current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return user


@app.on_event("startup")
def _startup() -> None:
    ensure_seeded()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Public landing; logged-in users go to dashboard."""
    user = current_user(request)
    if user:
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse(request, "landing.html", {"user": None})


@app.get("/signup", response_class=HTMLResponse)
def signup_form(request: Request):
    return templates.TemplateResponse(request, "signup.html", {"error": None})
@app.post("/signup")
def signup(request: Request, email: str = Form(...), password: str = Form(...)):
    store = read_store()
    email = email.strip().lower()
    if any(u["email"] == email for u in store["users"]):
        return templates.TemplateResponse(request, "signup.html", {"error": "Email already registered"}, status_code=400)
    if len(password) < 6:
        return templates.TemplateResponse(request, "signup.html", {"error": "Password min 6 chars"}, status_code=400)
    user = {
        "id": str(uuid.uuid4()),
        "email": email,
        "passwordHash": pbkdf2_sha256.hash(password),
        "createdAt": now_iso(),
    }
    store["users"].append(user)
    write_store(store)
    request.session["user_id"] = user["id"]
    return RedirectResponse("/dashboard", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})
@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    store = read_store()
    email = email.strip().lower()
    user = next((u for u in store["users"] if u["email"] == email), None)
    if not user or not pbkdf2_sha256.verify(password, user["passwordHash"]):
        return templates.TemplateResponse(request, "login.html", {"error": "Invalid email or password"}, status_code=401)
    request.session["user_id"] = user["id"]
    return RedirectResponse("/dashboard", status_code=303)


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    store = read_store()
    items = [w for w in store["watchlist"] if w["userId"] == user["id"]]
    status_by = {s["localId"].upper(): s for s in store.get("statuses", [])}
    rows = []
    for w in items:
        st = status_by.get(w["localId"].upper(), {})
        rows.append({**w, "status": st.get("status", "—"), "operatorIco": st.get("operatorIco"),
                     "wasteCodeCount": st.get("wasteCodeCount", 0), "changeSummary": st.get("changeSummary")})
    snap = resolve_snapshot()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "user": user,
            "rows": rows,
            "data_label": snapshot_label_cs(snap),
            "data_source": "live" if snap else "missing",
        },
    )


@app.get("/watchlist", response_class=HTMLResponse)
def watchlist_page(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    store = read_store()
    items = [w for w in store["watchlist"] if w["userId"] == user["id"]]
    return templates.TemplateResponse(request, "watchlist.html", {"user": user, "items": items, "error": None})


@app.post("/watchlist/add")
def watchlist_add(
    request: Request,
    local_id: str = Form(...),
    label: str = Form(""),
    country: str = Form("CZ"),
):
    user = current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    local_id = local_id.strip().upper()
    country = (country or "CZ").strip().upper()
    store = read_store()
    items = [w for w in store["watchlist"] if w["userId"] == user["id"]]
    if not local_id or len(local_id) < 3:
        return templates.TemplateResponse(
            request,
            "watchlist.html",
            {"user": user, "items": items, "error": "Zadejte platné IČZ / IČOB (min. 3 znaky, např. CZK00551)."},
            status_code=400,
        )
    if any(w["userId"] == user["id"] and w["localId"].upper() == local_id for w in store["watchlist"]):
        return templates.TemplateResponse(
            request,
            "watchlist.html",
            {"user": user, "items": items, "error": "Tento partner už je na watchlistu."},
            status_code=400,
        )
    item = {
        "id": str(uuid.uuid4()),
        "userId": user["id"],
        "country": country,
        "localId": local_id,
        "kind": infer_kind(local_id),
        "label": label.strip() or local_id,
        "createdAt": now_iso(),
        "updatedAt": now_iso()}
    store["watchlist"].append(item)
    if country == "CZ":
        found = lookup_statuses([local_id], "CZ")
        st = found.get(local_id)
        if st:
            store["statuses"] = [s for s in store["statuses"] if s["localId"].upper() != local_id] + [st]
    write_store(store)
    return RedirectResponse("/watchlist", status_code=303)


@app.post("/watchlist/{item_id}/delete")
def watchlist_delete(request: Request, item_id: str):
    user = current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    store = read_store()
    store["watchlist"] = [
        w for w in store["watchlist"] if not (w["id"] == item_id and w["userId"] == user["id"])
    ]
    write_store(store)
    return RedirectResponse("/watchlist", status_code=303)


@app.get("/alerts", response_class=HTMLResponse)
def alerts_list(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    store = read_store()
    alerts = [a for a in store["alerts"] if a["userId"] == user["id"]]
    return templates.TemplateResponse(request, "alerts.html", {"user": user, "alerts": alerts})


@app.get("/alerts/{alert_id}", response_class=HTMLResponse)
def alert_detail(request: Request, alert_id: str):
    user = current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    store = read_store()
    alert = next((a for a in store["alerts"] if a["id"] == alert_id and a["userId"] == user["id"]), None)
    if not alert:
        return RedirectResponse("/alerts", status_code=303)
    status_by = {s["localId"].upper(): s for s in store.get("statuses", [])}
    partners = []
    for pid in alert.get("partnerIds") or []:
        st = status_by.get(str(pid).upper(), {})
        partners.append(
            {
                "localId": pid,
                "status": st.get("status", "—"),
                "operatorIco": st.get("operatorIco"),
                "wasteCodeCount": st.get("wasteCodeCount", 0),
                "changeSummary": st.get("changeSummary"),
            }
        )
    return templates.TemplateResponse(
        request,
        "alert_detail.html",
        {"user": user, "alert": alert, "partners": partners},
    )


@app.post("/alerts/run")
def alerts_run(request: Request):
    """Generate a manual status email for current watchlist (concierge button)."""
    user = current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    store = read_store()
    items = [w for w in store["watchlist"] if w["userId"] == user["id"]]
    status_by = {s["localId"].upper(): s for s in store.get("statuses", [])}
    # refresh CZ statuses from snapshot
    cz_ids = [i["localId"] for i in items if i.get("country") == "CZ"]
    if cz_ids:
        found = lookup_statuses(cz_ids, "CZ")
        for iid, st in found.items():
            store["statuses"] = [s for s in store["statuses"] if s["localId"].upper() != iid] + [st]
        status_by = {s["localId"].upper(): s for s in store["statuses"]}
    date = datetime.now().strftime("%Y-%m-%d")
    subject = f"WasteGate: stav partnerů ({date})"
    lines = [f"WasteGate — {date}", "", f"Partnerů na seznamu: {len(items)}", ""]
    for item in items:
        st = status_by.get(item["localId"].upper(), {})
        lines.append(f"{item['localId']} — {item.get('label') or item['localId']}")
        lines.append(f"Status: {status_cs(st.get('status', 'unknown'))}")
        lines.append(f"IČO provozovatele: {st.get('operatorIco') or '—'}")
        lines.append(f"Kódy odpadu: {st.get('wasteCodeCount', 0)}")
        lines.append("")
    lines.append("---")
    lines.append(FOOTER)
    body = "\n".join(lines)
    alert = {
        "id": str(uuid.uuid4()),
        "userId": user["id"],
        "createdAt": now_iso(),
        "subject": subject,
        "body": body,
        "kind": "manual",
        "partnerIds": [i["localId"] for i in items],
    }
    store["alerts"].insert(0, alert)
    write_store(store)
    OUTBOX.mkdir(parents=True, exist_ok=True)
    (OUTBOX / f"alert-{alert['id']}.eml.txt").write_text(
        f"To: {user['email']}\nFrom: alerts@wastegate.local\nSubject: {subject}\n\n{body}\n",
        encoding="utf-8",
    )
    return RedirectResponse(f"/alerts/{alert['id']}", status_code=303)


@app.get("/healthz")
def healthz():
    return health()


@app.get("/health")
def health():
    snap = resolve_snapshot()
    return {
        "ok": True,
        "product": "WasteGate",
        "snapshot": str(snap) if snap else None,
        "dataLabel": "live-snapshot" if snap else "missing-snapshot",
        "attribution": FOOTER,
    }

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "3460"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
