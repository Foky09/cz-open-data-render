#!/usr/bin/env python3
"""DeskaRadar Day-1→2 — JMK daily lead digest from official OFN JSON-LD feeds.

Fetches municipal (+ optional kraj) úřední deska open-data, classifies notices,
writes markdown digest with stavebni_zamer leads (high/medium confidence).

Usage:
  python3 daily_digest.py
  python3 daily_digest.py --date 2026-09-08
  python3 daily_digest.py --no-kraj
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import time
import urllib3
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests

from classify_notice import LABEL_STAVEBNI, classify

# --- config ---
ROOT = Path(__file__).resolve().parent
DIGEST_DIR = ROOT / "digests"
TZ = ZoneInfo("Europe/Prague")
USER_AGENT = "DeskaRadar-research/0.1 (+OFN digest MVP; polite sequential fetch)"
TIMEOUT = 25
PAUSE_BETWEEN_FEEDS_S = 0.4

# Official OFN / open-data URLs only (from day1-feeds.md). No eDesky HTML scrape.
FEEDS: list[dict[str, Any]] = [
    {
        "id": "brno",
        "name": "Brno (SMB)",
        "url": "https://edeska.brno.cz/eDeska/opendata",
        # Incomplete intermediate CA chain from some egresses → verify=False only here.
        "tls_insecure": True,
        "kind": "municipality",
    },
    {
        "id": "breclav",
        "name": "Břeclav",
        "url": "https://sluzby.breclav.eu/opendata/ODTURD02.json",
        "kind": "municipality",
    },
    {
        "id": "pohorelice",
        "name": "Pohořelice",
        "url": "https://www.pohorelice.cz/api/open-data/ofn67a4bd23b94a8",
        "kind": "municipality",
    },
    {
        "id": "hodonin",
        "name": "Hodonín",
        "url": "https://www.hodonin.eu/opendata-uredni-deska",
        "kind": "municipality",
    },
    {
        "id": "znojmo",
        "name": "Znojmo",
        "url": "https://www.znojmocity.cz/opendata-uredni-deska",
        "kind": "municipality",
    },
    {
        "id": "vyskov",
        "name": "Vyškov",
        "url": "https://www.vyskov-mesto.cz/opendata-uredni-deska",
        "kind": "municipality",
    },
    {
        "id": "tisnov",
        "name": "Tišnov",
        "url": "https://www.tisnov.cz/opendata-uredni-deska",
        "kind": "municipality",
    },
    {
        "id": "boskovice",
        "name": "Boskovice",
        "url": "https://www.boskovice.cz/data/308",
        "kind": "municipality",
    },
    {
        "id": "veseli",
        "name": "Veselí nad Moravou",
        "url": "https://www.veseli-nad-moravou.cz/opendata-uredni-deska",
        "kind": "municipality",
    },
    {
        "id": "moravany",
        "name": "Moravany u Brna",
        "url": "https://www.moravanyubrna.cz/api/office-desk",
        "kind": "municipality",
    },
    {
        "id": "jmk",
        "name": "Jihomoravský kraj (KÚ)",
        "url": "https://opendata.jmk.cz/data/ude.json",
        "kind": "kraj",
    },
]

# Place / org tokens we should not treat as personal names when redacting.
PLACE_WHITELIST = {
    "brno",
    "břeclav",
    "breclav",
    "pohořelice",
    "pohorelice",
    "hodonín",
    "hodonin",
    "znojmo",
    "vyškov",
    "vyskov",
    "tišnov",
    "tisnov",
    "boskovice",
    "veselí",
    "veseli",
    "moravany",
    "jihomoravský",
    "morava",
    "moravě",
    "česká",
    "české",
    "město",
    "obec",
    "úřad",
    "kraj",
    "republiky",
    "státní",
    "veřejná",
    "vyhláška",
    "rozhodnutí",
    "povolení",
    "záměru",
    "stavby",
    "řízení",
    "novostavba",
    "rodinný",
    "bytový",
}

TITLE_PREFIX_RE = re.compile(
    r"\b(?:Ing|Mgr|Bc|JUDr|MUDr|Ph\.?D|DiS|Mba|MVDr|RNDr|PharmDr|ThDr|prof|doc)\.?\s*",
    re.IGNORECASE,
)

# Two+ capitalized Czech-ish name tokens (First Last [Last])
PERSON_NAME_RE = re.compile(
    r"\b([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]{2,})"
    r"(?:\s+([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]{2,}(?:ová|á|ý|í|ek|ák|ík|ný|ský|cký)?))+"
)


def lang_text(value: Any) -> str:
    """Normalize OFN multilingual string / plain string / None → str."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("cs", "en", "sk"):
            if key in value and value[key]:
                return str(value[key]).strip()
        for v in value.values():
            if isinstance(v, str) and v.strip():
                return v.strip()
    return str(value).strip()


