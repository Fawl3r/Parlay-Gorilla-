# FEATURE_SETTLEMENT Production Rollout Guide

## ✅ Pre-Rollout Checklist

All stabilization work has been completed:
- ✅ Comprehensive unit tests (>90% coverage)
- ✅ Integration tests for all settlement flows
- ✅ Edge case handling (null scores, missing data)
- ✅ Error handling with crash-proof jobs
- ✅ Circuit breaker protection (opens after 5 consecutive errors)
- ✅ Rate limiting (max 100 games per cycle)
- ✅ Monitoring and health checks (`/health/settlement` endpoint)
- ✅ Structured logging with context

## 🚀 Production Rollout Steps

### Step 1: Deploy Code to Production

The code has been committed and pushed to `main`:
```bash
git log --oneline -1
# Should show: feat: Stabilize FEATURE_SETTLEMENT with comprehensive testing...
```

**If using Render:**
- Code will auto-deploy from `main` branch
- Wait for deployment to complete
- Verify deployment: `curl https://api.parlaygorilla.com/health`

### Step 2: Enable FEATURE_SETTLEMENT in Production

**For Render Production:**

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Navigate to your backend service (`parlay-gorilla-backend`)
3. Go to **Environment** tab
4. Click **Add Environment Variable**
5. Add:
   ```
   Key: FEATURE_SETTLEMENT
   Value: true
   ```
6. Click **Save Changes**
7. Render will automatically redeploy

**For Other Platforms:**
Set the environment variable:
```bash
FEATURE_SETTLEMENT=true
```

### Step 3: Verify Settlement System is Running

After deployment, verify the system is healthy:

```bash
# Check general health
curl https://api.parlaygorilla.com/health

# Check settlement-specific health
curl https://api.parlaygorilla.com/health/settlement
```

Expected response from `/health/settlement`:
```json
{
  "status": "healthy",
  "feature_enabled": true,
  "worker": {
    "running": true,
    "circuit_breaker": {
      "open": false,
      "consecutive_errors": 0,
      "opened_at": null
    }
  },
  "heartbeat": {
    "last_beat": "2024-01-XX...",
    "seconds_since_beat": 45.2,
    "meta": {
      "parlays_settled": 0,
      "parlays_won": 0,
      "parlays_lost": 0
    }
  }
}
```

### Step 4: Monitor for First 24 Hours

**Critical Monitoring Points:**

1. **Health Check** (every 15 minutes):
   ```bash
   curl https://api.parlaygorilla.com/health/settlement
   ```
   - Status should be "healthy"
   - Worker should be "running"
   - Circuit breaker should be "open": false

2. **Application Logs** (check Render logs):
   - Look for settlement-related errors
   - Verify legs are being settled correctly
   - Check for any database errors

3. **Settlement Activity**:
   - Monitor `/health/settlement` heartbeat meta
   - Should see `parlays_settled` count increasing
   - Verify `parlays_won` and `parlays_lost` are accurate

4. **Error Rate**:
   - Check `errors_total` in settlement metrics
   - Should be < 0.1% of total settlements
   - If errors spike, check logs immediately

### Step 5: Spot-Check Settlements

Manually verify a few settled parlays:

1. Find a FINAL game with parlays
2. Check that legs were settled correctly:
   - WON legs should have `status="WON"` and `settled_at` set
   - LOST legs should have `status="LOST"` and `settled_at` set
3. Verify parlay status cascaded correctly:
   - All legs WON → parlay WON
   - Any leg LOST → parlay LOST

### Step 6: Rollback Plan (If Needed)

If issues occur, **immediately disable** the feature:

**Render:**
1. Go to Environment tab
2. Change `FEATURE_SETTLEMENT` from `true` to `false`
3. Save (auto-redeploys)

**Or via CLI:**
```bash
# Set to false
FEATURE_SETTLEMENT=false
```

The system will:
- Stop processing new settlements
- Jobs will skip settlement logic
- No new settlements will occur
- Existing settled parlays remain unchanged

## 📊 Monitoring Dashboard

### Key Metrics to Track

1. **Settlement Health** (`/health/settlement`):
   - Worker running status
   - Circuit breaker state
   - Last heartbeat time

2. **Settlement Activity**:
   - Legs settled per hour
   - Parlays settled per hour
   - Win/loss ratio

3. **Error Rate**:
   - Errors per hour
   - Error types
   - Circuit breaker triggers

### Alert Thresholds

Set up alerts for:
- Circuit breaker opens (status: "circuit_open")
- No heartbeat for > 10 minutes (status: "stale")
- Error rate > 1% of settlements
- Worker stops running (status: "stopped")

## 🔍 Troubleshooting

### Circuit Breaker Opens

If circuit breaker opens:
1. Check application logs for error patterns
2. Verify database connectivity
3. Check for data integrity issues
4. Wait 5 minutes (circuit reset timeout)
5. If persists, disable feature and investigate

### No Settlements Occurring

Check:
1. Are there FINAL games with pending legs?
2. Is worker running? (`/health/settlement`)
3. Are there errors in logs?
4. Is feature flag enabled? (`feature_enabled: true`)

### Incorrect Settlements

If settlements are wrong:
1. Check game scores are correct
2. Verify leg selections match teams
3. Review calculation logic in logs
4. Disable feature and investigate

## ✅ Success Criteria

After 24-48 hours, verify:
- ✅ Zero crashes from settlement
- ✅ Error rate < 0.1%
- ✅ All settlements are accurate (spot-checked)
- ✅ Circuit breaker has not opened
- ✅ Worker heartbeat is consistent
- ✅ No performance degradation

## 📝 Post-Rollout

Once stable:
1. Document any issues encountered
2. Update monitoring dashboards
3. Set up automated alerts
4. Consider enabling additional settlement features

## 🔗 Related Documentation

- [Safe Fix Forward Plan](./ops/plan/safe_fix_forward.md)
- [Root Cause Analysis](./ops/incidents/root_cause.md)
- [Settlement System Tests](./backend/tests/test_settlement_*.py)
