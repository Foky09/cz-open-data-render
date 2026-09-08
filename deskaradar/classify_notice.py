#!/usr/bin/env python3
"""DeskaRadar MVP — rule-based notice classifier (no scraping).

classify(notice) -> {label, category, confidence, confidence_score, matched_terms, parcel_hints}
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field, asdict
from typing import Any

# --- taxonomy ---
LABEL_STAVEBNI = "stavebni_zamer"
LABEL_NOISE = "noise"
LABEL_UNKNOWN = "unknown"

CATEGORY_ORDER = [
    ("eia_zamer", "eia"),
    ("zmena_uzemniho_planu", "up"),
    ("povoleni_zameru", "pz"),
    ("spolecne_rizeni", "spol"),
    ("uzemni_rozhodnuti", "ur"),
    ("stavebni_povoleni", "sp"),
    ("zahajeni_rizeni", "zah"),
    ("jine_stavebni", "jine"),
]


def fold(text: str) -> str:
    """Lowercase + NFKC; keep diacritics for primary matching."""
    return unicodedata.normalize("NFKC", text or "").lower().strip()


def collapse(text: str) -> str:
    return re.sub(r"\s+", " ", fold(text))


# Strong include phrases → (category_key, phrase)
STRONG_INCLUDE: list[tuple[str, str]] = [
    ("eia", "oznámení záměru"),
    ("eia", "zjišťovací řízení"),
    ("eia", "posuzování vlivů"),
    ("eia", "dokumentace eia"),
    ("eia", "navazující řízení"),
    ("eia", "eia"),
    ("up", "změna územního plánu"),
    ("up", "změny územního plánu"),
    ("up", "návrh změny územního plánu"),
    ("up", "návrh změny úp"),
    ("up", "veřejné projednání návrhu změny"),
    ("up", "zásady územního rozvoje"),
    ("pz", "povolení záměru"),
    ("pz", "řízení o povolení záměru"),
    ("pz", "povolení ve zrychleném řízení"),
    ("sp", "povolení stavby"),
    ("sp", "rozhodnutí povolení stavby"),
    ("sp", "rozhodnutí o povolení stavby"),
    ("pz", "rozhodnutí o povolení záměru"),
    ("spol", "společné povolení"),
    ("spol", "společné rozhodnutí"),
    ("spol", "společné řízení"),
    ("spol", "ú+s rozhodnutí"),
    ("ur", "územní rozhodnutí"),
    ("ur", "územní souhlas"),
    ("sp", "stavební povolení"),
    ("zah", "zahájení územního řízení"),
    ("zah", "zahájení stavebního řízení"),
    ("zah", "zahájení společného řízení"),
    ("zah", "oznámení zahájení územního řízení"),
    ("zah", "oznámení zahájení stavebního řízení"),
    ("zah", "oznámení zahájení společného řízení"),
]

WEAK_INCLUDE = [
    "veřejná vyhláška",
    "stavební úřad",
    "úřad územního plánování",
    "oznámení zahájení řízení",
    "zahájení řízení",
    "pokračování řízení",
    "prodloužení platnosti",
    "novostavba",
    "rodinný dům",
    "bytový dům",
    "přípojka",
    "kabelizace",
    "průmyslov",
]

# standalone tokens / short forms checked with word-ish boundaries
WEAK_TOKENS = [
    (r"\brd\b", "rd"),
    (r"\bčov\b", "čov"),
    (r"\bhala\b", "hala"),
    (r"\bsklad\b", "sklad"),
    (r"\bstudna\b", "studna"),
    (r"\bvodovod\b", "vodovod"),
    (r"\bú\.?\s*r\.?\b", "ú.r."),
]

STRONG_EXCLUDE = [
    "ztráty a nálezy",
    "volby do",
    "obecně závazná vyhláška o místním poplatku",
    "místní poplatek",
    "rozpočet obce",
    "uzávěrka hospodaření",
    "výběrové řízení na ředitele",
    "konkurz na místo",
    "občanský průkaz",
    "řidičský průkaz",
    "rybářský řád",
    "aktualizace bpej",
    "kulturní akce",
]

PARCEL_RE = re.compile(
    r"(?:p\.?\s*p\.?\s*č\.?|parc\.?\s*č\.?|p\.?\s*č\.?)\s*(\d+(?:/\d+)?)",
    re.IGNORECASE,
)
KU_RE = re.compile(
    r"k\.?\s*ú\.?\s+([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽa-záčďéěíňóřšťúůýž][\w\-]*(?:\s+[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽa-záčďéěíňóřšťúůýž][\w\-]*){0,3})",
    re.IGNORECASE,
)


@dataclass
class ClassifyResult:
    label: str
    category: str | None
    confidence: str
    confidence_score: float
    matched_terms: list[str] = field(default_factory=list)
    parcel_hints: list[dict[str, Any]] = field(default_factory=list)
    ku_hints: list[str] = field(default_factory=list)
    flags: dict[str, bool] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _find_phrases(text: str, phrases: list[str]) -> list[str]:
    hits = []
    for p in phrases:
        if p in text:
            hits.append(p)
    return hits


def _category_from_keys(keys: set[str]) -> str | None:
    for cat, key in CATEGORY_ORDER:
        if key in keys:
            return cat
    return None


def extract_hints(raw: str) -> tuple[list[dict[str, Any]], list[str]]:
    parcels = [{"raw": m.group(0), "parcel": m.group(1), "ku": None} for m in PARCEL_RE.finditer(raw)]
    kus = [m.group(1).strip() for m in KU_RE.finditer(raw)]
    # de-dupe ku preserving order
    seen: set[str] = set()
    ku_out = []
    for k in kus:
        kl = k.lower()
        if kl not in seen:
            seen.add(kl)
            ku_out.append(k)
    return parcels, ku_out


def classify(notice: dict[str, Any] | str) -> ClassifyResult:
    """Classify a notice dict or bare title string."""
    if isinstance(notice, str):
        title, excerpt = notice, ""
    else:
        title = notice.get("title") or ""
        excerpt = notice.get("excerpt") or notice.get("raw_excerpt") or ""

    raw = f"{title}\n{excerpt}".strip()
    text = collapse(raw)

    strong_hits: list[tuple[str, str]] = []
    for key, phrase in STRONG_INCLUDE:
        if phrase in text:
            strong_hits.append((key, phrase))

    weak_hits = _find_phrases(text, WEAK_INCLUDE)
    for pat, name in WEAK_TOKENS:
        if re.search(pat, text):
            weak_hits.append(name)

    exclude_hits = _find_phrases(text, STRONG_EXCLUDE)
    parcels, kus = extract_hints(raw)

    matched = [p for _, p in strong_hits] + weak_hits
    # unique preserve order
    seen_m: set[str] = set()
    matched_terms = []
    for m in matched:
        if m not in seen_m:
            seen_m.add(m)
            matched_terms.append(m)

    keys = {k for k, _ in strong_hits}
    category = _category_from_keys(keys)
    conflict = bool(strong_hits and exclude_hits)

    # Decision tree
    if strong_hits and not exclude_hits:
        score = 0.9 + min(0.08, 0.02 * (len(strong_hits) - 1))
        return ClassifyResult(
            label=LABEL_STAVEBNI,
            category=category or "jine_stavebni",
            confidence="high",
            confidence_score=round(score, 2),
            matched_terms=matched_terms,
            parcel_hints=parcels,
            ku_hints=kus,
            flags={"conflict": False, "needs_review": False},
        )

    if strong_hits and exclude_hits:
        return ClassifyResult(
            label=LABEL_STAVEBNI,
            category=category or "jine_stavebni",
            confidence="medium",
            confidence_score=0.7,
            matched_terms=matched_terms + [f"exclude:{e}" for e in exclude_hits],
            parcel_hints=parcels,
            ku_hints=kus,
            flags={"conflict": True, "needs_review": True},
        )

    if exclude_hits and not strong_hits:
        return ClassifyResult(
            label=LABEL_NOISE,
            category=None,
            confidence="high",
            confidence_score=0.95,
            matched_terms=[f"exclude:{e}" for e in exclude_hits],
            parcel_hints=parcels,
            ku_hints=kus,
            flags={"conflict": False, "needs_review": False},
        )

    # Weak path: need ≥2 weak cues, or 1 procedure-ish + 1 object-ish
    procedure_weak = {
        "veřejná vyhláška",
        "stavební úřad",
        "úřad územního plánování",
        "oznámení zahájení řízení",
        "zahájení řízení",
        "pokračování řízení",
        "prodloužení platnosti",
    }
    object_weak = {
        "novostavba",
        "rodinný dům",
        "bytový dům",
        "rd",
        "čov",
        "přípojka",
        "kabelizace",
        "hala",
        "sklad",
        "studna",
        "vodovod",
        "průmyslov",
    }
    weak_set = set(weak_hits)
    n_proc = len(weak_set & procedure_weak)
    n_obj = len(weak_set & object_weak)

    if n_proc and n_obj:
        return ClassifyResult(
            label=LABEL_STAVEBNI,
            category="zahajeni_rizeni" if "zahájení řízení" in weak_set or "oznámení zahájení řízení" in weak_set else "jine_stavebni",
            confidence="medium",
            confidence_score=0.65,
            matched_terms=matched_terms,
            parcel_hints=parcels,
            ku_hints=kus,
            flags={"conflict": False, "needs_review": False},
        )

    if len(weak_set) >= 2:
        return ClassifyResult(
            label=LABEL_STAVEBNI,
            category="jine_stavebni",
            confidence="medium",
            confidence_score=0.55,
            matched_terms=matched_terms,
            parcel_hints=parcels,
            ku_hints=kus,
            flags={"conflict": False, "needs_review": True},
        )

    if weak_set:
        return ClassifyResult(
            label=LABEL_UNKNOWN,
            category=None,
            confidence="low",
            confidence_score=0.35,
            matched_terms=matched_terms,
            parcel_hints=parcels,
            ku_hints=kus,
            flags={"conflict": False, "needs_review": True},
        )

    return ClassifyResult(
        label=LABEL_NOISE,
        category=None,
        confidence="medium",
        confidence_score=0.6,
        matched_terms=[],
        parcel_hints=parcels,
        ku_hints=kus,
        flags={"conflict": False, "needs_review": False},
    )


# --- examples / self-check ---
EXAMPLES: list[tuple[str, str, str | None]] = [
    ("povolení záměru RD Jistebnice", LABEL_STAVEBNI, "povoleni_zameru"),
    ("Územní rozhodnutí Cetin Orlov", LABEL_STAVEBNI, "uzemni_rozhodnuti"),
    ("Stavební povolení účelové komunikace Božejovice", LABEL_STAVEBNI, "stavebni_povoleni"),
    ("oznámení zahájení územního řízení", LABEL_STAVEBNI, "zahajeni_rizeni"),
    (
        "Oznámení záměru – hala pro výrobu, k.ú. Lhota, p.p.č. 816/1",
        LABEL_STAVEBNI,
        "eia_zamer",
    ),
    (
        "VEŘEJNÁ VYHLÁŠKA – veřejné projednání návrhu změny č. 2 územního plánu Haluzice",
        LABEL_STAVEBNI,
        "zmena_uzemniho_planu",
    ),
    ("společné povolení a povolení nakládání s vodami", LABEL_STAVEBNI, "spolecne_rizeni"),
    ("Ztráty a nálezy – klíče", LABEL_NOISE, None),
    ("Výběrové řízení na ředitele ZŠ", LABEL_NOISE, None),
    ("Veřejná vyhláška", LABEL_UNKNOWN, None),
    ("Zahájení řízení studna Nehonín", LABEL_STAVEBNI, "zahajeni_rizeni"),
    ("aktualizace BPEJ Chlum u Jistebnice", LABEL_NOISE, None),
]


def _run_examples() -> int:
    failed = 0
    print(f"{'title':60} {'label':16} {'category':22} conf  ok")
    print("-" * 110)
    for title, exp_label, exp_cat in EXAMPLES:
        r = classify(title)
        ok = r.label == exp_label and (exp_cat is None or r.category == exp_cat)
        if not ok:
            failed += 1
        mark = "✓" if ok else "✗"
        cat = r.category or "—"
        print(f"{title[:60]:60} {r.label:16} {cat:22} {r.confidence:5} {mark}")
        if r.parcel_hints or r.ku_hints:
            print(f"  hints parcels={r.parcel_hints} ku={r.ku_hints}")
        if not ok:
            print(f"  expected label={exp_label} category={exp_cat} matched={r.matched_terms}")
    print("-" * 110)
    print(f"failed: {failed}/{len(EXAMPLES)}")
    return failed


if __name__ == "__main__":
    raise SystemExit(_run_examples())
