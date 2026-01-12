# Testing Alembic Migration Auto-Run

## ✅ What Was Tested Locally

1. **Migration Manager Initialization** - ✅ PASSED
   - Path resolution works correctly
   - Finds `alembic.ini` and `alembic/` directory
   - Config builds with absolute paths (required for Render)

2. **Python Syntax** - ✅ PASSED
   - All files compile without errors
   - No linter errors

## ⚠️ What Still Needs Production Testing

### 1. Render `startCommand` Syntax
**Location:** `render.yaml` line 56
```yaml
startCommand: alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Test:**
- [ ] Verify Render executes `&&` chaining correctly
- [ ] Verify `alembic upgrade head` runs before `uvicorn`
- [ ] Verify if `alembic` fails, `uvicorn` doesn't start (good - prevents broken deploys)
- [ ] Check Render logs for migration output

**Alternative if `&&` doesn't work:**
Use a shell script wrapper:
```yaml
startCommand: bash -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

### 2. FastAPI Startup Migration Runner
**Location:** `backend/app/main.py` lines 284-287

**Test:**
- [ ] Verify migrations run on startup for PostgreSQL
- [ ] Verify migrations are skipped for SQLite (dev mode)
- [ ] Verify startup doesn't hang if migrations take time
- [ ] Verify startup continues if migrations already applied (idempotent)

**How to test:**
1. Deploy to Render staging/production
2. Check logs for: `[STARTUP] Running Alembic migrations...`
3. Verify no errors about missing columns
4. Test `/api/auth/login` and `/api/auth/register` endpoints

### 3. Database Schema Verification
**Test:**
- [ ] Connect to production DB and verify `users.premium_custom_builder_used` exists
- [ ] Verify `users.premium_custom_builder_period_start` exists
- [ ] Verify `users.premium_inscriptions_used` exists
- [ ] Verify `users.premium_inscriptions_period_start` exists
- [ ] Check `alembic_version` table shows latest revision: `022_add_premium_usage_periods`

**SQL to check:**
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

SELECT version_num FROM alembic_version;
```

### 4. End-to-End Auth Flow
**Test:**
- [ ] `POST /api/auth/register` returns 200 (not 500)
- [ ] `POST /api/auth/login` returns 200 or 401 (not 500)
- [ ] `GET /api/auth/me` works after login
- [ ] Frontend login page works without console errors

## 🚨 If Migrations Fail in Production

### Option 1: Manual Migration via Render Shell
1. Go to Render Dashboard → `parlay-gorilla-backend` → Shell
2. Run: `alembic upgrade head`
3. Check for errors
4. Restart service

### Option 2: Fix render.yaml startCommand
If `&&` doesn't work, create a startup script:

**Create:** `backend/start.sh`
```bash
#!/bin/bash
set -e
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Update render.yaml:**
```yaml
startCommand: bash start.sh
```

### Option 3: Verify Alembic is Installed
Check `requirements.txt` includes `alembic` (it should - we added it).

## 📝 Current Status

- ✅ Code written and syntax-checked
- ✅ Unit tests pass locally
- ⚠️ **NOT tested in production Render environment**
- ⚠️ **NOT verified that Render `startCommand` `&&` syntax works**

## 🎯 Next Steps

1. **Deploy to Render** and monitor logs
2. **Check Render logs** for migration output
3. **Test auth endpoints** (`/api/auth/login`, `/api/auth/register`)
4. **Verify database schema** using SQL queries above
5. **If issues occur**, use manual migration via Render Shell as fallback




