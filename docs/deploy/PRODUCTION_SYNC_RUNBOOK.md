# Production Sync Runbook — Backend SHA + Frontend /api/version

Use this runbook to fix `/ops/verify` returning `"git_sha":"unknown"` and/or frontend `/api/version` returning 404, and to confirm Deploy Guardian can validate production sync. No architecture changes; configuration and wiring only.

---

## PART 1 — Backend SHA fix (Oracle VM)

**Problem:** `https://api.parlaygorilla.com/ops/verify` returns `{"ok":true,"git_sha":"unknown"}`.

**Cause:** The backend process is not receiving `GIT_SHA` from environment (systemd not loading slot `.env.deploy`, or unit/env order wrong).

Run these steps **on the Oracle VM** (SSH as deploy user or with sudo where noted).

### STEP 1 — Verify active slot

```bash
readlink -f /opt/parlaygorilla/current
```

Confirm the directory exists (e.g. `/opt/parlaygorilla/releases/blue` or `.../releases/green`).

### STEP 2 — Verify deploy env file

```bash
ls -la /opt/parlaygorilla/current/.env.deploy
cat /opt/parlaygorilla/current/.env.deploy
```

You must see:

- `GIT_SHA=<short_sha>`
- `BUILD_TIME=<timestamp>`

If the file is missing or does not contain `GIT_SHA`:

- **FAIL:** "deploy_bluegreen.sh did not write deployment metadata"
- Fix: Run a fresh deploy (GitHub Actions or `deploy_bluegreen.sh`) so the active slot gets `.env.deploy` written. Do not create `.env.deploy` by hand with a fake SHA.

### STEP 3 — Verify systemd loads env in correct order

```bash
sudo systemctl cat parlaygorilla-backend
```

Confirm **exactly** this order:

```ini
EnvironmentFile=-/opt/parlaygorilla/current/.env.deploy
EnvironmentFile=/etc/parlaygorilla/backend.env
```

`.env.deploy` **must** come **first**. If your unit has them reversed or only has `backend.env`:

1. Copy the unit from the repo:  
   `sudo cp /opt/parlaygorilla/current/docs/systemd/parlaygorilla-backend.service /etc/systemd/system/`
2. Or edit:  
   `sudo nano /etc/systemd/system/parlaygorilla-backend.service`  
   and set the two `EnvironmentFile=` lines as above.

### STEP 4 — Reload and restart

```bash
sudo systemctl daemon-reload
sudo systemctl restart parlaygorilla-backend
```

### STEP 5 — Confirm runtime environment has GIT_SHA

```bash
sudo systemctl show parlaygorilla-backend --property=Environment
```

Verify `GIT_SHA=` appears in the output. If it does not, the unit is still not loading `.env.deploy` first, or the file is missing in the current slot (re-check STEP 2 and 3).

### STEP 6 — Local verification (bypass Cloudflare)

```bash
curl -fsS -H "x-ops-token: $OPS_VERIFY_TOKEN" http://127.0.0.1:8000/ops/verify
```

**Expected:** `{"ok":true,"git_sha":"<real_sha>"}` (not `"unknown"`).

If still `"unknown"`, re-check WorkingDirectory in the unit: it must be `/opt/parlaygorilla/current/backend` so that `current` points to the active slot and `.env.deploy` is the one for that slot.

---

## PART 2 — Frontend /api/version fix

**Problem:** `https://parlaygorilla.com/api/version` returns 404.

Possible causes: domain not pointing to Vercel, Vercel project root misconfigured, route not deployed, or Cloudflare proxying wrong origin.

### STEP 1 — Inspect response headers

From your machine:

```bash
curl -I https://parlaygorilla.com
curl -I https://parlaygorilla.com/api/version
```

Check for:

- `server: Vercel` or `x-vercel-id`

If these are missing, traffic is not reaching Vercel (e.g. Cloudflare DNS/origin wrong, or Workers/Pages serving instead).

### STEP 2 — Vercel project configuration

In **Vercel Dashboard** → your project → **Settings**:

- **Root Directory:** `frontend` (required so `app/api/version/route.ts` is used).
- **Framework Preset:** Next.js.
- **Production Branch:** `main`.

If Root Directory was wrong, fix it and trigger a **Production Redeploy**.

### STEP 3 — Route and build in repo

- Route exists: `frontend/app/api/version/route.ts` — GET returns `{ git_sha }` and `Cache-Control: no-store`.
- Build script in `frontend/package.json`:  
  `"build": "NEXT_PUBLIC_GIT_SHA=$VERCEL_GIT_COMMIT_SHA next build"`  
  (Vercel sets `VERCEL_GIT_COMMIT_SHA` at build time; `next.config.js` also sets `NEXT_PUBLIC_GIT_SHA` from it.)

No code change needed if the above match; if build script differed, fix and redeploy.

### STEP 4 — Redeploy and validate

1. In Vercel: **Deployments** → latest production deploy → **Redeploy** (or push to `main`).
2. After deploy:

```bash
curl -fsS https://parlaygorilla.com/api/version
```

**Expected:** `{"git_sha":"<sha>"}` with HTTP 200. If you use `www.parlaygorilla.com`, test that host as well.

---

## PART 3 — Cloudflare (proxy only)

Cloudflare must **only**:

- Provide DNS, SSL, CDN caching, and proxy.

It must **not**:

- Build or deploy the frontend, run Workers, or override origin routing.

**Verify:**

- `parlaygorilla.com` (and www) → DNS/origin pointing to **Vercel**.
- `api.parlaygorilla.com` → DNS/origin pointing to **Oracle backend**.

If the project is linked to Cloudflare Workers or Pages with auto-build, **disable** that build/deploy or unlink the repo so Cloudflare does not run builds. See [CLOUDFLARE_PROXY_ONLY_ARCHITECTURE.md](CLOUDFLARE_PROXY_ONLY_ARCHITECTURE.md).

---

## PART 4 — Final validation

Run from a trusted machine (with `OPS_VERIFY_TOKEN` set for backend).

**Backend:**

```bash
curl -fsS -H "x-ops-token: $OPS_VERIFY_TOKEN" https://api.parlaygorilla.com/ops/verify
```

Expect: `{"ok":true,"git_sha":"<real_sha>"}`.

**Frontend:**

```bash
curl -fsS https://parlaygorilla.com/api/version
```

Expect: `{"git_sha":"<sha>"}` (HTTP 200).

**Production sync script:**

```bash
BACKEND_URL=https://api.parlaygorilla.com OPS_VERIFY_TOKEN=$OPS_VERIFY_TOKEN python backend/scripts/verify_production_sync.py
```

Expect: `PASS: Production backend matches local commit: <sha>` (when local HEAD matches deployed backend).

**Diagnose script:**

```bash
BACKEND_URL=https://api.parlaygorilla.com FRONTEND_URL=https://parlaygorilla.com OPS_VERIFY_TOKEN=$OPS_VERIFY_TOKEN python backend/scripts/production_diagnose.py
```

**Expected final state:** `STATE: SYNCED` (and no blocking errors).

---

## Success criteria

- Backend returns real git SHA (never `"unknown"`).
- Frontend returns real git SHA at `/api/version` (HTTP 200).
- Deploy Guardian reports OK (Vercel frontend SHA + backend `/ops/verify` SHA in sync).
- Push to `main` deterministically updates production (Vercel + GitHub Actions → Oracle); no manual SSH required for routine deploy validation.
