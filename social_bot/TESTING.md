# Testing the Social Writing Bot

## Prerequisites

1. **Install dependencies** (from `social_bot/` directory):
```bash
pip install -r requirements.txt
```

2. **Environment setup** (optional, dry-run works without it):
```bash
cp .env.example .env
# Edit .env if you want to test with real X API (not required for dry-run)
```

## 1. Unit Tests (Recommended First Step)

Run the comprehensive test suite from the **repo root**:

```bash
# From repo root (C:\F3 Apps\F3 Parlay Gorilla)
pytest social_bot/tests -q
```

**Expected output:**
```
...........                                                              [100%]
11 passed in 0.46s
```

**What's tested:**
- ✅ Guardian: banned phrase rejection, emoji/hashtag limits, length rules
- ✅ Dedupe: similarity checks, template/pillar cooldowns
- ✅ Writer: deterministic generation with seeded RNG
- ✅ Scheduler: tier selection, pillar repeat avoidance
- ✅ Publisher: backoff behavior (mocked), dry-run mode
- ✅ Site Feed: caching, slug reuse cooldown (mocked HTTP)

## 2. CLI Command Testing (Dry-Run Mode)

All commands work in **dry-run mode by default** (no X API credentials needed).

### Note on Images

If `config/settings.json -> images.enabled=true`, generation will call OpenAI to create backgrounds and will require:

- `OPENAI_API_KEY`

To test the bot without OpenAI calls, set `IMAGES_ENABLED=false` in your `.env` (see `.env.example`).

### Generate Posts into Queue

```bash
cd social_bot
python main.py generate --count 10
```

**What happens:**
- Generates 10 posts using pillars + templates
- Runs through Guardian (compliance checks)
- Runs through Dedupe (similarity/cooldown checks)
- Writes to `queue/outbox.json`

**Check results:**
```bash
# View generated posts
cat queue/outbox.json | python -m json.tool
```

**Expected:** Array of queue items with `id`, `type`, `text`, `pillar_id`, `template_id`, `score`, `recommended_tier`.

If images are enabled, eligible items will also include:

- `image_mode`
- `image_path`

### Post a Custom One-Off

```bash
python main.py post-now --text "Keep your unit size boring. If the stake changes because of emotion, the edge is already gone."
```

**What happens:**
- Creates a manual queue item
- Runs Guardian + Dedupe checks
- "Posts" in dry-run (logs to console + `queue/posted.json`)
- Logs: `Posted (dry_run=True) id=... tweet_ids=['dryrun-...']`

**Check results:**
```bash
# View posted record
cat queue/posted.json | python -m json.tool
```

**Expected:** New entry in `posted.json` with `tweet_ids` starting with `"dryrun-"`.

### Generate and Post a Thread

```bash
python main.py thread --topic "bankroll management" --length 5
```

**What happens:**
- Generates a 5-tweet thread on the topic
- Runs Guardian + Dedupe
- "Posts" thread in dry-run (all tweets logged)
- Logs: `Posted (dry_run=True) id=... tweet_ids=['dryrun-...', 'dryrun-...', ...]`

**Check results:**
```bash
# View thread in posted.json
cat queue/posted.json | python -m json.tool | Select-String -Pattern "thread" -Context 5
```

### Run Scheduler (Blocking)

**Note:** The scheduler runs continuously and posts at configured times. For testing, you may want to modify `config/settings.json` to set a near-future time.

```bash
python main.py run-scheduler
```

**What happens:**
- Starts APScheduler
- Waits for next scheduled slot (weekday/weekend schedule from `config/settings.json`)
- Picks a post from `queue/outbox.json` matching the slot's tier
- "Posts" in dry-run
- Moves item from `outbox.json` to `posted.json`
- Repeats for each scheduled slot

**To stop:** Press `Ctrl+C`

**Check logs:**
```bash
# View bot.log
cat logs/bot.log

# View audit trail (JSONL)
cat logs/audit.jsonl
```

## 3. Testing with Backend Analysis Feed

If your FastAPI backend is running, you can test analysis excerpt injection:

### Start Backend (if not running)

```bash
# From repo root
cd backend
# Start your FastAPI server (adjust command as needed)
uvicorn app.main:app --reload --port 8000
```

### Test Analysis Feed Endpoint

```bash
# Test the feed endpoint directly
curl http://localhost:8000/api/analysis-feed?limit=5
```

**Expected:** JSON array with analysis items containing `slug`, `angle`, `key_points`, `risk_note`, `cta_url`.

