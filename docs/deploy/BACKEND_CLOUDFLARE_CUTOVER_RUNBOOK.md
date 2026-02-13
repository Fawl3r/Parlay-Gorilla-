# Backend Cloudflare Cutover Runbook

Use this when `https://api.parlaygorilla.com/health` is unreachable or returns errors (e.g. ERR_QUIC_PROTOCOL_ERROR) after moving the backend to Oracle + Cloudflare.

## 1. Validate Oracle VM (origin sanity)

Run from a machine where **SSH is in PATH** (e.g. Git Bash, WSL, or PowerShell with OpenSSH installed):

```powershell
$env:ORACLE_SSH_HOST = "<VM_PUBLIC_IP>"   # if not already set or different from script default
.\scripts\oracle-server-check.ps1
```

- **If the script fails (key not found / SSH not recognized)**: Install OpenSSH or run the script from Git Bash. Set `ORACLE_SSH_KEY_PATH` to your private key path and `ORACLE_SSH_HOST` to the Oracle VM public IP.
- **If health returns non-200 on the VM**:
  - SSH to the VM and run: `sudo docker compose -f /opt/parlaygorilla/docker-compose.prod.yml ps` and `sudo docker compose -f /opt/parlaygorilla/docker-compose.prod.yml logs nginx api`.
  - Ensure `api` and `nginx` are up; fix container or `.env` per [docs/setup-oracle-and-cloudflare.md](../setup-oracle-and-cloudflare.md).

## 2. Direct origin reachability

From your machine (no Cloudflare):

```bash
curl -s -o /dev/null -w "%{http_code}" http://<VM_PUBLIC_IP>/health
```

Expect **200**. If not, the issue is on the VM (nginx/API/UFW), not Cloudflare.

## 3. Cloudflare settings (api.parlaygorilla.com)

In **Cloudflare Dashboard** → **Websites** → **parlaygorilla.com**:

| Check | Where | What to verify |
|-------|--------|-----------------|
| **DNS** | DNS → Records | `api` **A** record → Oracle VM public IP. Proxy status: **Proxied** (orange) or **DNS only** (grey). |
| **SSL/TLS** | SSL/TLS | If proxied: **Flexible** (Cloudflare terminates HTTPS; origin is HTTP on port 80). |
| **HTTP/3 (QUIC)** | Network | If you see **ERR_QUIC_PROTOCOL_ERROR** in the browser: set **HTTP/3 (with QUIC)** to **Off** temporarily to confirm. Re-enable later if the issue is fixed. |

Sanity check (recommended):

- If `api` is **Proxied**, `nslookup api.parlaygorilla.com 1.1.1.1` should return **Cloudflare IPs** (e.g. `104.x`, `172.64.x`, `188.114.x`), **not** your VM IP.
- If it returns your **VM IP**, you are effectively **DNS only**, and `https://api.parlaygorilla.com` will fail unless you install TLS on the VM. Use `http://api.parlaygorilla.com/health` instead (or re-enable proxy).
- If Cloudflare shows **Proxied** but *your* machine still resolves `api.parlaygorilla.com` to the VM IP, your local DNS resolver/cache is stale. Fix by flushing DNS (Windows: `ipconfig /flushdns`) or temporarily using a public resolver (1.1.1.1 / 8.8.8.8) until caches expire.

## 4. If you get "Connection was reset" (curl 35) through Cloudflare

Origin returns 200 directly (`http://<VM_IP>/health`) but `curl --http1.1 -I https://api.parlaygorilla.com/health` fails with **Recv failure: Connection was reset**. That means the **Cloudflare → origin (VM:80)** connection is being dropped.

Do these on the VM (SSH in) and in Cloudflare:

| Step | Where | Action |
|------|--------|--------|
| **A record IP** | Cloudflare DNS | Ensure the `api` A record points to the **same** VM IP you use for direct `http://<VM_IP>/health`. If it points to an old/different IP, Cloudflare is talking to the wrong host. |
| **Port 80 open** | Oracle Cloud Console | **Networking** → VCN → **Security List** → Ingress: allow **TCP 80** from **0.0.0.0/0** (or at least not restricted to your own IP). |
| **UFW on VM** | SSH on VM | Run `sudo ufw status`. If active, ensure **80** is allowed: `sudo ufw allow 80/tcp && sudo ufw reload`. |
| **Host header** | SSH on VM | Confirm nginx accepts Cloudflare’s request: `curl -s -o /dev/null -w "%{http_code}" -H "Host: api.parlaygorilla.com" http://localhost/health` → expect **200**. |
| **See if request hits nginx** | SSH on VM | While someone runs `curl --http1.1 -I https://api.parlaygorilla.com/health` from outside, run `sudo docker compose -f /opt/parlaygorilla/docker-compose.prod.yml logs -f nginx` on the VM. If no log line appears, the connection is blocked before nginx (firewall/security list). If a line appears then connection closes, check nginx/API logs. |

After fixing the A record or firewall, wait a minute and retry `curl --http1.1 -I https://api.parlaygorilla.com/health`.

## 4b. Still connection reset with proxy on (DNS-only works)

If **api** works with **DNS only** but fails with **Proxied** (curl 35), the reset is at the Cloudflare edge or WAF.

| Step | Where | Action |
|------|--------|--------|
| **Skip WAF for API** | Security → **WAF** (or **Security** → **Settings** / **Configuration rules**) | Add a **Configuration rule** or **WAF exception**: when **Hostname** equals `api.parlaygorilla.com`, set **Security Level** to "Essentially Off" or **Skip** the managed ruleset. This rules out WAF/Managed rules (e.g. WordPress rules) from blocking or resetting API traffic. |
| **Confirm request reaches origin** | VM (SSH) | Run `sudo docker compose -f /opt/parlaygorilla/docker-compose.prod.yml logs -f nginx`. From your PC run `curl --http1.1 https://api.parlaygorilla.com/health`. If **no** new log line appears on the VM, the connection is dying before Cloudflare talks to the origin (edge/WAF). If a line **does** appear, the issue is on the response path. |
| **Try another network** | Optional | Use a different Wi‑Fi or mobile hotspot; rule out local AV/firewall interfering with Cloudflare IPs. |

After adding the WAF skip for `api.parlaygorilla.com`, purge cache and retry the curl.

## 5. External smoke test

After DNS/SSL and any connection-reset fixes (Section 4) are done:

```powershell
.\scripts\validate-api-health.ps1
```

Or manually:

- `https://api.parlaygorilla.com/health` → 200, body `"status":"healthy"`
- `https://api.parlaygorilla.com/health/db` → 200 if DB is reachable (or 503 if DB down; still confirms API is reachable)

## Done condition

- `oracle-server-check.ps1` reports **HTTP 200** for `http://localhost/health` on the VM.
- `https://api.parlaygorilla.com/health` returns **200** from your browser or `validate-api-health.ps1`.
