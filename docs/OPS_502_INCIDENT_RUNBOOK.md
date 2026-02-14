# OCI 502 Incident Runbook — Parlay Gorilla

**Product:** Parlay Gorilla · **Domain:** https://api.parlaygorilla.com · **CDN:** Cloudflare (proxied) · **Host:** Oracle OCI VM (Ubuntu)

**Runtime:** systemd unit `parlaygorilla` runs Docker Compose from `/opt/parlaygorilla`. Stack: **api** (FastAPI/Gunicorn :8000), **scheduler**, **nginx** (:80 → api:8000). Postgres/Redis external via `.env.prod`.

**Symptom:** Intermittent Cloudflare **502 Bad Gateway (Host Error)** — origin stops responding on :80.

---

## A) Quick Triage (~2 minutes)

### 1. SSH and shell

```bash
ssh -i /path/to/key ubuntu@<ORACLE_VM_IP>
# or: ssh ubuntu@<ORACLE_VM_IP>
```

### 2. Local origin check

```bash
# Must succeed if nginx is up and responding (nginx returns 200 from fallback even when api is down)
curl -fsS -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1/health
# Expect: 200

# Direct API (bypass nginx)
curl -fsS -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:8000/healthz
# Expect: 200
```

### 3. Decision tree

| `/health` on :80 | `/healthz` on :8000 | Interpretation |
|------------------|---------------------|----------------|
| 200 | 200 | Origin OK; 502 may be transient or Cloudflare/edge. Check CF status / retry. |
| 200 | 5xx / timeout | Nginx up, API down. Restart api (or full stack). |
| 5xx / timeout | 200 | Nginx down or not bound to 80. Restart nginx or full stack. |
| 5xx / timeout | 5xx / timeout | Both down or host/network issue. Full stack restart + root-cause checks. |

---

## B) Status & Logs

### systemd

```bash
systemctl status parlaygorilla
journalctl -u parlaygorilla -n 100 --no-pager
journalctl -u parlaygorilla -f   # follow
```

### Docker Compose

```bash
cd /opt/parlaygorilla
docker compose -f docker-compose.prod.yml ps
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Focused logs (tail counts)

```bash
cd /opt/parlaygorilla
docker compose -f docker-compose.prod.yml logs --tail=100 api
docker compose -f docker-compose.prod.yml logs --tail=100 nginx
docker compose -f docker-compose.prod.yml logs --tail=100 scheduler
```

---

## C) Networking & Ports

### Host listeners

```bash
sudo ss -tlnp | grep -E ':80|:443|:8000'
# Expect: :80 (nginx), :8000 (api) if exposed for debug
```

### Nginx → API reachability (inside Docker)

```bash
docker exec parlaygorilla-nginx wget -qO- --timeout=3 http://api:8000/healthz || echo "FAIL"
# Expect: {"ok":true} or similar
```

### When to suspect OCI Security Lists / NSGs

- **Port 80** must be open **ingress** on the VM’s subnet (e.g. 0.0.0.0/0 or Cloudflare IPs) in OCI Security List / NSG.
- If `curl http://127.0.0.1/health` works but public `https://api.parlaygorilla.com/health` fails from outside, check OCI firewall and Cloudflare DNS (orange cloud = proxy; origin must be reachable on 80/443 from CF).

---

## D) One-Command Recovery

### Preferred (systemd)

```bash
sudo systemctl restart parlaygorilla
# Unit runs: compose up -d --build, then waits for /health on :80 and /healthz on :8000 (up to 30s + 90s).
```

### Fallback (manual compose)

```bash
cd /opt/parlaygorilla
sudo docker compose -f docker-compose.prod.yml down
sudo docker compose -f docker-compose.prod.yml up -d --build
# Then verify (see H).
```

### Post-restart verification

```bash
curl -fsS http://127.0.0.1/health
curl -fsS http://127.0.0.1:8000/healthz
docker compose -f docker-compose.prod.yml ps
# All services "running", healthchecks passing.
```

---

## E) Root Cause Checks

### OOM killer

```bash
sudo dmesg -T | grep -i -E 'oom|killed|out of memory'
```

### Memory and disk

```bash
free -h
df -h
```

### Common causes

| Cause | What to check / fix |
|-------|----------------------|
| OOM | Reduce Gunicorn workers or add swap (see F.7). |
| Migrations failing on start | `docker compose logs api` for migration errors; fix DB or migration, then restart. |
| Nginx not bound to 80 | Another process on 80, or container not started; `ss -tlnp`, restart stack. |
| API crash loop | Logs for Python tracebacks; DB/Redis unreachable, bad env, or code bug. |

---

## F) Hardening (Prevent Recurrence)

### F.1 Docker Compose healthchecks (already present)

- **api:** `curl -fsS http://localhost:8000/healthz` every 30s, 3 retries, start_period 40s.
- **nginx:** `wget -qO- http://127.0.0.1/health` every 15s, 10 retries, start_period 10s.

Keep these; they allow `depends_on` with `condition: service_healthy` for nginx (see F.4).

### F.2 nginx `/health` fallback (already present)

`nginx/conf.d/default.conf` already defines `location = /health` with `proxy_intercept_errors on` and `error_page 502 503 504 = @health_fallback`. The fallback returns HTTP 200 with `{"status":"degraded",...,"source":"nginx-fallback"}` so Cloudflare does not see 502 when the API is restarting. No change needed.

### F.3 depends_on / upstream retry

- Nginx already uses short timeouts for `/health` (1s connect, 2s send/read) so it fails fast and serves the fallback.
- Optional: set nginx to start only after api is healthy (F.4).

