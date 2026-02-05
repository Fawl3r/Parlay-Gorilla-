# Observability & Telegram Alerts

Parlay Gorilla uses **Telegram** for operator alerts at **$0 cost**. Alerts are throttled and deduplicated to prevent spam. Logs remain structured and searchable.

---

## Alert Types (Telegram)

| Alert event | Severity | When |
|-------------|----------|------|
| **settlement.failure** | error | Settlement worker throws during _process_settlements |
| **settlement.circuit_breaker_open** | critical | Circuit breaker opens after 5 consecutive settlement errors |
| **api.rate_limit_hit** | warning | A client hits our rate limit (429) |
| **database.connection_error** | critical | Health DB check fails (SELECT 1) |
| **api.unhandled_exception** | error | Unhandled exception in API (global handler) |
| **parlay.generate.fail.not_enough_games** | warning | Parlay build fails due to empty/low game pool (existing) |

Each payload includes:
- **environment** (development / staging / production)
- **error_type** or **exception_type**
- **error_message** or **message** (truncated)
- **stack_trace** (trimmed to 25 lines) for unhandled exceptions
- **path** for rate limit; **request_id** for API errors; **game_id**/parlay id when relevant

---

## How It Works

1. **TelegramNotifier** (`app.services.alerting.telegram_notifier.py`)
   - Sends messages via `https://api.telegram.org/bot{token}/sendMessage`.
   - **Dedupe:** same event + payload hash within 10 min → skip send (Redis or in-memory).
   - **Rate limit:** 1 message per 10 seconds.
   - No-op if `TELEGRAM_ALERTS_ENABLED=false` or missing `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`.

2. **AlertingService** (`app.services.alerting.alerting_service.py`)
   - **Spike detection:** same (event, sport) ≥ 3 times in 10 min → skip send.
   - Sanitizes payload (trim long strings, sample lists).
   - Calls `TelegramNotifier.send_event(event, severity, payload)`.

3. **Config (backend .env and Render)**
   - `TELEGRAM_ALERTS_ENABLED=true`
   - `TELEGRAM_BOT_TOKEN=<bot token>`
   - `TELEGRAM_CHAT_ID=<chat id>`

---

## Enabling Alerts

1. Create a Telegram bot via [@BotFather](https://t.me/BotFather); get the token.
2. Get your chat ID (e.g. send a message to the bot, then call `getUpdates`).
3. Set in backend `.env` and Render env vars:
   - `TELEGRAM_ALERTS_ENABLED=true`
   - `TELEGRAM_BOT_TOKEN=...`
   - `TELEGRAM_CHAT_ID=...`

Logs stay structured (existing logging); Telegram is for **operator visibility** only.

---

## Testing Telegram Alerts

**Script (full pipeline):** From backend directory, run:

```bash
cd backend
python scripts/test_telegram_alerts.py
```

This checks config, sends a **plain test message**, then (after 11s) sends an **event** via AlertingService. You should see two messages in your Telegram chat. If token or chat_id is missing, the script exits with clear instructions.

**Pytest (live send when configured):** With `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` set in env:

```bash
cd backend
pytest tests/test_alerting_telegram.py::test_telegram_alerts_live_send -v
```

Without those env vars, the live test is skipped. All other alerting tests (sanitizer, spike, disabled no-op) run in CI.
