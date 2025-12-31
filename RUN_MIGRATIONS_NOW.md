# 🚀 Quick Fix: Run Migrations Now

Since the Render CLI installation is complex on Windows, here are **3 quick ways** to run migrations:

## Option 1: Render Dashboard Shell (FASTEST - 2 minutes)

1. Go to: https://dashboard.render.com
2. Click: **Services** → `parlay-gorilla-backend`
3. Click: **Shell** tab (or "Open Shell" button)
4. Run:
   ```bash
   alembic upgrade head
   ```
5. Wait for: `INFO  [alembic.runtime.migration] Running upgrade ... -> 022_add_premium_usage_periods`
6. Test: `python scripts/validate_production_migrations.py`

## Option 2: Trigger Deployment (AUTOMATIC - 5 minutes)

The new `start.sh` script will run migrations automatically on deploy:

1. Go to: https://dashboard.render.com
2. Click: **Services** → `parlay-gorilla-backend`
3. Click: **Manual Deploy** → **Deploy latest commit**
4. Monitor logs for: `[STARTUP] Running Alembic migrations...`
5. Wait for deployment to complete
6. Test: `python scripts/validate_production_migrations.py`

## Option 3: Render API (If you have API key)

If you have a Render API key:

```powershell
# Set your API key
$env:RENDER_API_KEY='your-api-key-here'

# Run the migration script
cd backend
python scripts/run_migrations_via_render_api.py
```

**To get API key:**
1. Go to https://dashboard.render.com
2. Profile → Account Settings → API Keys
3. Create new key

## Verification

After migrations run, verify:

```bash
cd backend
python scripts/validate_production_migrations.py
```

Should show:
- ✅ Health Check: PASS
- ✅ Login Endpoint: PASS (401, not 500)
- ✅ Register Endpoint: PASS (201/400/422, not 500)

## Current Status

- ❌ Migrations NOT applied (confirmed via validation script)
- ✅ Fix code pushed (start.sh will auto-run migrations on future deploys)
- ⏳ Waiting for manual migration or deployment

