# Parlay Gorilla — Ops Runbook (Oracle VM, Docker-first)

## Infra (locked)

- **Frontend:** Vercel + Cloudflare  
- **Backend:** Oracle VM + Cloudflare  
- **Postgres + Redis:** Render  

Backend runs as three Docker services: **api**, **scheduler**, and **nginx**. Nginx listens on port 80 (Cloudflare → origin). No Postgres/Redis in Docker; connect via `DATABASE_URL` and `REDIS_URL` in `.env.prod`.

---

## First-time server setup

The **Deploy to Oracle** GitHub Action (`.github/workflows/deploy-oracle.yml`) creates **.env.prod** on the server from GitHub Secrets before each deploy. No manual SSH needed if secrets are set.

**Secrets** (Settings → Secrets and variables → Actions → Secrets):

| Secret | Required | Purpose |
|--------|----------|---------|
| `ORACLE_SSH_HOST` | Yes | VM hostname or IP |
| `ORACLE_SSH_KEY` | Yes | Private key for SSH |
| `DATABASE_URL` | Yes | Render Postgres URL |
| `REDIS_URL` | Yes | Render Redis URL |
| `TELEGRAM_BOT_TOKEN` | Yes | Operator alerts |
| `TELEGRAM_ALERT_CHAT_ID` | Yes | Alert chat ID |
| `JWT_SECRET` | Yes | Auth signing |
| `THE_ODDS_API_KEY` | Yes | Odds API |
| `OPENAI_API_KEY` | No | Gorilla Bot / AI |

**Variables** (same → Variables; optional):

| Variable | Purpose |
|----------|---------|
| `ORACLE_SSH_USER` | SSH user (default `ubuntu`) |
| `OPS_DEBUG_ENABLED` | Set `true` to enable /ops |
| `OPS_DEBUG_TOKEN` | Optional token for /ops |

On each deploy, the workflow writes these into `/opt/parlaygorilla/.env.prod` and then runs `scripts/deploy.sh`. Do **not** commit `.env.prod`; it exists only on the server.

**Manual option:** If you prefer not to use secrets for env, SSH to the VM, `cd /opt/parlaygorilla`, create `.env.prod` yourself (see **Env (production)** below), then re-run the workflow or `bash scripts/deploy.sh`.

---

## Quick commands

### Restart everything (e.g. after VM reboot or deploy)

```bash
sudo systemctl restart parlaygorilla
```

### View logs

```bash
cd /opt/parlaygorilla   # or your deploy path

# API
docker compose -f docker-compose.prod.yml logs -f api

# Scheduler
docker compose -f docker-compose.prod.yml logs -f scheduler

# Nginx (reverse proxy; port 80)
docker compose -f docker-compose.prod.yml logs -f nginx
```

### Health and job status

```bash
# Liveness (returns {"ok": true})
curl -s http://localhost:8000/healthz

# Readiness (DB + Redis)
curl -s http://localhost:8000/readyz

# Last scheduler job runs (from DB)
curl -s http://localhost:8000/ops/jobs
```

If the API is behind Cloudflare, use your public origin URL instead of `localhost:8000` for external checks.

**502 Bad Gateway (api.parlaygorilla.com):** Cloudflare hits origin on port 80. If nginx is not running or port 80 is blocked, you get 502. Use the **OCI 502 Incident Runbook:** **[docs/OPS_502_INCIDENT_RUNBOOK.md](docs/OPS_502_INCIDENT_RUNBOOK.md)** — triage, recovery, root-cause checks, hardening, and emergency capture pack.

---

## Service layout

| Service   | Role                                      | Restart      | Healthcheck   |
|-----------|-------------------------------------------|-------------|---------------|
| **api**   | FastAPI/Gunicorn; port 8000               | `restart: always` | GET /healthz |
| **scheduler** | Standalone Python loop; Redis lock; writes job status to Postgres; Telegram on failure | `restart: always` | — |
| **nginx** | Reverse proxy; port 80 → api:8000 (Cloudflare hits 80) | `restart: always` | — |

- **api** sets `SCHEDULER_STANDALONE=true` so the in-process scheduler is **not** started (avoids double-run with multiple workers).
- **scheduler** runs `python -m app.workers.scheduler_main` in a loop (e.g. every 1h), runs due jobs (sport state 6h, daily pass), uses Redis lock, records to `scheduler_job_runs`, sends Telegram alerts on failure (rate-limited).

---

## API auto-migrate (advisory lock)

