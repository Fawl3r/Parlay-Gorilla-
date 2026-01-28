# API-Sports: Local Checkout & Testing

How to run and verify the API-Sports integration locally (quota-safe, DB-first).

## 1. Prerequisites

- Backend deps installed: `pip install -r requirements.txt`
- **PostgreSQL** running (Docker or local), or SQLite for quick run (see below)
- Optional: **Redis** (for quota/rate limit; if not set, quota uses DB table `api_quota_usage`)
- Optional: **API-Sports key** (leave blank to skip live API calls; quota/admin still work)

## 2. Environment

In `backend/.env` (or export):

```bash
# Required for app
DATABASE_URL=postgresql://user:pass@localhost:5432/parlaygorilla
# Or SQLite: USE_SQLITE=true and DATABASE_URL=sqlite+aiosqlite:///parlay_gorilla.db

# Optional: Redis (quota + rate limit). If empty, quota uses DB.
REDIS_URL=redis://localhost:6379

# Optional: API-Sports (leave blank to disable live calls)
API_SPORTS_API_KEY=your_key_here
```

Other optional vars (defaults in `config.py`):

- `APISPORTS_DAILY_QUOTA=100`
- `APISPORTS_TTL_FIXTURES_SECONDS=900`
- `APISPORTS_BUDGET_RESERVE=5`

## 3. Run migrations

```bash
cd backend
alembic upgrade head
```

This creates tables: `apisports_fixtures`, `apisports_results`, `apisports_team_stats`, `apisports_standings`, `apisports_injuries`, `apisports_features`, `api_quota_usage`.

## 4. Start the backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

If Redis is not set and you're not in production, the **scheduler may not start** (by design). You can still hit the admin endpoints and trigger refresh manually.

## 5. Check quota (admin only)

You need an admin user and a valid JWT.

**Get quota status:**

```bash
curl -s -X GET "http://localhost:8000/api/admin/apisports/quota" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT"
```

Example response:

```json
{
  "used_today": 0,
  "remaining": 100,
  "circuit_open": false,
  "daily_limit": 100
}
```

**Trigger refresh (uses quota):**

```bash
curl -s -X POST "http://localhost:8000/api/admin/apisports/refresh" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT"
```

Example response:

```json
{
  "used": 2,
  "remaining": 98,
  "refreshed": {
    "fixtures": 10,
    "team_stats": 0,
    "standings": 1
  }
}
```

If `API_SPORTS_API_KEY` is not set, refresh will return `used: 0` and skip live calls.

## 6. Run tests

From `backend`:

```bash
pytest tests/test_apisports_quota_and_confidence.py -v
```

Tests cover:

- `_today_chicago()` format
- Confidence engine clamp and blend
- QuotaManager `can_spend` / `remaining_async` with Redis disabled (mocked DB)

Full test suite (all tests) uses the test SQLite DB from `conftest.py`; API-Sports models are SQLite-compatible (JSON variant).

## 7. Verify you’re not exceeding 100/day

- Call **GET /api/admin/apisports/quota** and check `used_today` and `remaining`.
- Check logs for `[SCHEDULER] API-Sports refresh: used=X remaining=Y` (when scheduler runs).
- If Redis is used, the daily counter resets at midnight America/Chicago.

## 8. Optional: Run scheduler locally

The scheduler only starts when:

- `REDIS_URL` is set (leader election), and
- In production, or you temporarily allow it in dev.

To run refresh on a timer locally without changing code, you can:

- Call **POST /api/admin/apisports/refresh** on a schedule (e.g. cron or a small script), or
- Set `REDIS_URL` and ensure the app is in an environment where the scheduler starts, then wait for the 60-minute job.

## Quick test without API key

1. `alembic upgrade head`
2. Start backend: `uvicorn app.main:app --reload --port 8000`
3. Log in as admin, get JWT.
4. `GET /api/admin/apisports/quota` → should show `remaining: 100`, `used_today: 0`.
5. `POST /api/admin/apisports/refresh` → should return `used: 0`, no live calls.

This confirms routes and quota logic without spending API-Sports quota.
