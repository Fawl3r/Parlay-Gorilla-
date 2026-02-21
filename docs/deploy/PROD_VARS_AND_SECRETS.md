# Production Deployment: GitHub Variables and Secrets

Required configuration for the **Deploy Backend (Oracle Blue/Green)** workflow and for local/CI verification.

> **Deployment readiness:** The workflow needs **ORACLE_SSH_KEY** and either **ORACLE_HOST** or **ORACLE_SSH_HOST** to run the deploy. It requires **BACKEND_URL** (variable) and **OPS_VERIFY_TOKEN** (secret) for the **Verify deployed version** step. If **OPS_VERIFY_TOKEN** is missing, the verify step cannot assert production and deploy drift may go undetected; the job will fail until both are set.

---

## Required GitHub Secrets

Configure under: **Repository → Settings → Secrets and variables → Actions → Secrets.**

| Secret | Description | Used by |
|--------|-------------|--------|
| **ORACLE_SSH_KEY** | Private key for SSH to the Oracle VM (PEM format). Deploy user must have sudo for `systemctl restart` and write to `/opt/parlaygorilla`. | Copy deploy script, Run blue/green deploy |
| **ORACLE_HOST** or **ORACLE_SSH_HOST** | Hostname or IP of the Oracle VM (e.g. `parlay-api.example.com`). The workflow uses **ORACLE_HOST** if set, otherwise **ORACLE_SSH_HOST**. | All deploy steps |
| **OPS_VERIFY_TOKEN** | Token sent as `x-ops-token` header to `/ops/version` and `/ops/verify`. Must match `OPS_VERIFY_TOKEN` in `/etc/parlaygorilla/backend.env` on the VM. Required for verify step. | Verify deployed version (and local `verify_production_sync.py`) |

**Navigation:** GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **Secrets** → **New repository secret**.

**Creating OPS_VERIFY_TOKEN:** Generate a strong value (e.g. `openssl rand -hex 32`). Add it as repository secret **OPS_VERIFY_TOKEN** and set the same value in `/etc/parlaygorilla/backend.env` on the Oracle VM as `OPS_VERIFY_TOKEN=<value>`. Do not log or commit the value.

---

## Required Repository Variable

Configure under: **Repository → Settings → Secrets and variables → Actions → Variables.**

| Variable | Value | Description |
|----------|-------|-------------|
| **BACKEND_URL** | `https://api.parlaygorilla.com` | Base URL of the production backend. Used by the **Verify deployed version** step and by **Deploy Guardian** for `GET ${BACKEND_URL}/ops/verify`. Required for verify step. |
| **FRONTEND_URL** | `https://parlaygorilla.com` | Base URL of the production frontend. Used by **Deploy Guardian** for `GET ${FRONTEND_URL}/api/version`. See [AUTONOMOUS_DEPLOY_GUARDIAN.md](./AUTONOMOUS_DEPLOY_GUARDIAN.md). |

**Navigation:** GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **Variables** → **New repository variable**.

---

## Optional Repository Variable

| Variable | Default | Description |
|----------|--------|-------------|
| **ORACLE_USER** | `ubuntu` | SSH user for the Oracle VM. Set if the deploy user is not `ubuntu`. |

---

## Exact GitHub UI Steps

1. Open the repository on GitHub.
2. Click **Settings** (repo top bar).
3. In the left sidebar, under **Security**, click **Secrets and variables** → **Actions**.
4. **Secrets tab:** Click **New repository secret** for each of `ORACLE_SSH_KEY`, `ORACLE_HOST` or `ORACLE_SSH_HOST`, and **OPS_VERIFY_TOKEN**. Paste the value; do not share or log.
5. **Variables tab:** Click **New repository variable**. Name: **BACKEND_URL**, Value: `https://api.parlaygorilla.com`. Optionally add `ORACLE_USER` (e.g. `ubuntu`).
6. Ensure the **Deploy Backend (Oracle Blue/Green)** workflow has access (default: all environments).

After this, pushes to `main` will run the workflow and the **Verify deployed version** step will run (and fail the job if `/ops/verify` does not return a `git_sha` or if **BACKEND_URL** / **OPS_VERIFY_TOKEN** are missing).

---

## Oracle VM: OPS_VERIFY_TOKEN and env order

On the Oracle VM, verification only works when the backend has the same token as GitHub:

1. **Set the token on the VM:** In `/etc/parlaygorilla/backend.env` add (or update) `OPS_VERIFY_TOKEN=<same value as GitHub secret OPS_VERIFY_TOKEN>`. Use a strong random value (e.g. `openssl rand -hex 32`); do not log or commit it.
2. **Env load order:** The systemd unit `parlaygorilla-backend.service` loads `/opt/parlaygorilla/current/.env.deploy` first (slot-specific `GIT_SHA`, `BUILD_TIME`), then `/etc/parlaygorilla/backend.env`. So slot deploy metadata is set before secrets; keep this order.
3. **Restart after setting token:** Run `sudo systemctl restart parlaygorilla-backend` after adding or changing `OPS_VERIFY_TOKEN` in `backend.env`.

