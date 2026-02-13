# Safety Mode Spec

Detailed spec for parlay generation Safety Mode: states, triggers, and behaviors.

## States

| State  | Meaning |
|--------|---------|
| **GREEN** | Normal operation; no restrictions. |
| **YELLOW** | Degraded: cap max legs, attach warning and reasons to response. |
| **RED**   | Generation frozen: return safe message (503 or 200 with body); do not run builder. |

## Triggers (env-configurable)

All in `backend/app/core/config.py`; see `backend/.env.example`.

| Env | Default | Effect |
|-----|---------|--------|
| `SAFETY_MODE_ENABLED` | true | Master kill switch. |
| `SAFETY_MODE_STALE_ODDS_SECONDS` | 900 | Odds older than this → YELLOW. |
| `SAFETY_MODE_STALE_GAMES_SECONDS` | 3600 | Games refresh older than this → YELLOW. |
| `SAFETY_MODE_YELLOW_API_BUDGET_RATIO` | 0.80 | Used/budget ≥ ratio → YELLOW. |
| `SAFETY_MODE_RED_ERROR_COUNT_5M` | 25 | Errors in 5m ≥ this → RED. |
| `SAFETY_MODE_RED_NOT_ENOUGH_GAMES_30M` | 10 | "Not enough games" count in 30m ≥ this → RED. |
| `SAFETY_MODE_YELLOW_GEN_FAILURES_5M` | 10 | Gen failures in 5m ≥ this → YELLOW. |
| `SAFETY_MODE_YELLOW_API_FAILURES_30M` | 15 | API failures in 30m ≥ this → YELLOW. |
| `SAFETY_MODE_YELLOW_MAX_LEGS` | 4 | In YELLOW, cap requested legs to this. |

## Telemetry (minimal)

Stored in-memory (see `backend/app/core/telemetry.py`). Keys:

- `last_successful_games_refresh_at`, `last_successful_odds_refresh_at` (timestamps)
- `error_count_5m`, `generation_failures_5m`, `not_enough_games_failures_30m`
- `api_429_count_30m`, `api_failures_30m`
- `estimated_api_calls_today`, `daily_api_budget` (config)

Schedulers/refresh jobs set last-refresh timestamps; parlay route and API clients increment failure/429 counters.

## Behaviors

### GREEN

- No changes to request or response.

### YELLOW

- Cap `num_legs` to `SAFETY_MODE_YELLOW_MAX_LEGS`.
- Response includes: `safety_mode: "YELLOW"`, `warning: "..."`, `reasons: [...]`.

### RED

- Do not call parlay builder.
- Return 503 or 200 with body: `safety_mode: "RED"`, `message: "Parlay generation temporarily paused for data reliability. Try again soon."`, `reasons: [...]`.
- Emit admin alert (Telegram) on transition to RED (rate-limited).

## Endpoints

- **GET /api/admin/safety** — Admin-only; current state, reasons, telemetry.
- **GET /ops/safety** — Public; same payload (no secrets) for frontend banner.

## Integration points

- **Parlay route:** At start of `suggest_parlay`, call `require_generation_allowed()`; if RED, return safe response; if YELLOW, `apply_degraded_policy(request_params)` then proceed.
- **API clients (API-Sports, Odds):** On 429 or failure, increment telemetry; optional request dedupe and TTL cache per existing patterns.
- **Refresh jobs:** On success, set `last_successful_*_refresh_at`.
