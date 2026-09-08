# SpectrumDeadline – Railway deploy

## Service
- Suggested name: `spectrum`
- Stack: Next.js 14 (App Router)

## Railway settings
- **Root Directory:** `spectrum/app`
- **Dockerfile path:** `Dockerfile`

## Start command
```bash
npx next start -H 0.0.0.0 -p $PORT
```

## Port
- Env: `PORT  (Railway injects; Next reads it)
- Local fallback default: **3000**

## Notes
- Client sample load uses relative `fetch("/sample_stations.csv")` – no localhost hardcodes.
- Multi-stage image: `npm ci` + `npm run build`, then `next start`.
- CTU product boundary / no auto-renew messaging unchanged.