### F.4 nginx depends_on api (condition: service_healthy)

In `docker-compose.prod.yml`, under `nginx:` set:

```yaml
depends_on:
  api:
    condition: service_healthy
```

So nginx starts only after api’s healthcheck passes. Reduces 502s during deploy/restart.

### F.5 systemd unit (existing post-start verification)

The unit already has:

- `ExecStartPost`: `docker compose ... ps`
- `ExecStartPost`: wait up to 30s for `curl -fsS http://127.0.0.1/health`
- `ExecStartPost`: wait up to 90s for `curl -fsS http://127.0.0.1:8000/healthz`

So start is failed if origin or API is not responding. No change required for basic hardening.

### F.6 systemd watchdog (auto-restart if `/health` fails)

A timer runs **scripts/health-watchdog.sh** every 2 minutes. If `http://127.0.0.1/health` does not return 200 within 5s, it runs `systemctl restart parlaygorilla`.

- **Script:** `scripts/health-watchdog.sh` (checks HEALTH_URL, restarts parlaygorilla on failure).
- **Units:** `docs/systemd/parlaygorilla-watchdog.service`, `docs/systemd/parlaygorilla-watchdog.timer`.

Install (on the VM, from repo root or deploy path):

```bash
# From /opt/parlaygorilla
sudo cp docs/systemd/parlaygorilla-watchdog.service /etc/systemd/system/
sudo cp docs/systemd/parlaygorilla-watchdog.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now parlaygorilla-watchdog.timer
```

Ensure `scripts/health-watchdog.sh` is executable: `chmod +x scripts/health-watchdog.sh`.

### F.7 Swap (low-RAM OCI shapes)

If OOM is likely (e.g. &lt;2 GB RAM):

```bash
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### F.8 Gunicorn workers (safe defaults)

Keep workers low on small VMs to avoid OOM. In entrypoint or env, e.g.:

- `--workers 2` (or 1 on 1 GB)
- `--threads 2` if using gthread
- Optionally `--max-requests 1000` / `--max-requests-jitter 50` to recycle workers.

---

## G) Deploy Safety

`scripts/deploy.sh` **already** does fail-fast:

1. Build, then `up -d --remove-orphans`.
2. Wait for `http://127.0.0.1/health` (30×1s), then `http://127.0.0.1:8000/healthz` (90×1s), then `http://127.0.0.1:8000/readyz` (60×1s).
3. On any timeout: runs `dump_debug` (compose ps, logs for api/nginx/scheduler, dmesg OOM), then exits 1.

No change required.

---

## H) Verification Checklist

- [ ] **Localhost /health:** `curl -fsS http://127.0.0.1/health` → 200.
- [ ] **Localhost /healthz:** `curl -fsS http://127.0.0.1:8000/healthz` → 200.
- [ ] **Container health:** `docker compose -f docker-compose.prod.yml ps` — api and nginx (healthy).
- [ ] **Public:** `curl -sS -o /dev/null -w "%{http_code}" https://api.parlaygorilla.com/health` → 200 (through Cloudflare).
- [ ] **Simulated API failure:** `docker stop parlaygorilla-api` → `/health` on :80 still 200 (nginx fallback). Restart api → `/health` returns API JSON again.

---

## I) Emergency Capture Pack

Run this block when 502 is occurring to snapshot state (copy-paste as one block):

```bash
CAPTURE_DIR="/opt/parlaygorilla/captures"
mkdir -p "$CAPTURE_DIR"
TS=$(date -u +%Y%m%d-%H%M%S)
CAP="$CAPTURE_DIR/502-capture-$TS"
{
  echo "=== $TS ==="
  echo "--- curl 127.0.0.1/health ---"
  curl -sS -w "\nhttp_code=%{http_code}\n" --max-time 5 http://127.0.0.1/health || true
  echo "--- curl 127.0.0.1:8000/healthz ---"
  curl -sS -w "\nhttp_code=%{http_code}\n" --max-time 5 http://127.0.0.1:8000/healthz || true
  echo "--- ss -tlnp ---"
  sudo ss -tlnp
  echo "--- docker ps -a ---"
  docker ps -a
  echo "--- compose ps ---"
  cd /opt/parlaygorilla && docker compose -f docker-compose.prod.yml ps
  echo "--- systemctl status ---"
  systemctl status parlaygorilla --no-pager || true
  echo "--- free -h ---"
  free -h
  echo "--- df -h ---"
  df -h
  echo "--- dmesg OOM ---"
  sudo dmesg -T 2>/dev/null | grep -i -E 'oom|killed|out of memory' || true
  echo "--- logs api last 80 ---"
  docker compose -f docker-compose.prod.yml logs --tail=80 api 2>/dev/null || true
  echo "--- logs nginx last 30 ---"
  docker compose -f docker-compose.prod.yml logs --tail=30 nginx 2>/dev/null || true
} > "$CAP.txt" 2>&1
echo "Capture written to $CAP.txt"
```

---

## Reference: Key Paths and Commands

| Item | Value |
|------|--------|
| Working dir | `/opt/parlaygorilla` |
| Compose file | `docker-compose.prod.yml` |
| Env file | `.env.prod` (not committed) |
| Start (systemd) | `sudo systemctl start parlaygorilla` |
| Stop | `sudo systemctl stop parlaygorilla` |
| Restart | `sudo systemctl restart parlaygorilla` |
| Origin health | `curl -fsS http://127.0.0.1/health` |
| API liveness | `curl -fsS http://127.0.0.1:8000/healthz` |
