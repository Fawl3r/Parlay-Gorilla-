# Production Deployment: GitHub Variables and Secrets

Required configuration for the **Deploy Backend (Oracle Blue/Green)** workflow and for local/CI verification.

> **Deployment readiness:** If the **Verify deployed version** step skips (or the job fails at verify), ensure all required secrets and the repository variable below are set. Missing **ORACLE_SSH_KEY** or **ORACLE_HOST** skips the entire deploy; missing **BACKEND_URL** or **OPS_VERIFY_TOKEN** skips verify only. Without these, production version visibility cannot be guaranteed and `verify_production_sync.py` will fail for production URLs.

---

## Required GitHub Secrets

Configure under: **Repository → Settings → Secrets and variables → Actions → Secrets.**

| Secret | Description | Used by |
|--------|-------------|--------|
| **ORACLE_SSH_KEY** | Private key for SSH to the Oracle VM (PEM format). Deploy user must have sudo for `systemctl restart` and write to `/opt/parlaygorilla`. | Copy deploy script, Run blue/green deploy |
| **ORACLE_HOST** | Hostname or IP of the Oracle VM (e.g. `parlay-api.example.com`). | All deploy steps |
| **OPS_VERIFY_TOKEN** | Token sent as `x-ops-token` header to `/ops/version` and `/ops/verify`. Must match `OPS_VERIFY_TOKEN` in `/etc/parlaygorilla/backend.env` on the VM. | Verify deployed version (and local `verify_production_sync.py`) |

**Navigation:** GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **Secrets** → **New repository secret**.

---

## Required Repository Variable

Configure under: **Repository → Settings → Secrets and variables → Actions → Variables.**

| Variable | Value | Description |
|----------|-------|-------------|
| **BACKEND_URL** | `https://api.parlaygorilla.com` | Base URL of the production backend. Used by the **Verify deployed version** step to call `GET ${BACKEND_URL}/ops/verify`. |

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
4. **Secrets tab:** Click **New repository secret** for each of `ORACLE_SSH_KEY`, `ORACLE_HOST`, `OPS_VERIFY_TOKEN`. Paste the value; do not share or log.
5. **Variables tab:** Click **New repository variable**. Name: `BACKEND_URL`, Value: `https://api.parlaygorilla.com`. Optionally add `ORACLE_USER` (e.g. `ubuntu`).
6. Ensure the **Deploy Backend (Oracle Blue/Green)** workflow has access (default: all environments).

After this, pushes to `main` will run the workflow and the **Verify deployed version** step will receive `BACKEND_URL` and `OPS_VERIFY_TOKEN`, so it will not skip and will fail the job if `/ops/verify` does not return a `git_sha`.
