# API-Sports: Production Deployment Guide

Complete guide for deploying API-Sports integration to Render production.

## ✅ Pre-Deployment Checklist

- [ ] Code pushed to main branch (includes migration `042_add_apisports_tables`)
- [ ] API-Sports API key obtained from https://api-sports.io
- [ ] Render dashboard access ready

## Step 1: Set Environment Variables in Render

1. **Go to Render Dashboard:**
   - https://dashboard.render.com
   - Navigate to: **Services** → `parlay-gorilla-backend`

2. **Add API-Sports Environment Variables:**
   - Click **Environment** tab
   - Click **Add Environment Variable**

   **Required:**
   ```
   API_SPORTS_API_KEY = your_api_key_here
   ```

   **Optional (defaults are fine for most cases):**
   ```
   APISPORTS_BASE_URL = https://v3.football.api-sports.io
   # Per-sport base URL overrides (optional). NFL/NBA/NHL/MLB use v1 hosts by default.
   # APISPORTS_BASE_URL_NFL = https://v1.american-football.api-sports.io
   # APISPORTS_BASE_URL_NBA = https://v1.basketball.api-sports.io
   # APISPORTS_BASE_URL_NHL = https://v1.hockey.api-sports.io
   # APISPORTS_BASE_URL_MLB = https://v1.baseball.api-sports.io
   APISPORTS_DAILY_QUOTA = 100
   APISPORTS_SOFT_RPS_INTERVAL_SECONDS = 15
   APISPORTS_BURST = 2
   APISPORTS_CIRCUIT_BREAKER_FAILURES = 5
   APISPORTS_CIRCUIT_BREAKER_COOLDOWN_SECONDS = 1800
   APISPORTS_TTL_FIXTURES_SECONDS = 900
   APISPORTS_TTL_TEAM_STATS_SECONDS = 86400
   APISPORTS_TTL_STANDINGS_SECONDS = 86400
   APISPORTS_TTL_INJURIES_SECONDS = 43200
   APISPORTS_BUDGET_FIXTURES = 60
   APISPORTS_BUDGET_TEAM_STATS = 25
   APISPORTS_BUDGET_STANDINGS = 10
   APISPORTS_BUDGET_RESERVE = 5
   ```

3. **Save Changes** (Render will auto-deploy if enabled)

## Step 2: Run Migration

The `start.sh` script automatically runs migrations on deploy, but you can also run manually:

### Option A: Automatic (on next deploy)
- Just push your code or trigger a manual deploy
- Check logs for: `[STARTUP] Running Alembic migrations...`
- Should see: `Running upgrade 041_create_system_heartbeats -> 042_add_apisports_tables`

### Option B: Manual via Render Shell (if needed)
1. Go to: **Services** → `parlay-gorilla-backend` → **Shell** tab
2. Run:
   ```bash
   alembic upgrade head
   ```
3. Verify:
   ```bash
   alembic current
   ```
   Should show: `042_add_apisports_tables (head)`

## Step 3: Verify Deployment

### 3.1 Check Migration Applied

In Render Shell:
```bash
alembic current
```

Should show: `042_add_apisports_tables (head)`

### 3.2 Check Tables Exist

In Render Shell:
```bash
psql $DATABASE_URL -c "\dt apisports*"
```

Should list:
- `apisports_fixtures`
- `apisports_results`
- `apisports_team_stats`
- `apisports_standings`
- `apisports_injuries`
- `apisports_features`
- `api_quota_usage`

### 3.3 Check Quota Status (Admin Endpoint)

**Get admin JWT first** (via login endpoint), then:

```bash
curl -X GET "https://api.parlaygorilla.com/api/admin/apisports/quota" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT"
```

Expected response:
```json
{
  "used_today": 0,
  "remaining": 100,
  "circuit_open": false,
  "daily_limit": 100
}
```

### 3.4 Check Scheduler is Running

In Render **Logs** tab, look for:
```
[STARTUP] Background scheduler started
```

And after ~60 minutes, you should see:
```
[SCHEDULER] API-Sports refresh: used=X remaining=Y refreshed={...}
```

### 3.5 Test Manual Refresh (Admin Only)

```bash
curl -X POST "https://api.parlaygorilla.com/api/admin/apisports/refresh" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT"
```

Expected response:
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

## Step 4: Monitor Quota Usage

### Daily Quota Check

