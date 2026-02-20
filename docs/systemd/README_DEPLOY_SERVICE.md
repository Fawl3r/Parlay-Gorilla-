# Parlay Gorilla Backend — systemd service (blue/green deploy)

This service runs the FastAPI backend from `/opt/parlaygorilla/current` (a symlink to the active blue or green slot). Used with the zero-downtime blue/green deploy.

## Prerequisites

- Blue/green layout: `/opt/parlaygorilla/releases/{blue,green}`, `/opt/parlaygorilla/current` → one of them.
- Python 3.x, venv, and app dependencies installed in each slot (see `docs/deploy/oracle_bluegreen_setup.md`).

## 1. Create the `parlaygorilla` user

```bash
sudo useradd -r -s /bin/false -d /opt/parlaygorilla parlaygorilla
# If dirs already exist, fix ownership:
sudo chown -R parlaygorilla:parlaygorilla /opt/parlaygorilla
```

## 2. Place the environment file (secrets)

Create `/etc/parlaygorilla/backend.env` with all runtime secrets. **Do not commit this file.**

```bash
sudo mkdir -p /etc/parlaygorilla
sudo touch /etc/parlaygorilla/backend.env
sudo chmod 600 /etc/parlaygorilla/backend.env
sudo nano /etc/parlaygorilla/backend.env
```

Example contents (adjust to your env):

```bash
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
JWT_SECRET=...
THE_ODDS_API_KEY=...
# Optional: MIGRATIONS_ALLOWED=true   # Set to true to run alembic upgrade head during deploy
# Optional: ENVIRONMENT=production
```

## 3. Install the systemd unit

```bash
sudo cp docs/systemd/parlaygorilla-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable parlaygorilla-backend
```

## 4. Start the service

```bash
sudo systemctl start parlaygorilla-backend
sudo systemctl status parlaygorilla-backend
```

## Nginx / reverse proxy

If you use Nginx in front of the backend, point the upstream to `127.0.0.1:8000`. No Nginx config change is required for blue/green: the systemd service runs the app on 8000; after cutover, `systemctl restart parlaygorilla-backend` makes the new slot serve on 8000. Reload Nginx only when you change Nginx config (e.g. `nginx -s reload`).

Example upstream (for reference only):

```nginx
upstream parlaygorilla_backend {
    server 127.0.0.1:8000;
}
```

If you do not use Nginx, health checks and traffic can still hit `http://127.0.0.1:8000` directly (e.g. from another proxy or Cloudflare Tunnel).

## Reload and restart after unit changes

After editing the service file:

```bash
sudo cp docs/systemd/parlaygorilla-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart parlaygorilla-backend
```

## Useful commands

- **Status:** `sudo systemctl status parlaygorilla-backend`
- **Logs:** `sudo journalctl -u parlaygorilla-backend -f`
- **Restart:** `sudo systemctl restart parlaygorilla-backend`
- **Health:** `curl -sS http://127.0.0.1:8000/ops/version` (add `-H "x-ops-token: $OPS_VERIFY_TOKEN"` if token is set)

## If /ops/verify returns git_sha "unknown"

The backend reads `GIT_SHA` from environment; the deploy script writes it to `/opt/parlaygorilla/current/.env.deploy`. If the service does not load that file first, you get `"git_sha":"unknown"`.

1. Ensure the unit loads `.env.deploy` **before** `backend.env`:  
   `EnvironmentFile=-/opt/parlaygorilla/current/.env.deploy` then `EnvironmentFile=/etc/parlaygorilla/backend.env`.
2. Re-install the unit from the repo:  
   `sudo cp /opt/parlaygorilla/current/docs/systemd/parlaygorilla-backend.service /etc/systemd/system/`  
   then `sudo systemctl daemon-reload` and `sudo systemctl restart parlaygorilla-backend`.
3. Full steps: see [PRODUCTION_SYNC_RUNBOOK.md](../deploy/PRODUCTION_SYNC_RUNBOOK.md) (Part 1 — Backend SHA fix).
