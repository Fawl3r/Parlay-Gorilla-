# API-Sports Production Deployment - Quick Checklist

## 🚀 Deploy Steps (5 minutes)

### 1. Set Environment Variable
- Render Dashboard → `parlay-gorilla-backend` → **Environment**
- Add: `API_SPORTS_API_KEY` = `your_key_here`
- **Save** (triggers auto-deploy)

### 2. Verify Migration
After deploy completes, check logs for:
```
[STARTUP] Running Alembic migrations...
Running upgrade 041_create_system_heartbeats -> 042_add_apisports_tables
```

Or manually in Render Shell:
```bash
alembic current
```
Should show: `042_add_apisports_tables (head)`

### 3. Test Quota Endpoint (Admin)
```bash
curl -X GET "https://api.parlaygorilla.com/api/admin/apisports/quota" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT"
```

Expected: `{"used_today": 0, "remaining": 100, "circuit_open": false}`

### 4. Wait for Scheduler (60 min)
Check logs after ~60 minutes for:
```
[SCHEDULER] API-Sports refresh: used=2 remaining=98 refreshed={...}
```

## ✅ Verification

- [ ] Migration `042_add_apisports_tables` applied
- [ ] `API_SPORTS_API_KEY` set in Render env vars
- [ ] Quota endpoint returns `remaining: 100`
- [ ] Scheduler runs refresh (check logs after 60 min)
- [ ] No errors in logs

## 📚 Full Guide

See: [docs/API_SPORTS_PRODUCTION_DEPLOYMENT.md](docs/API_SPORTS_PRODUCTION_DEPLOYMENT.md)