**Via Admin Endpoint:**
```bash
curl -X GET "https://api.parlaygorilla.com/api/admin/apisports/quota" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT"
```

**Via Render Logs:**
Look for: `[SCHEDULER] API-Sports refresh: used=X remaining=Y`

### Quota Reset

Quota resets at **midnight America/Chicago** (configurable via `_today_chicago()` in `quota_manager.py`).

If using Redis: counter resets automatically (key is date-based).
If using DB fallback: new row created per day.

## Step 5: Verify Scheduler Job

The API-Sports refresh job runs **every 60 minutes** when:
- `ENABLE_BACKGROUND_JOBS=true` (default in render.yaml)
- Redis is configured (for leader election)
- Scheduler starts successfully

**Check logs for:**
```
[SCHEDULER] API-Sports refresh: used=2 remaining=98 refreshed={'fixtures': 10, 'standings': 1}
```

If you don't see this after 60 minutes:
1. Check `ENABLE_BACKGROUND_JOBS` is `true`
2. Check Redis is reachable (scheduler needs it for leader election)
3. Check logs for scheduler errors

## Troubleshooting

### Migration Not Applied

**Symptoms:** Admin quota endpoint returns 500, or tables don't exist.

**Fix:**
1. Go to Render Shell
2. Run: `alembic upgrade head`
3. Verify: `alembic current` shows `042_add_apisports_tables`

### Quota Not Tracking

**Symptoms:** Quota always shows 100 remaining even after requests.

**Check:**
1. Redis is reachable (quota prefers Redis)
2. If Redis fails, check DB table exists: `\dt api_quota_usage`
3. Check logs for: `QuotaManager Redis spend failed, falling back to DB`

### Scheduler Not Running

**Symptoms:** No refresh logs after 60 minutes.

**Check:**
1. `ENABLE_BACKGROUND_JOBS=true` in env vars
2. Redis is configured (required for leader election)
3. Logs show: `[SCHEDULER] Background scheduler started`
4. No errors in scheduler startup logs

### API Calls Failing

**Symptoms:** Refresh returns `used: 0` or errors.

**Check:**
1. `API_SPORTS_API_KEY` is set correctly
2. API key is valid (test at https://api-sports.io)
3. Quota not exhausted: `GET /api/admin/apisports/quota`
4. Circuit breaker not open: `circuit_open: false`
5. Check logs for API errors (no key leakage in logs)

## Production Safety Features

✅ **Quota Protection:**
- Hard cap: 100/day (enforced)
- Reserve: 5 calls preserved
- Budget allocation: 60 fixtures, 25 team stats, 10 standings, 5 reserve

✅ **Circuit Breaker:**
- Opens after 5 consecutive failures
- Cooldown: 30 minutes
- Auto-closes on next success

✅ **DB-First:**
- User endpoints never call API-Sports
- All reads from DB cache
- Background job only makes API calls

✅ **Redis Fallback:**
- If Redis unavailable, quota uses DB table
- Rate limiter uses in-process fallback
- No single point of failure

## Monitoring Recommendations

1. **Set up alerts** for:
   - Quota < 10 remaining
   - Circuit breaker opens
   - Scheduler errors

2. **Daily check:**
   - `GET /api/admin/apisports/quota` to verify usage
   - Review scheduler logs for refresh success

3. **Weekly review:**
   - Check quota usage patterns
   - Adjust budget allocation if needed (via env vars)

## Rollback Plan

If API-Sports causes issues:

1. **Disable API calls:**
   - Remove or blank `API_SPORTS_API_KEY` in Render env vars
   - System will skip all API calls but still serve cached data

2. **Disable scheduler job:**
   - Set `ENABLE_BACKGROUND_JOBS=false`
   - Or comment out the job in `scheduler.py`

3. **Keep DB tables:**
   - Tables are safe to keep (they're just cache)
   - No user-facing endpoints depend on them
   - Can delete later if needed: `DROP TABLE apisports_*;`

## Next Steps After Deployment

1. ✅ Verify migration applied
2. ✅ Set `API_SPORTS_API_KEY` in Render
3. ✅ Wait 60 minutes for first scheduler run
4. ✅ Check quota endpoint shows usage
5. ✅ Monitor logs for refresh success
6. ✅ Verify data in `apisports_fixtures` table (via Render PostgreSQL dashboard)

---

**Questions?** Check logs first, then admin quota endpoint for status.