Then from a trusted environment: `curl -fsS -H "x-ops-token: $OPS_VERIFY_TOKEN" https://api.parlaygorilla.com/ops/verify` should return `{"ok":true,"git_sha":"<sha>"}`. If you get 403, the token on the VM does not match the one in GitHub Secrets or the service was not restarted.

---

## Production sync verification checklist

| Item | Where | How to verify |
|------|--------|----------------|
| **OPS_VERIFY_TOKEN** (secret) | GitHub → Settings → Secrets and variables → Actions → Secrets | From a trusted env with token in `$OPS_VERIFY_TOKEN`: `curl -fsS -H "x-ops-token: $OPS_VERIFY_TOKEN" https://api.parlaygorilla.com/ops/verify` → must return `ok: true` and `git_sha`. |
| **BACKEND_URL** (variable) | GitHub → Settings → Secrets and variables → Actions → Variables | Value `https://api.parlaygorilla.com`. CI verify step uses it; if missing, job fails with instructions. |
| **Oracle VM** `OPS_VERIFY_TOKEN` | `/etc/parlaygorilla/backend.env` | Same value as GitHub secret; then `sudo systemctl restart parlaygorilla-backend`. |
| **CI verify step** | Deploy Backend (Oracle Blue/Green) workflow | Push to `main`; **Verify deployed version** must run and print `Deployed backend git_sha: <sha>`; job fails if `git_sha` cannot be retrieved. |
| **Local sync scripts** | Repo root | `BACKEND_URL=https://api.parlaygorilla.com OPS_VERIFY_TOKEN=*** python backend/scripts/verify_production_sync.py` → must print `PASS` and exit 0 when production matches local HEAD. |
| **Diagnose script** | Repo root | `BACKEND_URL=https://api.parlaygorilla.com OPS_VERIFY_TOKEN=*** python backend/scripts/production_diagnose.py` → must report `STATE: SYNCED` when backend SHA matches local. |

---

## Production: Payment (credits and subscription)

If production shows **"Payment system is not setup for credits or subscription"**, the backend is returning **503** with `"Payment system not configured"` because Stripe is not configured on the VM.

### Required on the Oracle VM

In **`/etc/parlaygorilla/backend.env`** on the Oracle VM, set at least:

| Variable | Description |
|----------|-------------|
| **STRIPE_SECRET_KEY** | Stripe secret key (live: `sk_live_...`). Without this, all credit-pack and subscription checkouts return 503. |

After adding or changing these, restart the backend:

```bash
sudo systemctl restart parlaygorilla-backend
```

### Optional (for full flows)

- **STRIPE_WEBHOOK_SECRET** – Required for Stripe webhooks (subscription/credit activation). Webhook URL: `{BACKEND_URL}/api/webhooks/stripe`.
- **STRIPE_PRICE_ID_PRO_MONTHLY**, **STRIPE_PRICE_ID_PRO_ANNUAL**, **STRIPE_PRICE_ID_PRO_LIFETIME** – Fallback price IDs if not set in `subscription_plans`.
- **STRIPE_PRICE_ID_CREDITS_10**, **STRIPE_PRICE_ID_CREDITS_25**, **STRIPE_PRICE_ID_CREDITS_50**, **STRIPE_PRICE_ID_CREDITS_100** – Fallback for credit packs if not in DB.
- **APP_URL** – Frontend URL for checkout redirects (e.g. `https://parlaygorilla.com`).

Full list and Stripe Dashboard setup: see **[STRIPE_PRE_TEST_CHECKLIST.md](../../STRIPE_PRE_TEST_CHECKLIST.md)** and **backend/.env.example**.

### Upload whole local .env to Oracle (for testing with Stripe test API)

To give the production backend the same env as local (e.g. Stripe test keys), upload your **backend/.env** and then apply it on the VM.

**1. Upload from your machine (PowerShell, from repo root):**

```powershell
.\backend\scripts\upload_env_to_oracle.ps1 -OracleHost "your-oracle-vm-hostname-or-ip"
# If you use an SSH key:
.\backend\scripts\upload_env_to_oracle.ps1 -OracleHost "your-oracle-vm-hostname-or-ip" -KeyPath "$env:USERPROFILE\.ssh\oracle_deploy"
```

Or with Bash (Git Bash / WSL):

```bash
ORACLE_HOST=your-oracle-vm-hostname-or-ip ./backend/scripts/upload_env_to_oracle.sh
```

**2. On the Oracle VM (not on your local machine):** SSH into the VM first, then run:

```bash
sudo cp /etc/parlaygorilla/backend.env /etc/parlaygorilla/backend.env.bak
sudo cp /tmp/backend.env.uploaded /etc/parlaygorilla/backend.env
# Use the service name your VM has (often parlaygorilla-backend or parlaygorilla-api):
sudo systemctl restart parlaygorilla-backend
# If "Unit not found": install the systemd unit (see docs/deploy/VM_OPS_VERIFY_RUNBOOK.md, section 0)
```

**Warning:** Your local .env must use the same **DATABASE_URL** and **REDIS_URL** as production (or production will point at the wrong DB/Redis). If your local .env points to local or staging DB/Redis, do not replace the whole file; merge only the vars you need (e.g. all `STRIPE_*` and `APP_URL`) into `/etc/parlaygorilla/backend.env` and restart.
