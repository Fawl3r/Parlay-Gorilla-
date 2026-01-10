# Social Bot Commands

## Basic Usage

### Single Post
Run the social bot to generate and post a single post to X:

```bash
python -m social_bot.bot
```

### Scheduled Mode (Live/Production)
Run the bot with automatic scheduling - it will post at configured times throughout the day:

```bash
python -m social_bot.bot --run-schedule
```

**Scheduled Mode Details:**
- Runs continuously in a loop
- Posts at configured times (with jitter to avoid patterns)
- Respects daily posting limits
- Automatically handles rate limits with backoff
- Never posts before the configured early-post time
- Skips missed slots (no catch-up posting)

**Default Schedule (configurable in `.env`):**
- **Weekdays**: 08:10, 11:40, 14:10, 17:10 (with ±8 min jitter)
- **Weekends**: 09:05, 12:35, 18:15 (with ±8 min jitter)
- **Daily Limits**: 4 posts/weekday, 3 posts/weekend
- **Early Post Limit**: Never posts before 06:30 AM local time

## Optional Flags

### `--print-only`
Generate and print the post without posting to X (useful for testing):

```bash
python -m social_bot.bot --print-only
```

### `--force-type <type>`
Force a specific post type:

```bash
# Edge Explainer
python -m social_bot.bot --force-type edge_explainer

# Trap Alert
python -m social_bot.bot --force-type trap_alert

# Parlay Math
python -m social_bot.bot --force-type parlay_math

# Example Parlay
python -m social_bot.bot --force-type example_parlay
```

### `--seed <number>`
Use a specific seed for reproducible output (useful for testing):

```bash
python -m social_bot.bot --seed 12345
```

## Configuration

**Important:** Make sure `BOT_DRY_RUN=false` in your `.env` file if you want the bot to actually post to X.

- If `BOT_DRY_RUN=true`: Bot will only generate and print the post without posting
- If `BOT_DRY_RUN=false`: Bot will generate and post to X

## Examples

### Test a post without posting:
```bash
python -m social_bot.bot --print-only
```

### Post an edge explainer:
```bash
python -m social_bot.bot --force-type edge_explainer
```

### Post with a specific seed (for debugging):
```bash
python -m social_bot.bot --seed 42
```

