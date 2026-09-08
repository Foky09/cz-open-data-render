# UX Wave Summary — CZ open-data products

Date: 2026-09-08 (PT). Design system: Fraunces + Nunito Sans, paper `#F7F4EF`, ink `#1C1917`, chunky rounded buttons, soft shadows, subtle SVG/CSS doodles. Czech UI copy. No commits (parent handles git).

## Brand accents applied
| App | Accent |
|-----|--------|
| DeskaRadar | terracotta `#E07A5F` |
| SitePack | moss `#3D6B4F` |
| WasteGate | amber `#D97706` |
| CapexPulse | ink blue `#1D4ED8` + pulse lime `#84CC16` |

## DeskaRadar (`deskaradar/`)
**Landing:** public `/` → `static/landing.html` (hero / problem / how-it-works / features / CTA). Logged-in users redirect to `/app`.
**App:** `/app` → polished `static/app.html` (same paper design). Login restyled; demo auth unchanged (`demo` password).
**Functionality beyond cosmetics:**
- Fulltext query filter `q` on `/api/leads` (title / obec / kategorie / matched terms)
- CSV export `/api/leads.csv` (UTF-8 BOM, `;` delimiter) wired to “Export CSV” button
- Clearer empty states already present, restyled

**Files:** `main.py`, `static/landing.html` (new), `static/login.html`, `static/app.html`  
**Synced to:** `/workspace/deskaradar/app/`

## SitePack (`sitepack/`)
**Landing:** upgraded `templates/saas/landing.html` with full sections + CTA.
**Styles:** `static/app.css` + `templates/saas/base.html` (Google Fonts, moss brand, paper bg).
**App/results:** progress steppers (1→2→3), busy state on submit, friendlier PDF-missing error on results.
**Functionality beyond cosmetics:** progress UX + explicit PDF fallback guidance (print HTML if WeasyPrint missing).

**Files:** `static/app.css`, `templates/saas/{base,landing,app,results}.html`  
**Synced to:** `/workspace/sitepack/concierge/`

## WasteGate (`wastegate/`)
**Landing:** new `templates/landing.html` at `/` (signup/login CTAs). Logged-in → `/dashboard`.
**In-app:** amber design system; Czech labels; KPI chips; status badges; empty states on dashboard / watchlist / alerts.
**Functionality beyond cosmetics:**
- IČZ validation message when ID too short / duplicate (Czech)
- Alert detail now shows partner status table (not only raw email body)
- Logout returns to landing

**Files:** `main.py`, `static/style.css`, `templates/{landing,base,dashboard,watchlist,alerts,alert_detail,login,signup}.html`  
**Synced to:** `/workspace/wastegate/app/`

## CapexPulse (`capexpulse/`)
**Split:** `/` → `landing.html` (hero…CTA); `/app` (+ `/index.html`) → movers dashboard.
**App polish:** KPI chips (count / ΣΔ / clean / positive), search by name/IČO, reset filters, Czech empty state, paper+blue/lime design.
**Kept:** `/healthz`, `/data/...` static mount, MONITOR links, metric v2.1 explainer.

**Files:** `main.py`, `landing.html` (new), `index.html`  
**Synced to:** `/workspace/capexpulse/dashboard/`

## Verification
- `python -m py_compile` on `deskaradar/main.py`, `sitepack/app/main.py`, `wastegate/main.py`, `capexpulse/main.py` — OK
- Render start commands / `healthz` paths unchanged in `render.yaml`

## Blockers
- None for this wave. Live OFN / WeasyPrint / VISOH snapshot behaviour depends on runtime data & OS packages (already pre-existing).


## Spectrum (spectrum/)
**Path:** /workspace/cz-open-data-render/spectrum (mirrored into /workspace/spectrum/app)

**Design:** Fraunces + Nunito Sans; teal #0D9488 on paper #F7F4EF, ink #1C1917; chunky buttons, soft shadows, SVG accents; Czech copy.

**Landing (/):** hero, WISP problems, how-it-works, features, CTA to /app and /settings.

**Workspace (/app):** friendlier upload, empty states, clearer bucket calendar. Core: parse, buckets, alerts, export.

**Settings (/settings):** polished ConnectPanel stub + roadmap.

**Build:** next build green; /healthz OK.

**Files:** globals.css, layout.tsx, page.tsx, settings/page.tsx, Workspace.tsx, ConnectPanel.tsx
**Synced to:** /workspace/spectrum/app/src/


## P0 copy remint
Date: 2026-09-08 (PT). Source: `/workspace/ux-audit/paste-ready-cz.md`.

Applied Czech P0 landing copy (eyebrow / H1 / sub / CTAs / 3 benefits / 3 how-it-works / footer) to all five apps; kill-list jargon removed from hero + how-it-works; brand accents unchanged; primary CTAs deep-link into real workflows.

| App | Landing | Primary CTA → |
|-----|---------|---------------|
| CapexPulse | `capexpulse/landing.html` | Ukázat tohoto týdne → `/app` |
| DeskaRadar | `deskaradar/static/landing.html` | Chci dnešní leady → `/login` |
| SitePack | `sitepack/templates/saas/landing.html` (+ base footer) | Ověřit parcelu → `/app` |
| WasteGate | `wastegate/templates/landing.html` | **Hlídat první partnery** → `/signup` |
| Spectrum | `spectrum/src/app/page.tsx` | Ukázat stanice k obnově → `/app` |

Also: CapexPulse `index.html` flag select labels → v pořádku / nová jednotka / zkontrolovat. Mirrors synced (capexpulse/dashboard, deskaradar/app, sitepack/concierge, wastegate/app, spectrum/app). `next build` green; Python mains AST-OK; no git commit.

## P1 in-app empty states & engineering labels
Date: 2026-09-08 (PT). Source: `/workspace/ux-audit/p1-in-app-empty-states.md`.

Applied paste-ready Czech empty states + kill-list jargon out of main UI (metric/flags, cache/query/Stub/OFN chrome, valid_to/settings stubs, FALLBACK/VDP, baseline/facility). Attributions, brand accents, healthz, auth kept. No git commit.

| Order | App | Highlights |
|-------|-----|------------|
| 1 | CapexPulse | Czech flag/typ labels; Prev/Curr → období; empty „Nic v tomto filtru“ + CTA; methodology collapsed as „Jak počítáme skok“; metric/gospel off canvas |
| 2 | DeskaRadar | Login bez Stub/OFN; empty leads/digest/feeds; Pravděpodobnost; Stav zdrojů; footer attribution only |
| 3 | Spectrum | Dropzone ČTÚ export; settings „Připojení ČTÚ (připravujeme)“; Brzy fields; valid_to only in errors |
| 4 | SitePack | Form help + ukázková parcela; human badges Živá/Orientační/Ukázka; Územní plán (orientační) |
| 5 | WasteGate | baseline→Výchozí stav; facility/trader→Zařízení/Obchodník; empty watchlist/alerts; zkušební e-mail; aktivní/ukončeno |

**Verify:** `python -m py_compile` on CapexPulse/DeskaRadar/SitePack/WasteGate mains — OK. Spectrum `next build` green (`/workspace/spectrum/app`). Mirrors synced: capexpulse/dashboard, deskaradar/app, sitepack/concierge, wastegate/app, spectrum/app.
