# 502 Bad Gateway (Cloudflare → OCI Backend) — Diagnosis & Fix

**Context:** api.parlaygorilla.com returns 502 (Host Error). Cloudflare and browser work; origin is not responding.

**Assumptions:** Ubuntu on OCI, FastAPI + Uvicorn (Gunicorn) in Docker; Cloudflare proxied (orange cloud) hits origin on **port 80**.

---

## 1. Verify backend process status

**On the VM (SSH in):**

```bash
cd /opt/parlaygorilla

# How is the stack started? (systemd → docker compose)
sudo systemctl status parlaygorilla

# What is actually running?
sudo docker compose -f docker-compose.prod.yml ps
```

**Expected:** `parlaygorilla` service active; containers `parlaygorilla-api`, `parlaygorilla-scheduler`, **parlaygorilla-nginx** running.

**Start command (API):** The API runs via `scripts/entrypoint-api.sh` → Gunicorn bound to **0.0.0.0:8000** (correct; not 127.0.0.1).

```bash
# Confirm API process inside container
sudo docker compose -f docker-compose.prod.yml exec api ps aux
```

You should see `gunicorn` with `--bind 0.0.0.0:8000`.

---

## 2. Verify listening ports

```bash
# All listening TCP (prefer ss; netstat if ss missing)
ss -tlnp

# Or
netstat -tlnp 2>/dev/null || ss -tlnp
```

**Expected:**

| Port | Process | Purpose |
|------|---------|---------|
| **80** | nginx (parlaygorilla-nginx) | Cloudflare → origin (must be open) |
| **8000** | api container (mapped from host) | Optional direct API access |

If **port 80 is not listed**, nothing is accepting Cloudflare traffic → 502. Fix: ensure **nginx** is in the stack and running (see Section 7).

---

## 3. Verify OCI network access

**A. OCI Security List (VCN)**

- Oracle Cloud Console → **Networking** → **Virtual Cloud Networks** → select VCN → **Security Lists** → Ingress rules.
- **Required:** Allow **TCP 80** from **0.0.0.0/0** (or at least Cloudflare IP ranges). Add **TCP 443** if you add TLS at origin later.

**B. VM firewall (UFW)**

On the VM:

```bash
sudo ufw status

# If active, allow 80 (and 443 if used)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp   # optional, for future TLS
sudo ufw reload
```

---

## 4. Verify Cloudflare DNS

- **Cloudflare Dashboard** → **parlaygorilla.com** → **DNS** → **Records**.
- **A record** for `api` must point to the **current OCI VM public IP**.
- **Proxy status:** Proxied (orange cloud) = Cloudflare connects to your origin on **port 80** (HTTP). Ensure origin listens on 80.

**Confirm IP from VM:**

```bash
curl -s ifconfig.me
# or
curl -s icanhazip.com
```

Compare with the A record in Cloudflare. If they differ (e.g. VM IP changed), update the A record.

---

## 5. Verify HTTP reachability

**On the VM:**

```bash
# (A) Local to API (inside host, port 8000)
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health
# Expect: 200

# (B) Local to nginx (port 80) — this is what Cloudflare hits
curl -s -o /dev/null -w "%{http_code}" -H "Host: api.parlaygorilla.com" http://127.0.0.1:80/health
# Expect: 200
```

**From your machine (replace `<VM_PUBLIC_IP>` with actual IP):**

```bash
# (C) Direct to VM on port 80 (bypass Cloudflare)
curl -s -o /dev/null -w "%{http_code}" -H "Host: api.parlaygorilla.com" http://<VM_PUBLIC_IP>/health
# Expect: 200. If failure → firewall/security list or nginx not on 80.

# (D) Via Cloudflare
curl -s -o /dev/null -w "%{http_code}" https://api.parlaygorilla.com/health
# Expect: 200. If 502 here but (C) 200 → Cloudflare or DNS issue. If (C) fails → origin (nginx/API/port 80).
```

| (A) | (B) | (C) | (D) | Implication |
|-----|-----|-----|-----|--------------|
| 200 | 200 | 200 | 502 | Cloudflare/DNS or WAF; (C) proves origin is fine. |
| 200 | 5xx/empty | fail | 502 | Nginx not running or not on 80; fix stack (add/restart nginx). |
| 200 | 200 | fail | 502 | OCI security list or UFW blocking port 80. |
| 5xx | — | — | 502 | API unhealthy; check API logs and DB/Redis. |

---

## 6. Health endpoint validation

Backend exposes:

- **GET /health** — returns 200 and `{"status":"healthy",...}` (and optional keys). Use for external checks.
- **GET /healthz** — returns 200 and `{"ok":true}`. Used by Docker healthcheck and internal probes.

**On VM:**

```bash
curl -s http://127.0.0.1:80/health
curl -s http://127.0.0.1:8000/health
```

Both should return 200 and JSON with `"status":"healthy"` or `"ok":true`. If port 80 fails, nginx or routing is wrong.

---

## 7. Stable production setup (if missing)

**Root cause (typical):** Cloudflare connects to origin on **port 80**. If only the API container is running and bound to 8000, nothing listens on 80 → **502 Bad Gateway**.

**Fix:** Run **nginx** on 80/443 and reverse-proxy to the API on port 8000.

**7.1 Ensure nginx is in the stack**

`docker-compose.prod.yml` must include an **nginx** service:

- Image: `nginx:alpine`
- Ports: `80:80` (and `443:443` if you add TLS at origin)
- Volume: mount `./nginx/conf.d` to `/etc/nginx/conf.d:ro`
- Network: same as `api` (e.g. `app`) so `proxy_pass http://api:8000` resolves

**7.2 Exact nginx config (already in repo)**

File: `nginx/conf.d/default.conf`

```nginx
upstream api {
    server api:8000;
}

server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

**7.3 Start/restart the stack**

On the VM:

```bash
cd /opt/parlaygorilla
sudo docker compose -f docker-compose.prod.yml up -d --build
sudo docker compose -f docker-compose.prod.yml ps
ss -tlnp | grep -E ':80|:8000'
```

Then re-run the curl tests from Section 5 (B) and (C).

**7.4 systemd (boot)**

Ensure the stack starts on boot:

```bash
sudo systemctl enable parlaygorilla
sudo systemctl status parlaygorilla
```

Unit file: `docs/systemd/parlaygorilla.service` — runs `docker compose -f docker-compose.prod.yml up -d --build` from `/opt/parlaygorilla`.

---

## Root cause (one sentence)

**Cloudflare proxies to origin on port 80; if only the API is running on port 8000 and nginx is not in the stack or not running, nothing listens on 80 → connection refused → 502 Bad Gateway.**

---

## Verification checklist (after fix)

- [ ] `sudo docker compose -f /opt/parlaygorilla/docker-compose.prod.yml ps` shows **api**, **scheduler**, **nginx** running.
- [ ] `ss -tlnp` shows **:80** (nginx) and **:8000** (API host mapping).
- [ ] `curl -s -o /dev/null -w "%{http_code}" -H "Host: api.parlaygorilla.com" http://127.0.0.1:80/health` → **200**.
- [ ] From your PC: `curl -s -o /dev/null -w "%{http_code}" http://<VM_PUBLIC_IP>/health` (with Host header if needed) → **200**.
- [ ] From your PC: `curl -s -o /dev/null -w "%{http_code}" https://api.parlaygorilla.com/health` → **200**.
- [ ] OCI Security List allows TCP 80 (and 443 if used) from 0.0.0.0/0; UFW allows 80 (and 443 if used).
- [ ] Cloudflare A record for `api` points to the current VM public IP; proxy (orange cloud) enabled.
