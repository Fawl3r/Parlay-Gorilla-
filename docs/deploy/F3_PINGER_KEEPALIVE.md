# F3 Pinger (Parlay Gorilla keepalive) — summary for another dev

## What it is

A small keep-alive service that hits the Parlay Gorilla site and API on a schedule so **Render free-tier** services (and their DB) don’t cold-start as often.

## What it does each run

1. **GET homepage** — `https://www.parlaygorilla.com/`
2. **GET deep health** — `https://api.parlaygorilla.com/health?deep=1` (warms the DB)
3. **GET API health** — `https://api.parlaygorilla.com/health`

Order is fixed: homepage first, then post-load URLs, then the rest.

Each request is logged as one JSON line: `ts`, `url`, `ok`, `status`, `latency_ms`, `error`.  
Retries on timeout/5xx with backoff. Optional Telegram alerts after N consecutive failures or when latency exceeds a threshold (throttled per URL).

## Tech

- **Python 3.11+**, `requests`, `python-dotenv`
- No framework (plain script/modules)
- Config from env (or defaults): `TARGET_URLS`, `POST_LOAD_URLS`, `INTERVAL_SECONDS`, timeouts, retries, alert thresholds, optional `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`

## Where it runs

- **GitHub Actions:** `.github/workflows/keepalive.yml` runs every 10 minutes and executes `python -m keepalive.main --once`. No Render/dashboard access; purely external HTTP.
- **Local / VPS:** `python -m keepalive.main` loops forever with the configured interval between cycles.

## Repo layout (keepalive app)

- `keepalive/` — config, pinger, telegram, main/CLI
- `tests/` — unittest
- Root: `requirements.txt`, `.env.example`

## CLI

- `--once` — one cycle, exit code 0/1
- `--print-config` — print sanitized config

Health-endpoint **404s** are treated as **warnings** (no failure count, no nonzero exit).

## Relation to Parlay Gorilla

This repo is **Parlay Gorilla** (frontend + backend). The keepalive service is a **separate app** (F3 Pinger) that pings these URLs so free-tier Render services stay warm. If the keepalive repo is separate, link it here or in the team wiki.