On **API container start**, the entrypoint runs DB migrations under a Postgres advisory lock, then starts Gunicorn. Only one process migrates; other replicas wait for the lock then continue (sub-second when DB is already at head). The **scheduler** container uses the same image but overrides CMD and **does not run migrations**.

- **Lock:** `pg_advisory_lock` so scaling to multiple API replicas is safe; no double-migrate.
- **Timeout:** Optional env `MIGRATION_LOCK_TIMEOUT_SECONDS` (default 600) caps how long a replica waits for the lock before exiting non-zero.
- **Failure:** If the DB is unreachable or migrations fail, the API container exits non-zero and Docker restart policy applies.

**Manual migration** (e.g. one-off from your machine or a job):

```bash
docker compose -f docker-compose.prod.yml run --rm api python -m app.ops.migrate_with_lock
```

This uses the same lock; if the API is already running and migrating, the manual run will wait for the lock.

**Smoke (when DB is available):** From repo root, `python scripts/smoke_migrate.py` (or `cd backend && python -m app.ops.migrate_with_lock`). Exit 0 means migrations ran or DB already at head.

---

## Endpoints

- **GET /healthz** — Liveness; returns `{ "ok": true }`.
- **GET /readyz** — Readiness; checks DB + Redis; 200 when both reachable, 503 otherwise.
- **GET /ops/jobs** — Last run status per scheduler job: `job_name`, `last_run_at`, `duration_ms`, `status`, `error_snippet`.

All error responses and logs include **request_id** (and scheduler alerts include a correlation id) for tracing.

---

## Env (production)

Create **.env.prod** at repo root (do not commit). Required:

- `DATABASE_URL` — Render Postgres URL  
- `REDIS_URL` — Render Redis URL  
- `TELEGRAM_BOT_TOKEN` — For operator alerts  
- `TELEGRAM_ALERT_CHAT_ID` — Chat ID for alerts  
- `SCHEDULER_STANDALONE=true` — Set in compose for api service; do not start in-process scheduler in API.

Optional: `TELEGRAM_ALERTS_ENABLED=true` to enable Telegram; notifier is rate-limited and deduped (e.g. 10 min TTL, 1 msg/10 sec).

---

## systemd (VM boot + restart)

1. Copy unit file:
   ```bash
   sudo cp docs/systemd/parlaygorilla.service /etc/systemd/system/
   ```
2. If deploy path is not `/opt/parlaygorilla`, edit the unit:
   - `WorkingDirectory=`
   - `ExecStart=` and `ExecStop=` paths.
3. Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable parlaygorilla
   sudo systemctl start parlaygorilla
   ```

After a VM reboot, `parlaygorilla` will start automatically and bring up api + scheduler with `restart: always`.

---

## Watchdog (self-heal if nginx/api go down)

If the VM is up but the stack is unhealthy (e.g. nginx not listening on :80, API crash-loop), enable the watchdog timer.

1. Install watchdog script + unit files:

```bash
cd /opt/parlaygorilla

sudo cp scripts/parlaygorilla-watchdog.sh /usr/local/bin/parlaygorilla-watchdog.sh
sudo chmod +x /usr/local/bin/parlaygorilla-watchdog.sh

sudo cp docs/systemd/parlaygorilla-watchdog.service /etc/systemd/system/
sudo cp docs/systemd/parlaygorilla-watchdog.timer /etc/systemd/system/
```

2. Enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now parlaygorilla-watchdog.timer
sudo systemctl status parlaygorilla-watchdog.timer --no-pager
```

3. View watchdog logs (journald):

```bash
sudo journalctl -u parlaygorilla-watchdog.service -n 200 --no-pager
```

---

## Caching (Cloudflare)

The API sets **Cache-Control** for:

- `/api/sports`, `/api/games`, `/api/analysis`, `/api/game`  
- Value: `max-age=60, must-revalidate`  

So /sports and game/analysis state are not cached for long and won’t stay stale for hours.

---

## Acceptance checklist

- [ ] VM reboot → docker services (api, scheduler, nginx) come up automatically.  
- [ ] **GET /readyz** returns OK when Render Postgres and Redis are reachable.  
- [ ] API runs migrations on boot (advisory lock); scheduler does not run migrations.  
- [ ] Multiple API replicas: only one migrates; others wait then start (safe for scaling).  
- [ ] Scheduler runs independently of API worker count (standalone process + Redis lock).  
- [ ] Roster/injuries (scheduler) failures send at most one Telegram alert (rate-limited, no spam).  
- [ ] /sports state is not stale for hours due to caching (Cache-Control on critical paths).  
- [ ] Logs and error responses include **request_id** for correlation.
