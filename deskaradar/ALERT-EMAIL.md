# DeskaRadar — alert e-mail setup

## What it does

When a user has **Alerty zapnuté**, a non-empty **e-mail**, and a **live** feed refresh succeeds, DeskaRadar sends a digest of **new** high/medium leads from the last 24 hours that match their prefs (`high_only`, municipalities).

Dedup: SQLite table `alert_sent` `(user_key, lead_key)` — same lead is not re-mailed to the same account.

UI: Alerty tab → **Poslat zkušební e-mail** · status line shows configured vs missing key.

## Render dashboard

1. Open the `deskaradar` service → **Environment**.
2. Add:
   - `RESEND_API_KEY` = (from https://resend.com/api-keys)
   - `ALERT_FROM_EMAIL` = a sender you verified in Resend (e.g. `alerts@yourdomain.com` or Resend onboarding address)
   - Optional: `PUBLIC_APP_URL=https://deskaradar.onrender.com`
3. Save / redeploy so the new env is live.
4. Log in at https://deskaradar.onrender.com → Alerty → set your e-mail → **Poslat zkušební e-mail**.

### SMTP fallback (instead of Resend)

Unset `RESEND_API_KEY` and set:

```
SMTP_HOST=...
SMTP_PORT=587
SMTP_USER=...
SMTP_PASS=...
SMTP_TLS=1
ALERT_FROM_EMAIL=noreply@example.com
```

## Local smoke (no key)

```bash
cd /workspace/deskaradar/app
PYTHONPATH=/workspace/deskaradar .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8765
curl -s http://127.0.0.1:8765/api/health | jq '{ok,data_mode,sample_label,attribution}'
# login cookie then:
curl -s -b cookies.txt http://127.0.0.1:8765/api/alerts/status
# expect: {"email_configured":false,"provider":null,...}
curl -s -b cookies.txt -X POST http://127.0.0.1:8765/api/alerts/send-test
# expect HTTP 503 + actionable Czech message
```

With a key: set `RESEND_API_KEY` in the shell before uvicorn, save prefs with a real inbox, then POST `/api/alerts/send-test`.

## API

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET | `/api/alerts/status` | yes | `{ email_configured, provider: "resend"\|"smtp"\|null }` |
| POST | `/api/alerts/send-test` | yes | one test mail to `prefs.email`; **503** if not configured |
| GET/PUT | `/api/alert-prefs` | yes | includes `email`, `enabled`, `high_only`, `municipalities` |

## Badge DoD (related)

User-facing mode badge is only **Živá data** or **Ukázka**. Live responses omit `sample_label`. Fixture uses label „Ukázková data“ and provider id `ukazka` (never `fixture` in UI notes).
