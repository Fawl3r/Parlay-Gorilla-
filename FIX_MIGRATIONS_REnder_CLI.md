# Fix Migrations Using Render CLI

## Issue
The Render CLI binary download didn't work on Windows. Here are **working alternatives**:

## ✅ Option 1: Render Dashboard Shell (RECOMMENDED - 2 minutes)

**This is the fastest and most reliable method:**

1. **Open Render Dashboard:**
   - Go to: https://dashboard.render.com
   - Login if needed

2. **Navigate to Backend Service:**
   - Click: **Services** → `parlay-gorilla-backend`

3. **Open Shell:**
   - Click: **Shell** tab (or "Open Shell" button)
   - This opens an interactive terminal

4. **Run Migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Verify Success:**
   - Look for: `INFO  [alembic.runtime.migration] Running upgrade ... -> 022_add_premium_usage_periods`
   - Should see: `INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.`

6. **Test Endpoints:**
   ```bash
   cd backend
   python scripts/validate_production_migrations.py
   ```

## ✅ Option 2: Trigger Deployment (AUTOMATIC - 5 minutes)

The new `start.sh` script will automatically run migrations:

1. **Go to Render Dashboard:**
   - https://dashboard.render.com
   - Services → `parlay-gorilla-backend`

2. **Trigger Manual Deploy:**
   - Click: **Manual Deploy** → **Deploy latest commit**
   - Or click: **Deploy** button

3. **Monitor Logs:**
   - Click: **Logs** tab
   - Look for: `[STARTUP] Running Alembic migrations...`
   - Wait for: `INFO  [alembic.runtime.migration] Running upgrade ...`

4. **Wait for Deployment:**
   - Status should change to: **Live**
   - Usually takes 2-5 minutes

5. **Verify:**
   ```bash
   python scripts/validate_production_migrations.py
   ```

## ✅ Option 3: Render API (If you have API key)

If you have a Render API key, you can trigger a deployment programmatically:

1. **Get API Key:**
   - Dashboard → Profile → Account Settings → API Keys
   - Create new key

2. **Set Environment Variable:**
   ```powershell
   $env:RENDER_API_KEY='your-api-key-here'
   ```

3. **Run Script:**
   ```powershell
   cd backend
   python scripts/run_migrations_via_render_api.py
   ```

## Current Status

- ✅ **Fix code pushed** - `start.sh` will auto-run migrations on future deploys
- ❌ **Migrations NOT applied yet** - Need to run manually or trigger deploy
- ⏳ **Waiting for action** - Choose one of the options above

## Verification

After migrations run, test with:

```bash
cd backend
python scripts/validate_production_migrations.py
```

**Expected output:**
```
✅ PASS: Health Check
✅ PASS: Login Endpoint (401, not 500)
✅ PASS: Register Endpoint (201/400/422, not 500)
```

## Why Render CLI Didn't Work

The Render CLI binary download failed on Windows. The Dashboard Shell is actually **faster and more reliable** than the CLI for one-off commands like migrations.



