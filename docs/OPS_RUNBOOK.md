# Parlay Gorilla — Ops Runbook (Oracle VM + Render)

## Restart services

```bash
sudo systemctl restart parlaygorilla-api
sudo systemctl restart parlaygorilla-scheduler
```

## Logs

```bash
# API — follow logs
journalctl -u parlaygorilla-api -f

# Scheduler — follow logs
journalctl -u parlaygorilla-scheduler -f

# Last 100 lines
journalctl -u parlaygorilla-api -n 100
```

## Validate

```bash
# Readiness (DB + Redis)
curl -s https://api.parlaygorilla.com/readyz | jq

# Liveness
curl -s https://api.parlaygorilla.com/healthz

# Job status (last run per job)
curl -s https://api.parlaygorilla.com/ops/jobs | jq
```

## Rotate env

1. Edit env on the VM: `sudo nano /etc/parlaygorilla.env`
2. Reload systemd and restart:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart parlaygorilla-api
   sudo systemctl restart parlaygorilla-scheduler
   ```

## Smoke test (from repo root)

```bash
# Default: https://api.parlaygorilla.com
python scripts/smoke_test.py

# Custom base URL
API_BASE_URL=https://api.staging.example.com python scripts/smoke_test.py
```

## Health endpoints

| Endpoint    | Purpose |
|------------|---------|
| `GET /healthz` | Liveness: `{"ok": true}` |
| `GET /readyz`  | Readiness: DB + Redis; 503 if not ready |
| `GET /ops/jobs` | Last run status per scheduler job |
| `GET /health`   | Legacy health with status/timestamp |
| `GET /health/db` | DB-only check |

## Render Postgres + Redis

- **DATABASE_URL**: Use `postgresql+asyncpg://...?sslmode=require` for Render. Optional: `connect_timeout=10` in URL.
- **REDIS_URL**: Set from Render Redis dashboard. Backend uses it for cache, scheduler lock, and alert dedupe.

## Telegram alerts

- Set `TELEGRAM_ALERT_CHAT_ID` (or `TELEGRAM_CHAT_ID`) and `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALERTS_ENABLED=true`.
- Alerts fire on: unhandled API exceptions, scheduler job failures.
- Rate limit: 1 per unique error fingerprint per 10 min; max 1 msg/10 sec.
