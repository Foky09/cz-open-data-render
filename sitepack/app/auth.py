"""Account stub — fake register/login + cookie session. NOT real auth security."""

from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any, Optional

from fastapi import Request

ACCOUNTS_PATH = Path(__file__).resolve().parent.parent / "data" / "accounts" / "users.json"
SESSION_COOKIE = "sp_session"
# Plaintext passwords on purpose — stub only, never production.
_DEMO_USERS: dict[str, dict[str, Any]] = {
    "demo@sitepack.cz": {
        "email": "demo@sitepack.cz",
        "password": "demo",
        "name": "Demo uživatel",
        "id": "u-demo",
    }
}


def _load() -> dict[str, dict[str, Any]]:
    if ACCOUNTS_PATH.exists():
        try:
            raw = json.loads(ACCOUNTS_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                return {**_DEMO_USERS, **raw}
        except json.JSONDecodeError:
            pass
    return dict(_DEMO_USERS)


def _save(users: dict[str, dict[str, Any]]) -> None:
    ACCOUNTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Persist only non-seed users
    persist = {k: v for k, v in users.items() if k not in _DEMO_USERS}
    ACCOUNTS_PATH.write_text(json.dumps(persist, ensure_ascii=False, indent=2), encoding="utf-8")


def register_user(email: str, password: str, name: str = "") -> tuple[bool, str, Optional[dict]]:
    email = email.strip().lower()
    if not email or "@" not in email:
        return False, "Zadejte platný e-mail.", None
    if len(password) < 3:
        return False, "Heslo musí mít alespoň 3 znaky (stub).", None
    users = _load()
    if email in users:
        return False, "Účet s tímto e-mailem už existuje.", None
    user = {
        "email": email,
        "password": password,  # stub — plaintext
        "name": (name or email.split("@")[0]).strip(),
        "id": f"u-{secrets.token_hex(4)}",
    }
    users[email] = user
    _save(users)
    return True, "Účet vytvořen (stub session).", user


def authenticate(email: str, password: str) -> tuple[bool, str, Optional[dict]]:
    email = email.strip().lower()
    users = _load()
    user = users.get(email)
    if not user or user.get("password") != password:
        return False, "Neplatný e-mail nebo heslo.", None
    return True, "Přihlášeno.", user


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {"id": user["id"], "email": user["email"], "name": user.get("name") or user["email"]}


def current_user(request: Request) -> Optional[dict[str, Any]]:
    sess = request.session
    raw = sess.get("user")
    if not isinstance(raw, dict) or not raw.get("email"):
        return None
    return raw


def login_session(request: Request, user: dict[str, Any]) -> None:
    request.session["user"] = public_user(user)


def logout_session(request: Request) -> None:
    request.session.clear()
