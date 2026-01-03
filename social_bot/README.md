## Parlay Gorilla Social Writing Bot (X Free Tier)

Self-contained, **write-only**, **queue-first**, schedule-driven social posting engine for X (Twitter API v2).

### What this bot does

- **Generates** compliant single posts or threads into `queue/outbox.json`
- **Schedules** posting with APScheduler using local-time weekday/weekend slots
- **Publishes** via X write endpoint (`POST /2/tweets`) with **dry-run enabled by default**
- **Optionally injects real analysis excerpts** from your FastAPI backend via `GET /api/analysis-feed`
- **Tracks** what was posted in `queue/posted.json` (append-only)

### Free Tier philosophy (minimal reads, write-only)

- Designed to be **write-heavy** and **read-light**
- Analysis feed reads are cached to keep the bot under ~**100 reads/month** by default
- Posting is **dry-run by default** until credentials are provided

### Quickstart

From `social_bot/`:

- Generate queue items:

```bash
python main.py generate --count 50
```

- Run scheduler (blocking):

```bash
python main.py run-scheduler
```

- Post a custom one-off (guardian + dedupe, then dry-run publish):

```bash
python main.py post-now --text "custom text"
```

- Generate and post a thread immediately (3–6 tweets):

```bash
python main.py thread --topic "topic" --length 5
```

### Configuration

- **Primary config**: `config/settings.json`
- **Content library**: `content/*.json`
- **Queue files**: `queue/outbox.json`, `queue/posted.json`
- **Analysis cache**: `cache/analysis_feed.json`
- **Logs**: `logs/bot.log`, `logs/audit.jsonl`

Environment overrides are supported (see `.env.example`).

### Scheduling + tier routing

- Writer assigns each queue item a `score` and `recommended_tier`.
- Scheduler posts by configured slot tier and falls back to nearby tiers when empty.
- Scheduler avoids repeating the same pillar twice in a row when possible.
- Safety caps:
  - `max_posts_per_day`
  - `max_threads_per_week`
  - disclaimer enforced **once/day** via `posted.json` tracking

### Analysis excerpt injection

- Backend must expose:
  - `GET /api/analysis-feed`
  - `GET /r/{slug}?v=a|b` (redirect with UTMs)
- Bot caches feed responses (`cache/analysis_feed.json`) with configurable TTL (default 12h).
- Bot enforces a **48h reuse cooldown** per analysis `slug`.
- Bot uses A/B variants via `v=a|b` and tracks via `utm_content=variant_a|variant_b`.

### Tests

Run bot tests from repo root:

```bash
pytest social_bot/tests -q
```


