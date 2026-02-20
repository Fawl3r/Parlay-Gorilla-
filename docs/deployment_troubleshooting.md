# Deployment troubleshooting

When new Git commits are not reaching production, use this guide to find and fix the cause.

---

## 1. Wrong production branch

**Symptom:** Pushes to `main` do not update the live site; or only preview URLs show new code.

**Cause:** Vercel production branch is not `main` (e.g. set to `master` or another branch).

**Diagnosis:**

- Vercel Dashboard → Project → Settings → Git → **Production Branch**. Must be `main`.
- Check latest deployment: Deployments → open latest → confirm branch is `main` and “Production” (not Preview).

**Fix:** Change Production Branch to `main` in Vercel. Redeploy from Deployments → Redeploy.

---

## 2. Vercel preview-only deployments

**Symptom:** New commits appear on preview URLs (e.g. `*-username.vercel.app`) but not on production domain.

**Cause:** Deploys are running for non‑production branches only, or production deploy failed.

**Diagnosis:**

- Vercel Dashboard → Deployments. Filter by “Production”. Check that the latest commit on `main` has a production deployment and status “Ready”.
- Confirm Root Directory is `frontend` (Settings → General). Wrong root can cause failed or wrong builds.

**Fix:** Set Production Branch to `main` and Root Directory to `frontend`. Trigger a production deploy from the latest `main` (Redeploy).

---

## 3. Cloudflare cached HTML

**Symptom:** Frontend or API responses look stale after a successful deploy.

**Cause:** Cloudflare (or browser) is serving cached HTML/API responses.

**Diagnosis:**

- Backend: `curl -s https://api.parlaygorilla.com/ops/version` — check `git_sha`. Compare to local: `git rev-parse --short HEAD`.
- Frontend: Hard refresh (Ctrl+Shift+R) or open in incognito. Check browser console for `Build: <sha>` or `window.__PG_BUILD_SHA`.

**Fix:**

- **Cloudflare purge:** Dashboard → Caching → Configuration → **Purge Everything** (or “Custom Purge” for specific URLs, e.g. `https://parlaygorilla.com/`).
- **Backend:** If `/ops/version` is cached, purge that URL or use a cache-busting query: `curl -s 'https://api.parlaygorilla.com/ops/version?t=1'`.
- Do not change DNS or proxy settings for this; only purge cache.

---

## 4. Backend process not restarted

**Symptom:** Backend `/ops/version` shows an old `git_sha` after you deployed code on the Oracle VM.

**Cause:** New code was pulled but the FastAPI process was not restarted.

**Diagnosis:**

- On the VM: `curl -s http://127.0.0.1:8000/ops/version`
- Compare `git_sha` to `git rev-parse --short HEAD` in the repo on the VM.

**Fix:**

- Restart the service: `sudo systemctl restart parlaygorilla-backend`
- Or run the full deploy script: `./backend/scripts/deploy_backend.sh` from repo root on the VM (script pulls, installs, sets GIT_SHA, restarts, verifies).

---

## 5. Stale VM checkout

**Symptom:** Backend version is old; you have run deploy or restarts but code on the VM is not from latest `main`.

**Cause:** Git on the Oracle VM is not on `main` or not updated (e.g. wrong branch, no `git pull`/`git reset`).

**Diagnosis (on VM):**

```bash
cd /opt/parlaygorilla/current   # or your repo path
git fetch origin
git status
git rev-parse --short HEAD
git rev-parse --short origin/main
```

If `HEAD` is not `origin/main`, or fetch shows new commits on `origin/main` that you don’t have, the checkout is stale.

**Fix:**

```bash
git fetch origin
git reset --hard origin/main
# Then re-run deploy script or at least: sudo systemctl restart parlaygorilla-backend
```

---

## 6. Webhook / Git disconnect

**Symptom:** Pushing to `main` does not trigger a Vercel deploy, or backend VM is never updated.

**Cause:** Vercel Git integration disconnected; or no automation (webhook/CI) to update the VM.

**Diagnosis:**

- **Vercel:** Dashboard → Project → Settings → Git. Confirm repo is connected and “Production Branch” is `main`. Check Deployments for new entries after a push.
- **Backend:** Backend on Oracle has no automatic deploy; someone must run the deploy script or equivalent on the VM after push. Check your runbooks or GitHub Actions (if any) for “deploy backend” steps.

**Fix:**

- Reconnect Vercel to the Git provider if needed; ensure production branch is `main`.
- For backend: run `backend/scripts/deploy_backend.sh` on the VM after pushing to `main`, or set up a secure webhook/CI job that runs it (see existing docs for Oracle/bootstrap).

---

## Quick reference

| Check | Command / place |
|-------|------------------|
| Local commit | `git rev-parse --short HEAD` |
| Production backend version | `curl -s https://api.parlaygorilla.com/ops/version` |
| Backend on VM | `curl -s http://127.0.0.1:8000/ops/version` |
| Sync script | `BACKEND_URL=https://api.parlaygorilla.com python backend/scripts/verify_production_sync.py` |
| Vercel production branch | Dashboard → Settings → Git → Production Branch |
| Cloudflare purge | Dashboard → Caching → Purge Everything / Custom Purge |

See [README_DEPLOY_CHECKLIST.md](../README_DEPLOY_CHECKLIST.md) for normal deploy and verification steps.
