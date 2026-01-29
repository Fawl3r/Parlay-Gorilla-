# Telegram Alerts

Operator alerts for parlay generation failures, odds fetch failures, schedule repair failures, and API-Sports quota blocks (when critical) are sent to Telegram when configured.

## Configuration

Set these in your environment or `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_ALERTS_ENABLED` | Set to `true` to enable Telegram alerts | `false` |
| `TELEGRAM_BOT_TOKEN` | Bot token from [@BotFather](https://t.me/BotFather) | — |
| `TELEGRAM_CHAT_ID` | Chat or group ID to receive alerts | — |

If any of these are missing or `TELEGRAM_ALERTS_ENABLED` is `false`, the notifier is a no-op (no messages sent).

## Getting a Bot Token and Chat ID

1. **Bot token**: Message [@BotFather](https://t.me/BotFather) on Telegram, send `/newbot`, follow the prompts. Copy the token.
2. **Chat ID**: Start a chat with your bot or add it to a group. Send a message. Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` and find `"chat":{"id":...}` — that number is your chat ID.

## Behavior

- **Deduplication**: Same event + payload is not sent again within 10 minutes (Redis when available, else in-memory).
- **Rate limit**: At most 1 message per 10 seconds globally.
- **Spike suppression**: Per (event, sport), if the same alert would be sent 3+ times in 10 minutes, later sends are suppressed.
- **Payload sanitizer**: Large fields and long lists (e.g. candidates) are trimmed; stack traces are limited to 25 lines.

## Events that trigger alerts

| Event | When |
|-------|------|
| `api.unhandled_exception` | Unhandled exception in FastAPI (stack trimmed to 25 lines). |
| `parlay.generate.fail.not_enough_games` | Single-sport or mixed parlay build failed due to no candidate legs. |
| `odds.fetch.fail` | Odds API rate limit, invalid response, or all fallbacks failed. |
| `schedule.repair.fail` | Schedule repair (placeholder team names) failed (commit or exception). |
| `provider.quota.state` | API-Sports quota blocked a **critical** action (e.g. schedule repair during postseason). |

## Optional: Redis for deduplication

When `REDIS_URL` is set, deduplication uses Redis so multiple app instances share the same 10-minute dedupe window. Without Redis, deduplication is per-process (in-memory).
