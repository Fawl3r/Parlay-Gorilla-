## Parlay Gorilla — Simple X Social Bot (v2)

This is a minimal “one post per run” bot that follows the FINAL SPEC:

- 4 post types only: Edge Explainer, Trap Alert, Example 2–3 leg parlay structure (hypothetical), Parlay math/bankroll
- Plain English, disciplined, credible
- No hype words, no hashtags, max 1 emoji
- Uses production analysis feed for matchup context
- No dashboards, no queues

### Setup

1) Copy env template:

`social_bot/.env.example` → `.env` (repo root)

2) Fill in:

- `OPENAI_API_KEY`
- X credentials (either `X_BEARER_TOKEN` or OAuth1 keys)

### Run once

From repo root:

```bash
python -m social_bot.bot --print-only
```

Then (after you trust outputs):

```bash
python -m social_bot.bot
```

### Scheduling (peak windows + jitter)

Run the built-in scheduler (continuous loop):

```bash
python -m social_bot.bot --run-schedule
```

Config is driven by env vars:
- `POSTING_WINDOWS_WEEKDAY`, `POSTING_WINDOWS_WEEKEND`
- `SCHEDULE_JITTER_MINUTES`
- `NO_EARLY_POST_BEFORE`
- `WEEKDAY_MAX_POSTS_PER_DAY`, `WEEKEND_MAX_POSTS_PER_DAY`

The bot stores state in `social_bot/memory.json`.

### Manual images (no AI images)

Put your curated images in:

`social_bot/images/{football,basketball,baseball,soccer,hockey,education,analysis,general}`

Rules:
- Avoids reusing the last 8 images
- Uses topic/sport folder priority
- Attaches images automatically for analysis/parlay posts when available
- If upload fails, posts text-only (no crash)