def strip_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def extract_date(vyveseni: Any) -> str | None:
    if not vyveseni:
        return None
    if isinstance(vyveseni, str):
        return vyveseni[:10]
    if isinstance(vyveseni, dict):
        for key in ("datum", "date", "datum_a_čas", "datum_a_cas"):
            if key in vyveseni and vyveseni[key]:
                return str(vyveseni[key])[:10]
    return None


def redact_names(title: str) -> str:
    """Best-effort redaction of obvious personal names in notice titles."""
    if not title:
        return title
    cleaned = TITLE_PREFIX_RE.sub("", title)

    def repl(m: re.Match[str]) -> str:
        parts = [p for p in m.groups() if p]
        # full match text tokens
        tokens = m.group(0).split()
        lower_tokens = [t.lower().rstrip(".,;:") for t in tokens]
        if any(t in PLACE_WHITELIST for t in lower_tokens):
            return m.group(0)
        # keep street-like / org-like ALLCAPS-ish sequences alone
        if len(parts) < 1:
            return m.group(0)
        return "[jméno]"

    return PERSON_NAME_RE.sub(repl, cleaned)


def parse_informace(data: Any, municipality: str) -> list[dict[str, Any]]:
    """Walk OFN JSON-LD and return normalized notice dicts."""
    notices: list[dict[str, Any]] = []

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            info = obj.get("informace")
            if isinstance(info, list):
                for item in info:
                    if not isinstance(item, dict):
                        continue
                    title = lang_text(item.get("název") or item.get("nazev"))
                    if not title:
                        continue
                    popis = strip_html(lang_text(item.get("popis")))
                    url = item.get("url") or item.get("iri") or ""
                    if isinstance(url, dict):
                        url = lang_text(url)
                    published = extract_date(item.get("vyvěšení") or item.get("vyveseni"))
                    notices.append(
                        {
                            "municipality": municipality,
                            "title": title,
                            "excerpt": popis[:500] if popis else "",
                            "url": str(url) if url else "",
                            "published_at": published,
                            "iri": item.get("iri") or "",
                        }
                    )
            for v in obj.values():
                if isinstance(v, (dict, list)):
                    walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)

    walk(data)
    return notices


