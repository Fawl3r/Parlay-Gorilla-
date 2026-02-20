# Oracle VM — Blue/Green Zero-Downtime Setup

One-time bootstrap to prepare the Oracle VM for blue/green deploys. After this, every push to `main` can deploy via GitHub Actions with near-zero downtime.

## 1. Directory layout

```bash
sudo mkdir -p /opt/parlaygorilla/releases/blue /opt/parlaygorilla/releases/green
sudo ln -sfn /opt/parlaygorilla/releases/blue /opt/parlaygorilla/current
```

Initial active slot is `blue`; the deploy script alternates between blue and green.

## 2. User and permissions

The systemd service runs as `parlaygorilla`. The deploy script (run via SSH, e.g. as `ubuntu`) must be able to write into `/opt/parlaygorilla/releases` and run `sudo systemctl restart parlaygorilla-backend`.

```bash
sudo useradd -r -s /bin/false -d /opt/parlaygorilla parlaygorilla
sudo chown -R parlaygorilla:parlaygorilla /opt/parlaygorilla
sudo chmod -R g+w /opt/parlaygorilla
sudo usermod -aG parlaygorilla ubuntu
```

Log out and back in (or `newgrp parlaygorilla`) so the deploy user is in group `parlaygorilla` and can write to the release dirs.

Deploy log and lock:

```bash
sudo mkdir -p /var/log/parlaygorilla
sudo chown ubuntu:ubuntu /var/log/parlaygorilla
```

Lock file is under `/opt/parlaygorilla/.deploy.lock` (writable by parlaygorilla group).

## 3. Install Python, venv, and build tools

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git curl build-essential
```

## 4. Environment file (secrets)

Create `/etc/parlaygorilla/backend.env` with all runtime secrets. **Do not commit this file.**

```bash
sudo mkdir -p /etc/parlaygorilla
sudo touch /etc/parlaygorilla/backend.env
sudo chmod 600 /etc/parlaygorilla/backend.env
sudo nano /etc/parlaygorilla/backend.env
```

Example (adjust to your env):

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname
REDIS_URL=redis://...
JWT_SECRET=...
THE_ODDS_API_KEY=...
ENVIRONMENT=production
# Ops verification (required for /ops/version and /ops/verify behind Cloudflare/WAF)
# Use a long random string; add same value to GitHub Secrets as OPS_VERIFY_TOKEN.
OPS_VERIFY_TOKEN=<long random string>
# Optional: set to true to run alembic upgrade head during deploy
# MIGRATIONS_ALLOWED=false
```

## 5. Install and enable systemd service

```bash
# From repo root on the VM (or copy the service file into place)
sudo cp /opt/parlaygorilla/current/docs/systemd/parlaygorilla-backend.service /etc/systemd/system/
# If current is empty on first run, copy from a checked-out repo:
# sudo cp docs/systemd/parlaygorilla-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable parlaygorilla-backend
```

Before the first deploy, you must have at least one slot populated (e.g. run the deploy script once, or clone the repo into one slot and create the venv so `current` points to a valid app). See step 7.

## 6. Firewall

Allow only what you need. If Cloudflare or a proxy connects to the VM:

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

The backend listens on `127.0.0.1:8000`; only Nginx or your reverse proxy needs to reach it (localhost).

## 7. First deploy and verification

- **Option A — GitHub Actions:** Push to `main` with secrets `ORACLE_SSH_KEY`, `ORACLE_HOST` set (and `ORACLE_USER` in vars if not `ubuntu`). The workflow copies `deploy_bluegreen.sh` and runs it on the VM; the script clones the repo into the target slot.
- **Option B — Manual first run:** SSH to the VM, copy or checkout the repo, then run the deploy script by hand:

  ```bash
  git clone --depth 1 --branch main https://github.com/YOUR_ORG/YOUR_REPO.git /tmp/pg-repo
  # Copy script from repo
  bash /tmp/pg-repo/backend/scripts/deploy_bluegreen.sh https://github.com/YOUR_ORG/YOUR_REPO.git main
  ```

For **private repos**, the VM needs access to clone: use a deploy key (SSH key added to the repo) and pass the SSH clone URL to the script, or configure Git credentials on the VM.

Verify:

```bash
curl -sS http://127.0.0.1:8000/ops/version
```

You should see JSON with `git_sha`, `build_time`, `environment`, `service`.

## 8. Nginx (optional)

If you use Nginx as a reverse proxy, point the backend upstream to `127.0.0.1:8000`. No Nginx change is required for blue/green cutover; the systemd service handles the switch. See `docs/systemd/README_DEPLOY_SERVICE.md`.

## GitHub secrets and vars

- **Secrets:** `ORACLE_SSH_KEY` (private key for SSH), `ORACLE_HOST` or `ORACLE_SSH_HOST` (VM hostname or IP), `OPS_VERIFY_TOKEN` (same value as in `/etc/parlaygorilla/backend.env`; used for post-deploy verify step).
- **Vars (required for verify):** `BACKEND_URL` (e.g. `https://api.parlaygorilla.com`). **Optional:** `ORACLE_USER` (default `ubuntu`).

Do not put `DATABASE_URL`, `REDIS_URL`, or other app secrets in GitHub; they live only in `/etc/parlaygorilla/backend.env` on the VM.