### Test Redirect Endpoint

```bash
# Test redirect with variant
curl -I "http://localhost:8000/r/nfl/bears-vs-packers-week-1-2025?v=a"
```

**Expected:** `302 Found` redirect to frontend analysis page with UTM parameters.

### Generate Posts with Analysis Injection

```bash
cd social_bot
python main.py generate --count 5
```

**What happens:**
- Writer may inject analysis excerpts (if feed is available and within caps)
- Check `cache/analysis_feed.json` for cached feed data
- Check `queue/outbox.json` for items with `is_analysis: true` and `analysis_slug`

**Check cache:**
```bash
cat cache/analysis_feed.json | python -m json.tool
```

**Expected:** `fetched_at`, `expires_at`, `items` array, `used_slugs` tracking.

## 4. Manual Testing Checklist

### ✅ Guardian Compliance

Test banned phrase rejection:
```bash
python main.py post-now --text "This is a banned phrase test"
```

If the text contains banned phrases (see `content/banned_phrases.json`), it should be rejected or sanitized.

### ✅ Dedupe Similarity

Generate similar posts:
```bash
python main.py generate --count 20
```

Check that very similar posts are filtered out (see `config/settings.json` → `dedupe.similarity_threshold`).

### ✅ Tier Routing

Generate posts and check `recommended_tier`:
```bash
python main.py generate --count 10
cat queue/outbox.json | python -m json.tool | Select-String "recommended_tier"
```

Posts should have `low`, `mid`, or `high` tiers based on scoring.

### ✅ Scheduler Tier Selection

1. Generate posts with mixed tiers:
```bash
python main.py generate --count 20
```

2. Check `config/settings.json` for current slot tier (e.g., `weekday_schedule[0].tier`)

3. Run scheduler and verify it picks posts matching the slot tier:
```bash
python main.py run-scheduler
```

### ✅ Daily/Weekly Caps

Check `config/settings.json`:
- `scheduler.max_posts_per_day`
- `scheduler.max_threads_per_week`

Generate and post enough items to hit caps, then verify scheduler stops posting.


## 5. Integration Testing with Real X API (Optional)

**⚠️ Only do this when ready to post to X!**

1. **Get X API credentials:**
   - Create a project in [X Developer Portal](https://developer.twitter.com/)
   - Generate Bearer Token (or OAuth 2.0 credentials)

2. **Update `.env`:**
```bash
BOT_DRY_RUN=false
X_BEARER_TOKEN=your_bearer_token_here
```

3. **Test with a single post first:**
```bash
python main.py post-now --text "Test post from Parlay Gorilla bot"
```

4. **Check X account** to verify the post appeared.

5. **Run scheduler** (if confident):
```bash
python main.py run-scheduler
```

## 6. Troubleshooting

### Import Errors

```bash
# Ensure you're in social_bot/ directory or PYTHONPATH is set
cd social_bot
python main.py generate --count 1
```

### Queue Files Not Found

The bot creates `queue/outbox.json` and `queue/posted.json` automatically. If missing, ensure the `queue/` directory exists:
```bash
mkdir -p queue
```

### Backend Feed Not Available

If `ANALYSIS_FEED_URL` is unreachable, the bot will skip analysis injection gracefully. Check:
- Backend is running on the configured port
- `/api/analysis-feed` endpoint is accessible
- Network/firewall allows connection

### Scheduler Not Posting

Check:
- Current time matches a scheduled slot in `config/settings.json`
- `queue/outbox.json` has items matching the slot's tier
- Daily/weekly caps haven't been reached
- Logs in `logs/bot.log` for errors

## 7. Test Data Cleanup

To reset test state:
```bash
# Clear queue
echo "[]" > queue/outbox.json
echo "[]" > queue/posted.json

# Clear cache
echo '{"fetched_at": null, "expires_at": null, "items": [], "used_slugs": {}}' > cache/analysis_feed.json

# Clear logs (optional)
> logs/bot.log
> logs/audit.jsonl
```

## Quick Test Summary

**Fastest way to verify everything works:**

```bash
# 1. Run unit tests
pytest social_bot/tests -q

# 2. Generate some posts
cd social_bot
python main.py generate --count 5

# 3. Post one manually
python main.py post-now --text "Test post"

# 4. Check results
cat queue/outbox.json | python -m json.tool
cat queue/posted.json | python -m json.tool
cat logs/bot.log
```

All should complete without errors! 🎉

