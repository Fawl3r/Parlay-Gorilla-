# Level-2 production hardening runbook

This doc covers ops verification token, Telegram alerts, job freshness, regression gate, and manual rollback.

---

## 1. Rotate OPS_VERIFY_TOKEN

Used to protect `/ops/version`, `/ops/verify`, and `/ops/deploy-status` behind Cloudflare/WAF.

1. **Generate a new token:** e.g. `openssl rand -hex 32`.
2. **On the Oracle VM:** update `/etc/parlaygorilla/backend.env`:
   ```bash
   OPS_VERIFY_TOKEN=<new_long_random_string>
   ```
3. **In GitHub:** Settings → Secrets and variables → Actions → update secret `OPS_VERIFY_TOKEN` with the same value.
4. **Restart the backend** so it picks up the new env: `sudo systemctl restart parlaygorilla-backend`.
5. **Verify:** `curl -sS -H "x-ops-token: NEW_TOKEN" https://api.parlaygorilla.com/ops/verify` returns `{"ok":true,"git_sha":"..."}`.

---

## 2. Rotate Telegram secrets

Used for deploy-failure and ops_watchdog (job staleness) alerts.

1. **Create/use a bot:** [@BotFather](https://t.me/BotFather) → new bot or use existing → copy **token**.
2. **Get chat ID:** add the bot to a group or message it; use an ID lookup (e.g. [api.telegram.org](https://api.telegram.org/bot<token>/getUpdates)) to get `chat_id`.
3. **GitHub:** Settings → Secrets → set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` (or use the same values as in backend env for server-side alerts).
4. **Backend (VM):** in `/etc/parlaygorilla/backend.env` set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` (or `TELEGRAM_ALERT_CHAT_ID`) so ops_watchdog can send alerts. Restart backend after change.

Never commit tokens; never log or echo them.

---

## 3. Interpret /ops/model-health (jobs_freshness and pipeline_blockers)

- **`pipeline_ok`:** `true` when there are no blockers (resolver running recently, enough resolved data).
- **`pipeline_blockers`:** list of strings, e.g. `["result_resolution has not run in 2 hours"]` or `["no resolved predictions"]`.
- **`jobs_freshness`:** per-job `last_run_at`, `stale` (true if no run within `stale_after_minutes`), and `stale_after_minutes`:
  - `result_resolution`: 120 min
  - `calibration_trainer`: 720 min (12 h)
  - `alpha_feature_discovery`: 1440 min (24 h)
  - `alpha_research`: 1440 min (24 h)

If `result_resolution` is stale or "result_resolution has not run in 2 hours" is in `pipeline_blockers`, the deploy regression gate fails and the blue/green script rolls back. The ops_watchdog job (every 30 min) sends a rate-limited Telegram alert for the same condition.

---

## 4. Manual rollback (slot)

If you need to revert to the previous slot without running a full deploy:

1. **SSH to the Oracle VM.**
2. **See current slot:** `readlink -f /opt/parlaygorilla/current` → e.g. `.../releases/green`.
3. **Switch to the other slot:**  
   - If current is `green`, run: `sudo ln -sfn /opt/parlaygorilla/releases/blue /opt/parlaygorilla/current`  
   - If current is `blue`, run: `sudo ln -sfn /opt/parlaygorilla/releases/green /opt/parlaygorilla/current`
4. **Restart backend:** `sudo systemctl restart parlaygorilla-backend`
5. **Verify:** `curl -sS -H "x-ops-token: $OPS_VERIFY_TOKEN" http://127.0.0.1:8000/ops/verify` and confirm `git_sha` matches the previous release (e.g. from the other slot’s `.gitsha` file).

---

## 5. Check deploy.log and last_deploy.json

- **Deploy log:** `/var/log/parlaygorilla/deploy.log` (or `$BASE/deploy.log` if that dir isn’t writable). Each line includes `deploy_id` and `correlation_id` for tracing.
- **Last successful deploy metadata:** `/opt/parlaygorilla/last_deploy.json` (path overridable with `LAST_DEPLOY_JSON_PATH` on the backend). Contains:
  - `deployed_sha`
  - `slot` (blue or green)
  - `deploy_time`
  - `deploy_id`
  - `duration_ms`

**From outside the VM:** use `GET /ops/deploy-status` with header `x-ops-token` to read `last_deploy` and compare with `current_sha` (see [Part 1](#1-rotate-ops_verify_token) for token).

---

## 6. Regression gate and auto-rollback

The blue/green deploy script (`backend/scripts/deploy_bluegreen.sh`) after cutover:

1. Calls `/ops/model-health` (with `x-ops-token` if `OPS_VERIFY_TOKEN` is set).
2. If `pipeline_ok` is false **and** `pipeline_blockers` contains "result_resolution has not run in 2 hours", it treats this as a regression:
   - Rolls back the symlink to the previous slot.
   - Restarts the backend.
   - Confirms `/ops/verify` returns the previous SHA (when available).
   - Exits non-zero so the GitHub Actions workflow fails.

So a deploy only “sticks” if the new slot passes the regression gate. Alerts (Telegram from workflow and ops_watchdog) help you notice failures and resolver staleness quickly.
