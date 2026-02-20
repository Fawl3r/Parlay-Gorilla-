# Setup: Oracle Cloud VM + Cloudflare (Backend on OCI, Frontend on Pages)

Step-by-step guide to run the Parlay Gorilla backend on an Oracle Cloud VM and point the Cloudflare frontend (Pages + DNS) at it.

---

## Part 1: Oracle Cloud (VM + deploy)

### 1.1 Create an Oracle Cloud account and VM

1. **Sign up**: [cloud.oracle.com](https://cloud.oracle.com) — use the Always Free tier if eligible (e.g. Ampere A1 ARM or x86).
2. **Create a compute instance**:
   - **Menu** → **Compute** → **Instances** → **Create instance**
   - **Name**: e.g. `parlaygorilla-backend`
   - **Image**: **Ubuntu** (22.04 or 24.04)
   - **Shape**: Ampere A1 (ARM, Always Free) or VM.Standard.E2.1.Micro (x86 free)
   - **Networking**: Create or use a VCN; ensure the subnet is **public**. Assign a **public IP**.
   - **Add SSH keys**: Either “Generate a key pair for me” (download the private key) or “Upload public key” (paste your existing `.pub`).
3. **Open ports in the cloud firewall**:
   - **Networking** → **Virtual Cloud Networks** → your VCN → **Security Lists** → **Default Security List**
   - Add **Ingress** rules:
     - **22** (SSH), **80** (HTTP), **443** (HTTPS)
     - Source: `0.0.0.0/0` (or restrict to your IP for 22)
4. **Note**:
   - **Public IP** of the instance (e.g. `129.146.x.x`)
   - **SSH user**: usually `ubuntu` for Ubuntu images

### 1.2 First SSH and bootstrap

1. **SSH in** (use the key you created or uploaded):
   ```bash
   ssh -i /path/to/your-key.key ubuntu@<PUBLIC_IP>
   ```
2. **Run the bootstrap script** (installs Docker, UFW, swap, creates `/opt/parlaygorilla`):
   ```bash
   # From your laptop, copy the script to the server (or clone the repo first and run from repo root)
   # Option A: clone repo then run script
   sudo git clone https://github.com/YOUR_ORG/parlay-gorilla.git /opt/parlaygorilla
   sudo bash /opt/parlaygorilla/scripts/server_bootstrap.sh
   # Fix ownership so your user can push/pull
   sudo chown -R ubuntu:ubuntu /opt/parlaygorilla
   ```
   **Option B** (if repo is private or you prefer copy-paste): Copy the contents of `scripts/server_bootstrap.sh` into a file on the server and run `sudo bash server_bootstrap.sh`, then create `/opt/parlaygorilla` and clone the repo manually.

### 1.3 Create `.env` on the Oracle VM

On the VM (or from your machine and SCP the file):

```bash
cd /opt/parlaygorilla
nano .env   # or vim / scp from laptop
```

Use the same variables as Render/backend, with these **required for OCI**:

| Variable | Example / note |
|----------|----------------|
| `DATABASE_URL` | Your Postgres URL (Render, Neon, or Supabase). Same as current production. |
| `VERIFICATION_DELIVERY` | `db` (so the Python verifier runs; no Redis for verification) |
| `SUI_RPC_URL` | e.g. `https://fullnode.mainnet.sui.io` |
| `SUI_PRIVATE_KEY` | Your SUI wallet private key (suiprivkey... or base64). **Keep secret.** |
| `SUI_PACKAGE_ID` | Your published Move package ID |
| `ENVIRONMENT` | `production` |
| `USE_SQLITE` | `false` |
| `REDIS_URL` | Required by API in production. Use Render Redis URL, or a stub like `redis://localhost:6379` if you don’t use Redis features. |
| `THE_ODDS_API_KEY` | Same as Render |
| `JWT_SECRET` | Same as Render (or generate new) |
| `FRONTEND_URL` | `https://www.parlaygorilla.com` (or your Cloudflare Pages URL) |
| `BACKEND_URL` | `https://api.parlaygorilla.com` (after DNS is set; see Part 2) or `http://<ORACLE_PUBLIC_IP>` for testing |
| `APP_URL` | Same as `FRONTEND_URL` |

Copy the rest from `backend/.env.example` or your Render env (OpenAI, API-Sports, Resend, etc.). A full OCI example is in **`.env.oci.example`** in the repo root. **After pulling Safety Mode v1.1+:** optionally add `SAFETY_MODE_RED_MIN_SECONDS`, `SAFETY_MODE_YELLOW_MIN_SECONDS`, `SAFETY_MODE_EVENT_BUFFER_SIZE` to the Oracle VM `.env` (defaults apply if omitted; see `.env.oci.example`).

### 1.4 GitHub secrets (for push-to-deploy)

1. **Repo** → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret** for each:

| Secret | Value |
|--------|--------|
| `ORACLE_SSH_HOST` | Public IP of the Oracle VM (e.g. `129.146.x.x`) or hostname once DNS is set |
| `ORACLE_SSH_KEY` | **Full contents** of your private key file (the one you use for `ssh -i key.key ubuntu@<host>`) |
| `ORACLE_SSH_USER` | `ubuntu` (default; add only if you use a different user) |

3. Push to `main` (or run the “Deploy to Oracle” workflow manually). The workflow will SSH in and run `git pull` + `scripts/deploy.sh`.

### 1.5 Run migration 048

Migration `048_add_verification_processing_status` adds `processing_started_at` and supports the `processing` status.

- **Option A**: Let the API run it on first start. The Docker CMD runs `alembic upgrade head` then uvicorn. After first deploy, check logs: `docker compose -f docker-compose.prod.yml logs api`.
- **Option B** (manual): SSH to the VM and run:
  ```bash
  cd /opt/parlaygorilla
  docker compose -f docker-compose.prod.yml run --rm api alembic upgrade head
  ```

### 1.6 Disable Render verification worker (cutover)

The **Oracle VM is the only verification worker** in production; the Render verification worker must be disabled. Verification delivery must be DB-only so records are not enqueued to Redis.

1. **Render** → **parlay-gorilla-verification-worker** → **Settings** → **Pause service** (or delete the worker).
2. Ensure on OCI `.env`: `VERIFICATION_DELIVERY=db` (required for Oracle verifier; deploy workflow writes this to `.env.prod` when secrets are set).
3. Redeploy OCI if you changed `.env`: re-run the GitHub workflow or run `bash scripts/deploy.sh` on the VM.

---

## Part 2: Cloudflare (DNS + Pages)

### 2.1 Cloudflare DNS: point API to Oracle

If your domain (e.g. `parlaygorilla.com`) is on Cloudflare:

1. **Cloudflare Dashboard** → **Websites** → **parlaygorilla.com** → **DNS** → **Records**
2. **Add/Edit** a record for the API:
   - **Type**: `A`
   - **Name**: `api` (so `api.parlaygorilla.com` points to Oracle)
   - **IPv4 address**: **Public IP of your Oracle VM**
   - **Proxy status**: **Proxied** (orange cloud) for DDoS/cache, or **DNS only** (grey) if you want traffic to hit the VM directly
   - **TTL**: Auto
3. Save. After DNS propagates (minutes), `api.parlaygorilla.com` will resolve to your Oracle VM.

**HTTPS**: If the record is **Proxied**, Cloudflare will terminate HTTPS for `api.parlaygorilla.com` and send HTTP to your VM (port 80). Your nginx listens on 80, so no cert change on the VM is required. If you use **DNS only**, you’d need TLS on the VM (e.g. Let’s Encrypt) and `BACKEND_URL`/browser will use `https://api.parlaygorilla.com` only after that.

### 2.2 Cloudflare Pages: frontend env (point to Oracle API)

Your frontend is already on Cloudflare Pages. Update its env so it talks to the Oracle backend:

1. **Cloudflare Dashboard** → **Workers & Pages** → your **Parlay Gorilla frontend** project → **Settings** → **Environment variables**
2. Set for **Production** (and Preview if you want):

| Variable | Value |
|---------|--------|
| `NEXT_PUBLIC_API_URL` | `https://api.parlaygorilla.com` (once DNS is set) or `http://<ORACLE_PUBLIC_IP>` for testing |
| `PG_BACKEND_URL` | Same as `NEXT_PUBLIC_API_URL` (used for server-side/SSR and mobile E2E) |
| `NEXT_PUBLIC_SITE_URL` | `https://www.parlaygorilla.com` (or your main site URL) |

3. **Save** and **redeploy** the Pages project (trigger a new deployment so the new env is used).

### 2.3 (Optional) Custom domain for Pages

If the frontend is on a custom domain (e.g. `www.parlaygorilla.com`):

- **Pages** → your project → **Custom domains** → add `www.parlaygorilla.com` (and optionally apex `parlaygorilla.com` with redirect to www). Cloudflare will provide SSL for these.

---

## Part 3: Checklist

- [ ] Oracle VM created; ports 22, 80, 443 open (security list + UFW via bootstrap)
- [ ] Bootstrap run; repo cloned at `/opt/parlaygorilla`; ownership `ubuntu:ubuntu`
- [ ] `.env` on VM with `DATABASE_URL`, `VERIFICATION_DELIVERY=db`, `SUI_*`, `REDIS_URL`, and all API keys/URLs
- [ ] GitHub secrets: `ORACLE_SSH_HOST`, `ORACLE_SSH_KEY`, (optional) `ORACLE_SSH_USER`
- [ ] First deploy: push to `main` or run “Deploy to Oracle” workflow; confirm `docker compose ps` shows api, verifier, nginx
- [ ] Migration 048 applied (automatic on first API start or run manually)
- [ ] Render verification worker paused or removed
- [ ] Cloudflare DNS: `api.parlaygorilla.com` → A record → Oracle VM IP (Proxied or DNS only)
- [ ] Cloudflare Pages env: `NEXT_PUBLIC_API_URL` and `PG_BACKEND_URL` → `https://api.parlaygorilla.com`; redeploy
- [ ] Smoke test: open `https://www.parlaygorilla.com`, check login/API calls; hit `https://api.parlaygorilla.com/health` and expect 200

---

## Troubleshooting

- **SSH / GitHub Action fails**: Check `ORACLE_SSH_KEY` has no extra newlines; use the same key that works with `ssh -i key ubuntu@<host>`. Ensure security list allows port 22 from the runner IP or 0.0.0.0/0.
- **502 / connection refused**: Ensure UFW allows 80/443; `docker compose -f docker-compose.prod.yml ps` shows api and nginx running; `docker compose logs nginx api` for errors.
- **api.parlaygorilla.com unreachable or ERR_QUIC_PROTOCOL_ERROR**: See [Backend Cloudflare Cutover Runbook](deploy/BACKEND_CLOUDFLARE_CUTOVER_RUNBOOK.md). Check DNS A record for `api` → VM IP; SSL mode **Flexible** when proxied; if the browser shows QUIC errors, turn **HTTP/3 (with QUIC)** off in Cloudflare → Network.
- **Verifier not processing**: `docker compose logs verifier`; confirm `VERIFICATION_DELIVERY=db` and `SUI_*` in `.env`; confirm migration 048 applied (`processing_started_at` column exists).
- **Frontend still calling old API**: Redeploy Pages after changing env vars; hard-refresh or clear cache; confirm `NEXT_PUBLIC_API_URL` and `PG_BACKEND_URL` in the build.
