# 🚨 Production Migration Fix - URGENT

## Current Status

**Validation Results:**
- ❌ Register endpoint: `column users.premium_custom_builder_used does not exist`
- ❌ Login endpoint: Returning 500 (likely same schema issue)
- ✅ Health endpoint: Working (service is running)

**Conclusion:** Migrations have NOT been applied to production database.

## Immediate Fix Options

### Option 1: Manual Migration via Render Shell (FASTEST)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Navigate to: **Services** → `parlay-gorilla-backend`
3. Click **Shell** tab (or use "Open Shell" button)
4. Run:
   ```bash
   alembic upgrade head
   ```
5. Wait for completion (should see "Running upgrade..." messages)
6. Verify: Check that it says "INFO  [alembic.runtime.migration] Running upgrade ... -> 022_add_premium_usage_periods"
7. Test: Run the validation script again:
   ```bash
   python scripts/validate_production_migrations.py
   ```

**Expected output:**
```
Running upgrade 021_add_saved_parlay_results -> 022_add_premium_usage_periods, Add premium rolling-period usage counters to users
```

### Option 2: Redeploy with Fixed startCommand

I've updated `render.yaml` to use a shell script instead of `&&` chaining (which may not work on Render).

**Files changed:**
- `render.yaml`: Changed `startCommand` to `bash start.sh`
- `backend/start.sh`: New startup script that runs migrations first

**Steps:**
1. Commit and push the changes (already done)
2. Go to Render Dashboard → `parlay-gorilla-backend`
3. Click **Manual Deploy** → **Deploy latest commit**
4. Monitor logs for: `[STARTUP] Running Alembic migrations...`
5. Wait for deployment to complete
6. Test endpoints

### Option 3: Verify Current Deployment

Check if the new code is even deployed:

1. Go to Render Dashboard → `parlay-gorilla-backend` → **Logs**
2. Look for:
   - `[STARTUP] Running Alembic migrations...` (means new code is running)
   - OR any migration-related output
3. If you see migration attempts but they fail, check error messages

## Verification

After applying migrations, run:

```bash
cd backend
python scripts/validate_production_migrations.py
```

**Expected results:**
- ✅ Health Check: PASS
- ✅ Login Endpoint: PASS (should return 401, not 500)
- ✅ Register Endpoint: PASS (should return 201/400/422, not 500)

## Why This Happened

The original `render.yaml` used:
```yaml
startCommand: alembic upgrade head && uvicorn app.main:app ...
```

Render may not support `&&` chaining in `startCommand`, or the command failed silently. The new approach uses a shell script that:
1. Runs migrations explicitly
2. Uses `set -e` to fail fast if migrations fail
3. Only starts uvicorn if migrations succeed

## Database Schema Check (Optional)

If you have direct database access, verify the columns exist:

```sql
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'users' 
  AND column_name IN (
    'premium_custom_builder_used',
    'premium_custom_builder_period_start',
    'premium_inscriptions_used',
    'premium_inscriptions_period_start'
  );
```

Should return 4 rows.

Also check Alembic version:
```sql
SELECT version_num FROM alembic_version;
```

Should show: `022_add_premium_usage_periods`