def fetch_feed(feed: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return (status_row, notices). Continues on failure."""
    status: dict[str, Any] = {
        "id": feed["id"],
        "name": feed["name"],
        "url": feed["url"],
        "ok": False,
        "http": None,
        "items": 0,
        "error": None,
        "tls_note": None,
    }
    headers = {"User-Agent": USER_AGENT, "Accept": "application/ld+json, application/json, */*"}
    # Prefer system/CA bundle verify. Brno may need a one-shot insecure retry
    # (incomplete intermediate CA from some egresses — day1-feeds.md).
    try:
        resp = requests.get(feed["url"], headers=headers, timeout=TIMEOUT, verify=True)
        status["http"] = resp.status_code
        resp.raise_for_status()
        data = resp.json()
        notices = parse_informace(data, feed["name"])
        status["ok"] = True
        status["items"] = len(notices)
        return status, notices
    except requests.exceptions.SSLError as ssl_exc:
        if not feed.get("tls_insecure"):
            status["error"] = f"SSLError: {ssl_exc}"
            return status, []
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        status["tls_note"] = "verify=False retry (incomplete CA chain) — residual Brno TLS blocker"
        try:
            resp = requests.get(feed["url"], headers=headers, timeout=TIMEOUT, verify=False)
            status["http"] = resp.status_code
            resp.raise_for_status()
            data = resp.json()
            notices = parse_informace(data, feed["name"])
            status["ok"] = True
            status["items"] = len(notices)
            return status, notices
        except Exception as exc:  # noqa: BLE001
            status["error"] = f"{type(exc).__name__}: {exc}"
            return status, []
    except Exception as exc:  # noqa: BLE001 — isolate per-feed failures
        status["error"] = f"{type(exc).__name__}: {exc}"
        return status, []


def classify_leads(notices: list[dict[str, Any]]) -> list[dict[str, Any]]:
    leads: list[dict[str, Any]] = []
    for n in notices:
        result = classify({"title": n["title"], "excerpt": n.get("excerpt") or ""})
        if result.label != LABEL_STAVEBNI:
            continue
        if result.confidence not in ("high", "medium"):
            continue
        leads.append(
            {
                **n,
                "title_redacted": redact_names(n["title"]),
                "category": result.category,
                "confidence": result.confidence,
                "confidence_score": result.confidence_score,
                "matched_terms": result.matched_terms,
                "flags": result.flags,
            }
        )
    # newest first; stable by municipality
    leads.sort(
        key=lambda x: (x.get("published_at") or "", x.get("municipality") or "", x.get("title") or ""),
        reverse=True,
    )
    return leads


def render_digest(
    digest_date: date,
    statuses: list[dict[str, Any]],
    leads: list[dict[str, Any]],
) -> str:
    now_pt = datetime.now(TZ).strftime("%Y-%m-%d %H:%M %Z")
    ok_n = sum(1 for s in statuses if s["ok"])
    fail_n = len(statuses) - ok_n
    today_s = digest_date.isoformat()
    today_leads = [L for L in leads if L.get("published_at") == today_s]

    lines: list[str] = [
        f"# DeskaRadar — JMK denní digest ({today_s})",
        "",
        f"**Generated:** {now_pt}  ",
        f"**Kraj:** Jihomoravský  ",
        f"**Feeds OK/fail:** {ok_n}/{fail_n}  ",
        f"**Leads (stavebni_zamer high/medium):** {len(leads)}  "
        f"(z toho vyvěšeno {today_s}: {len(today_leads)})",
        "",
        "Zdroje: oficiální OFN JSON-LD úřední desky (NKOD). Bez scrape eDesky HTML.",
        "Osobní jména v názvech jsou redigována heuristikou (`[jméno]`) — ověřte na zdroji.",
        "",
        "---",
        "",
        "## Fetch status",
        "",
        "| Municipality | HTTP | Items | Status | Note |",
        "|---|---:|---:|---|---|",
    ]
    for s in statuses:
        if s["ok"]:
            st = "OK"
            note = s.get("tls_note") or ""
        else:
            st = "FAIL"
            note = (s.get("error") or "")[:120]
        http = s["http"] if s["http"] is not None else "—"
        lines.append(
            f"| {s['name']} | {http} | {s['items']} | {st} | {note} |"
        )

    lines.extend(["", "---", "", "## Leads — stavební / záměr", ""])

    if not leads:
        lines.append("_Žádné high/medium `stavebni_zamer` leady v aktuálních feedech._")
        lines.append("")
    else:
        # Group by municipality for readability
        by_muni: dict[str, list[dict[str, Any]]] = {}
        for L in leads:
            by_muni.setdefault(L["municipality"], []).append(L)

        for muni in sorted(by_muni.keys()):
            group = by_muni[muni]
            lines.append(f"### {muni} ({len(group)})")
            lines.append("")
            for L in group:
                pub = L.get("published_at") or "?"
                conf = L["confidence"]
                cat = L.get("category") or "—"
                title = L["title_redacted"].replace("|", "\\|")
                url = L.get("url") or ""
                terms = ", ".join(L.get("matched_terms") or [])[:120]
                badge = "🆕 " if pub == today_s else ""
                if url:
                    lines.append(f"- {badge}**{title}**  ")
                    lines.append(
                        f"  _{pub}_ · `{cat}` · conf **{conf}** · [zdroj]({url})  "
                    )
                else:
                    lines.append(f"- {badge}**{title}**  ")
                    lines.append(f"  _{pub}_ · `{cat}` · conf **{conf}**  ")
                if terms:
                    lines.append(f"  matched: {terms}")
                lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## Attribution / compliance",
            "",
            "- Brno (SMB): CC BY 4.0 — uvádějte Magistrát města Brna / open data.",
            "- Ostatní obce: otevřená data dle NKOD (často bez autorského díla / DB).",
            "- JMK krajský feed: viz NKOD / opendata.jmk.cz (CC0 na sui generis DB).",
            "- Deep-link na `url` úřední desky je zdroj pravdy; digest je odvozený přehled.",
            "",
            f"_DeskaRadar digest MVP · {today_s}_",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DeskaRadar JMK daily OFN digest")
    parser.add_argument(
        "--date",
        help="Digest date YYYY-MM-DD (default: today Europe/Prague)",
        default=None,
    )
    parser.add_argument(
        "--no-kraj",
        action="store_true",
        help="Skip Jihomoravský kraj KÚ feed",
    )
    parser.add_argument(
        "--out",
        help="Output path (default: digests/YYYY-MM-DD-jmk.md)",
        default=None,
    )
    args = parser.parse_args(argv)

    if args.date:
        digest_date = date.fromisoformat(args.date)
    else:
        digest_date = datetime.now(TZ).date()

    feeds = [f for f in FEEDS if not (args.no_kraj and f.get("kind") == "kraj")]

    statuses: list[dict[str, Any]] = []
    all_notices: list[dict[str, Any]] = []

    for i, feed in enumerate(feeds):
        if i:
            time.sleep(PAUSE_BETWEEN_FEEDS_S)
        print(f"Fetching {feed['name']} …", flush=True)
        status, notices = fetch_feed(feed)
        statuses.append(status)
        if status["ok"]:
            print(f"  OK http={status['http']} items={status['items']}", flush=True)
            all_notices.extend(notices)
        else:
            print(f"  FAIL {status['error']}", flush=True)

    leads = classify_leads(all_notices)
    print(
        f"Classified leads: {len(leads)} / notices={len(all_notices)}",
        flush=True,
    )

    DIGEST_DIR.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out) if args.out else DIGEST_DIR / f"{digest_date.isoformat()}-jmk.md"
    body = render_digest(digest_date, statuses, leads)
    out_path.write_text(body, encoding="utf-8")
    print(f"Wrote {out_path}", flush=True)

    ok_n = sum(1 for s in statuses if s["ok"])
    fail_n = len(statuses) - ok_n
    print(f"SUMMARY feeds_ok={ok_n} feeds_fail={fail_n} leads={len(leads)} path={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
