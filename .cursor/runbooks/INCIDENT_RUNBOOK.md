# Incident Runbook — Safety Mode YELLOW/RED

What to do when Safety Mode is YELLOW or RED and how to diagnose.

## Check current state

1. **GET /ops/safety** (no auth) or **GET /api/admin/safety** (admin auth).
2. Response: `state` (GREEN/YELLOW/RED), `reasons`, `telemetry` (last refresh times, error counts, API budget).

## YELLOW — Degraded

**Meaning:** Generation still runs but with capped legs and a warning.

**Typical causes:**

- Stale odds or games (refresh job delayed or failed).
- API budget ratio above threshold (e.g. 80% of daily quota used).
- Generation failures or API failures in window.

**Actions:**

1. Check **last_successful_games_refresh_at** and **last_successful_odds_refresh_at**. If old, check scheduler and refresh jobs: `GET /ops/jobs`.
2. Check **estimated_api_calls_today** vs **daily_api_budget**. If near limit, wait for rollover or reduce refresh frequency.
3. Check **error_count_5m**, **api_failures_30m**. If high, check logs and external API status (API-Sports, Odds API).
4. No immediate user impact beyond smaller max legs; monitor until GREEN.

## RED — Generation frozen

**Meaning:** Parlay suggest returns safe message; no builder run.

**Typical causes:**

- **error_count_5m** ≥ `SAFETY_MODE_RED_ERROR_COUNT_5M`.
- **not_enough_games_failures_30m** ≥ `SAFETY_MODE_RED_NOT_ENOUGH_GAMES_30M`.
- Combination of triggers (see `SAFETY_MODE_SPEC.md`).

**Actions:**

1. **Confirm:** GET /ops/safety; note `reasons` and telemetry.
2. **Logs:** Search for recent errors in parlay route, API-Sports client, Odds API, scheduler.
3. **Data:** Check games/odds freshness (e.g. GET /health/games, GET /health/parlay-generation). If data is stale, fix refresh jobs or upstream API.
4. **Recovery:** Resolving the underlying issue (refresh success, API recovery) and waiting for rolling windows to expire will allow state to return to YELLOW then GREEN. Optionally relax thresholds temporarily via env (not recommended long-term).
5. **Alert:** RED transition should trigger a Telegram admin alert (if `ADMIN_ALERTS_ENABLED` or telegram alerting is on). Confirm alert was sent and acknowledge.

## Safety gate (merge policy)

- **No merge if Safety Mode ≠ GREEN.** See `.cursor/runbooks/BUILD_CHECKLIST.md`.
- Exceptions: documented admin override only (e.g. incident ticket, reason, and timeline to restore GREEN).

## Escalation

- If RED persists and data/APIs look healthy: check telemetry for flapping or incorrect increments; consider resetting in-memory telemetry only in dev/staging (production: fix root cause).
- If scheduler is down: start scheduler process; ensure Redis and DB are reachable (see `/readyz`).
