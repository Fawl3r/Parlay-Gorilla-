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

1. **Bot token**: Message [@BotFather](https://t.me/BotFather) on Telegram, send `/newbot`, follow the prompts. Copy the token. Do not share it or put it in public URLs.
2. **Chat ID** (getUpdates returns empty until the bot gets a message):
   - Open Telegram and **start a chat with your bot** (search for your bot’s username and tap **Start**), or add the bot to a group.
   - **Send any message** to the bot (e.g. `/start` or “hello”).
   - In your browser, open:  
     `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`  
     (replace `<YOUR_BOT_TOKEN>` with your token; use a private/incognito window if possible so the token is not in history.)
   - In the JSON, look at `result[0].message.chat.id` (for a direct chat) or `result[0].message.chat.id` for a group. That number is your **Chat ID** (e.g. `123456789` or `-1001234567890` for groups).
   - If you still see `"result": []`, send another message to the bot and reload the getUpdates page.

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
| `analysis.teams.placeholder` | A **game analysis detail** page was served with placeholder team names (TBD, AFC, etc.). |
| `analysis.list.teams.placeholder` | The **analysis list** (upcoming) was served and one or more games have placeholder team names. |

## Optional: Redis for deduplication

When `REDIS_URL` is set, deduplication uses Redis so multiple app instances share the same 10-minute dedupe window. Without Redis, deduplication is per-process (in-memory).
