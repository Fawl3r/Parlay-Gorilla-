# Oracle Cloud Migration (Render → OCI)

This document summarizes the migration of the Parlay Gorilla backend from Render to Oracle Cloud Infrastructure (OCI), using Docker Compose and GitHub Actions for push-to-deploy.

## Architecture on OCI

- **API**: FastAPI in a Docker container (same image as verifier), behind nginx.
- **Verifier**: Always-on Pattern A worker (Python), same image as API, runs `python -m app.workers.sui_verifier`; polls DB for `queued` records, claims atomically, creates SUI proof, updates status. **The Oracle VM is the only verification worker in production;** the Render verification worker must be disabled.
- **Nginx**: Reverse proxy in front of the API; listens on 80 (and optionally 443 with TLS).
- **Database**: External (Render Postgres, Neon, or Supabase); no change to DB hosting.
- **Redis**: Optional; if the API needs it for scheduler/cache, set `REDIS_URL` for the api service. Verification uses DB-only when `VERIFICATION_DELIVERY=db`; set this on OCI so records are not enqueued to Redis and are consumed only by the Oracle verifier.

## One-time server setup

1. Create an Ubuntu ARM (Ampere A1) or x86 VM on Oracle Cloud.
2. Run the bootstrap script (as root or with sudo):
   ```bash
   curl -sSL https://raw.githubusercontent.com/YOUR_ORG/parlay-gorilla/main/scripts/server_bootstrap.sh | sudo bash
   ```
   Or copy `scripts/server_bootstrap.sh` onto the server and run it. This installs Docker (and Docker Compose v2), configures UFW (22, 80, 443), adds 4G swap, and creates `/opt/parlaygorilla`.
3. Clone the repo into `/opt/parlaygorilla` (or copy files):
   ```bash
   git clone https://github.com/YOUR_ORG/parlay-gorilla.git /opt/parlaygorilla
   ```
4. Create `/opt/parlaygorilla/.env` with at least:
   - `DATABASE_URL` (PostgreSQL; same as Render/Neon/Supabase)
   - `SUI_RPC_URL`, `SUI_PRIVATE_KEY`, `SUI_PACKAGE_ID` (for the verifier)
   - `VERIFICATION_DELIVERY=db` (so the API does not push to Redis for verification; the Python verifier polls DB)
   - Other API env vars as in Render (e.g. `THE_ODDS_API_KEY`, `JWT_SECRET`, `FRONTEND_URL`, `BACKEND_URL`, etc.)
   - Optional: `REDIS_URL` if the API uses Redis for scheduler/cache. In production the API currently expects `REDIS_URL` to be set (e.g. for scheduler); use a Redis instance or a stub URL if you disable those features.

## Push-to-deploy (GitHub Actions)

1. In the GitHub repo, add secrets:
   - `ORACLE_SSH_HOST`: IP or hostname of the Oracle VM
   - `ORACLE_SSH_KEY`: Private key content (e.g. the key you use to `ssh ubuntu@<host>`)
   - Optional: `ORACLE_SSH_USER` (default `ubuntu`)

2. On every push to `main`, the workflow `.github/workflows/deploy-oracle.yml` SSHs into the VM and runs:
   ```bash
   cd /opt/parlaygorilla
   git pull
   bash scripts/deploy.sh
   ```
   `scripts/deploy.sh` builds the backend image, runs `docker compose -f docker-compose.prod.yml up -d`, and restarts all services (api, verifier, nginx).

## Manual deploy

On the Oracle VM:

```bash
cd /opt/parlaygorilla
git pull
bash scripts/deploy.sh
```

## Disabling the Render verification worker during cutover

The Oracle VM is the single source of truth for verification. To avoid double verification and enqueue errors:

1. In the Render dashboard, open the **parlay-gorilla-verification-worker** service.
2. Pause or delete the worker, or stop its deploy so it is no longer running.
3. Ensure `VERIFICATION_DELIVERY=db` is set on the OCI API (and in the deploy workflow `.env.prod`) so new records are written only to the DB and consumed solely by the Oracle verifier.

## Frontend

The frontend remains on Cloudflare Pages. After cutover, point `NEXT_PUBLIC_API_URL` (or equivalent) to the Oracle public URL (e.g. `http://<oracle-ip>` or your domain in front of the VM).

## TLS (optional)

For HTTPS, configure nginx with certificates (e.g. Let’s Encrypt with certbot) and expose 443 in `docker-compose.prod.yml` and UFW. Document the exact steps in this file or in a separate TLS doc.
