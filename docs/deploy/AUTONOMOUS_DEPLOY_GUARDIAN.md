# Autonomous Deploy Guardian

The Deploy Guardian runs on a schedule and after deployments to detect **production drift** (frontend Vercel vs backend Oracle) and deployment failures. It is **read-only**, fails CI loudly on drift/error, and sends **Telegram alerts** (rate-limited: on state change or at most once per 60 minutes).

## How it works

- **Backend check:** `GET BACKEND_URL/ops/verify` with header `x-ops-token` (requires `OPS_VERIFY_TOKEN`). Parses `git_sha`.
- **Frontend check:** `GET FRONTEND_URL/api/version`. Parses `git_sha` from the minimal Next.js API route (no auth).
- **Expected SHA:** From env `EXPECTED_SHA`, or fetched from GitHub API (`GITHUB_REPOSITORY` + `GITHUB_TOKEN`) for latest `main` commit.
- **Drift states:** `OK`, `BACKEND_DRIFT`, `FRONTEND_DRIFT`, `SPLIT_BRAIN` (backend ≠ frontend), `UNKNOWN` (sha missing), `ERROR` (network/auth).
- **CI:** Workflow fails (exit 1) on `BACKEND_DRIFT`, `FRONTEND_DRIFT`, `SPLIT_BRAIN`, or `ERROR`. Telegram alert is sent before exit when configured.

## Required GitHub configuration

### Repository variables (Settings → Secrets and variables → Actions → Variables)

| Variable | Example | Description |
|----------|---------|-------------|
| **BACKEND_URL** | `https://api.parlaygorilla.com` | Production backend base URL (used for `/ops/verify`). |
| **FRONTEND_URL** | `https://parlaygorilla.com` | Production frontend base URL (used for `/api/version`). |

### Secrets (Settings → Secrets and variables → Actions → Secrets)

| Secret | Description |
|--------|-------------|
| **OPS_VERIFY_TOKEN** | Token sent as `x-ops-token` to `/ops/verify`. Must match backend VM env. Required for backend check (Cloudflare/WAF). |
| **TELEGRAM_BOT_TOKEN** | Telegram bot token (from @BotFather). Optional; if missing, no alerts sent. |
| **TELEGRAM_CHAT_ID** | Chat or group ID for alerts. Optional; if missing, no alerts sent. |

`GITHUB_TOKEN` is provided automatically in GitHub Actions; the script uses it to fetch the expected commit SHA from the GitHub API when `EXPECTED_SHA` is not set.

## Workflow triggers

- **Schedule:** Every 15 minutes (`*/15 * * * *`).
- **After backend deploy:** On completion of workflow **Deploy Backend (Oracle Blue/Green)**.
- **Push to main:** On every push to `main` (fallback).

Concurrency group `deploy-guardian` prevents overlapping runs.

## Testing locally

1. Export required env (at least for production URLs):
   ```bash
   export BACKEND_URL="https://api.parlaygorilla.com"
   export FRONTEND_URL="https://parlaygorilla.com"
   export OPS_VERIFY_TOKEN="your-ops-token"
   ```
2. Optional: `EXPECTED_SHA`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GITHUB_REPOSITORY`, `GITHUB_TOKEN` (for expected SHA from GitHub).
3. From repo root:
   ```bash
   python backend/scripts/deploy_guardian.py
   ```
4. Exit 0 = OK or UNKNOWN; exit 1 = drift or ERROR.

State file (rate limiting) is written to `backend/scripts/.deploy_guardian_state.json` by default, or `GUARDIAN_STATE_PATH` if set.

## Interpreting alerts

Telegram messages include:

- **State:** OK, BACKEND_DRIFT, FRONTEND_DRIFT, SPLIT_BRAIN, UNKNOWN, ERROR.
- **Reason:** Short explanation (e.g. "backend (abc1234) != expected (def5678)").
- **Expected / Backend / Frontend SHA** (or error).
- **Timestamp** and, in CI, a link to the GitHub Actions run.

**BACKEND_DRIFT:** Backend is not on the expected commit (e.g. deploy didn’t complete or wrong branch).  
**FRONTEND_DRIFT:** Frontend is not on the expected commit.  
**SPLIT_BRAIN:** Backend and frontend SHAs differ (e.g. one deployed, the other not).  
**ERROR:** Network or auth failure (e.g. 403 on `/ops/verify` → check `OPS_VERIFY_TOKEN` and Cloudflare).

## Silencing alerts without breaking checks

- Remove or leave unset **TELEGRAM_BOT_TOKEN** and **TELEGRAM_CHAT_ID**. The guardian still runs and fails CI on drift/error; it simply does not send Telegram messages.
- Do not remove **OPS_VERIFY_TOKEN** or **BACKEND_URL** if you want the backend check to succeed behind Cloudflare.

## Files involved

- **Script:** `backend/scripts/deploy_guardian.py`
- **Frontend version endpoint:** `frontend/app/api/version/route.ts` (returns `{ git_sha }`, `Cache-Control: no-store`)
- **Workflow:** `.github/workflows/deploy_guardian.yml`
- **State (do not commit):** `backend/scripts/.deploy_guardian_state.json` (local) or workflow cache `deploy_guardian_state.json` (CI)

## Cloudflare / caching

- Backend `/ops/verify` is protected by `x-ops-token`; no change to Cloudflare security.
- Frontend `/api/version` is public, no auth; `Cache-Control: no-store` is set in the route and in `next.config.js` for `/api/version` so caches do not serve stale SHAs.
