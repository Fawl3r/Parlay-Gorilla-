# Production Deployment Validation (30 seconds)

Quick checks to confirm a deployment is live and matches the expected commit.

---

## 1. GitHub Actions deploy job

- Go to **Actions** → **Deploy Backend (Oracle Blue/Green)** → latest run for `main`.
- Confirm the run **succeeded** (green).
- Open the **Verify deployed version** step and confirm it **printed** a line like:
  - `Deployed backend git_sha: 1ac9fa0`
- If this step is missing or skipped, set **BACKEND_URL** (repo variable) and **OPS_VERIFY_TOKEN** (secret) per [PROD_VARS_AND_SECRETS.md](./PROD_VARS_AND_SECRETS.md).

---

## 2. Backend version via curl

From any machine that can reach production:

```bash
curl -fsS -H "x-ops-token: YOUR_OPS_VERIFY_TOKEN" "https://api.parlaygorilla.com/ops/verify"
```

**Expected response:**

```json
{"ok":true,"git_sha":"1ac9fa0"}
```

Replace `1ac9fa0` with the commit you just deployed. If you get `403`, the token is wrong or missing. If you get `git_sha: "unknown"`, the backend is not loading `GIT_SHA` from the slot’s `.env.deploy` (check systemd unit and `deploy_bluegreen.sh`).

---

## 3. Local script: verify_production_sync.py

From the repo root, with `OPS_VERIFY_TOKEN` set (and optional `BACKEND_URL`):

```bash
# Windows (PowerShell)
$env:OPS_VERIFY_TOKEN = "your-token"
$env:BACKEND_URL = "https://api.parlaygorilla.com"
python backend/scripts/verify_production_sync.py

# Linux/macOS
export OPS_VERIFY_TOKEN=your-token
export BACKEND_URL=https://api.parlaygorilla.com
python backend/scripts/verify_production_sync.py
```

**Expected output:**

```
PASS: Production backend matches local commit: 1ac9fa0
```

Exit code 0. Any other output (FAIL, SHA mismatch, 403, etc.) means production does not match local or token/URL is wrong.

---

## 4. Frontend build SHA in browser console

1. Open production site (e.g. https://parlaygorilla.com).
2. Open DevTools → **Console**.
3. Look for a log line: **Build: 1ac9fa0** (or the deployed short SHA).

If you see **Build: unknown**, the frontend build did not receive `NEXT_PUBLIC_GIT_SHA` (e.g. from `VERCEL_GIT_COMMIT_SHA` on Vercel). Check `frontend/package.json` build script and `frontend/next.config.js` `env.NEXT_PUBLIC_GIT_SHA`.

---

## Summary

| Check | Where | Pass condition |
|-------|--------|----------------|
| Deploy job | GitHub Actions | Success; Verify step prints `Deployed backend git_sha: <sha>` |
| Backend API | `curl` to `/ops/verify` | `{"ok":true,"git_sha":"<sha>"}` |
| Local verify | `verify_production_sync.py` | `PASS: Production backend matches local commit: <sha>` |
| Frontend | Browser console | `Build: <sha>` |

All four should show the **same** short commit SHA as the commit you pushed to `main`.

---

## 5. Read-only diagnostics script (optional)

From the repo root, with `OPS_VERIFY_TOKEN` set for production:

```bash
python backend/scripts/production_diagnose.py
```

Output includes `LOCAL_SHA`, `FRONTEND_EXPECTED_SHA`, `BACKEND_SHA`, and **STATE** — one of:

- **SYNCED** — Backend matches repo HEAD; frontend expected SHA matches.
- **BACKEND_OUT_OF_DATE** — Production backend is serving a different commit (or `unknown`); run deploy or check systemd/.env.deploy.
- **CACHE_OR_FRONTEND_STALE** — Backend matches HEAD but frontend build may show a different SHA; purge CDN or redeploy frontend.

The script is read-only (no SSH, no data changes). Exit code 0 = diagnosis completed (SYNCED or CACHE_OR_FRONTEND_STALE); 1 = BACKEND_OUT_OF_DATE; 2 = cannot determine (e.g. backend unreachable or 403).
