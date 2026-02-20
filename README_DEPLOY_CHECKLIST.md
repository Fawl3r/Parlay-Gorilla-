# Deployment checklist – Parlay Gorilla

Use this to verify that new commits reach **production** for both frontend (Vercel) and backend (Oracle VM).

---

## 1. Vercel configuration (frontend)

Verify in [Vercel Dashboard](https://vercel.com) → Project → Settings:

| Setting | Required value | Why |
|--------|----------------|-----|
| **Production Branch** | `main` | Only pushes to `main` should deploy to production. |
| **Root Directory** | `frontend` | Monorepo: frontend app lives in `frontend/`. |
| **Auto-deploy** | Enabled | Commits to `main` deploy without manual trigger. |

If any value is wrong, fix it in the dashboard (do not change code):

- **Production Branch**: Settings → Git → Production Branch → set to `main`.
- **Root Directory**: Settings → General → Root Directory → set to `frontend`.
- **Auto-deploy**: Settings → Git → Deploy Hooks / ensure production branch deploys on push.

**Preview vs production**

- **Production**: deploys from `main`; URL is your production domain (e.g. `parlaygorilla.com`).
- **Preview**: every other branch/PR gets a preview URL; it is **not** production. If you only see new commits on preview URLs, production branch or root directory is likely wrong.

---

## 2. Redeploy instructions

**Frontend (Vercel)**

- Push to `main` → production deploy runs automatically.
- Manual redeploy: Vercel Dashboard → Deployments → ⋮ on latest → **Redeploy** (use “Redeploy with existing Build Cache” only if you did not change deps).

**Backend (Oracle VM)**

- From repo root (or from backend): run `./backend/scripts/deploy_backend.sh` on the VM (see script for prereqs).
- Or follow [docs/systemd/README_DEPLOY_SERVICE.md](docs/systemd/README_DEPLOY_SERVICE.md) and your existing runbooks.

---

## 3. Quick verification

- **Backend version**: `curl https://api.parlaygorilla.com/ops/version` (or your backend host). Check `git_sha` matches latest `main`.
- **Frontend version**: Browser console on production site should show `Build: <sha>` (or check `window.__PG_BUILD_SHA` in devtools if console is stripped).
- **Sync check**: run `python backend/scripts/verify_production_sync.py` (see script for env vars).

**Cloudflare cache**  
If the live site shows old content after a deploy, purge cache: Cloudflare Dashboard → Caching → Configuration → **Purge Everything** (or purge by URL/prefix). See [docs/deployment_troubleshooting.md](docs/deployment_troubleshooting.md) for details.

See [docs/deployment_troubleshooting.md](docs/deployment_troubleshooting.md) for failure modes and exact diagnostic commands.
