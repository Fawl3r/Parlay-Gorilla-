# Safe Fix-Forward Deployment Plan

**Date**: 2026-01-22  
**Rollback Point**: `eb0d95e` (known-good state)  
**Status**: Ready for implementation

## Overview

This plan provides a step-by-step safe fix-forward path from rollback point `eb0d95e` to reintroduce features with comprehensive guardrails. The goal is to prevent future production outages by adding feature flags, health checks, crash-proof jobs, and graceful error handling.

## Prerequisites

- Current branch is at `eb0d95e` (rollback point)
- All guardrails have been implemented (see implementation checklist)
- Staging environment is available for testing

## Phase 1: Create Fix-Forward Branch

### Step 1.1: Create Branch from Rollback Point

```bash
# Ensure we're on the rollback point
git checkout eb0d95e

# Create new branch for safe fix-forward
git checkout -b hotfix/safe-forward

# Verify we're on the right commit
git log --oneline -1
# Should show: eb0d95e Redesign Analytics, Odds Heatmap, and Upset Finder pages...
```

### Step 1.2: Verify Current State

```bash
# Check that backend can start
cd backend
python -m uvicorn app.main:app --reload --port 8000
# Should start without errors

# In another terminal, test health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/health/db
# Both should return 200
```

## Phase 2: Implement Guardrails (MUST DO FIRST)

### Step 2.1: Feature Flags

**Files Modified**: `backend/app/core/config.py`

**Changes**:
- Added `feature_analytics: bool = True`
- Added `feature_live_scores: bool = True`
- Added `feature_settlement: bool = False` (OFF by default)
- Added `feature_live_wall: bool = True`

**Verification**:
```bash
# Test feature flags are loaded
python -c "from app.core.config import settings; print(f'Analytics: {settings.feature_analytics}, Settlement: {settings.feature_settlement}')"
```

### Step 2.2: Health Endpoints

**Files Modified**: `backend/app/api/routes/health.py`

**Changes**:
- Enhanced `/health` to never crash (always returns 200)
- Added `/health/db` endpoint (returns 200 if healthy, 503 if unhealthy)

**Verification**:
```bash
# Test health endpoints
curl -v http://localhost:8000/health
# Should return 200 with {"status": "healthy", ...}

curl -v http://localhost:8000/health/db
# Should return 200 with {"status": "healthy", "database": "connected", ...}

# Test with DB disconnected (if possible)
# Should return 503 with {"status": "unhealthy", "database": "disconnected", ...}
```

### Step 2.3: Global Exception Handler

**Files Modified**: `backend/app/main.py`

**Changes**:
- Enhanced global exception handler to include request_id in all responses
- Added request_id to error logs for correlation
- Wrapped handler logic in try/except to never crash

**Verification**:
```bash
# Trigger an error (e.g., invalid endpoint)
curl http://localhost:8000/api/invalid-endpoint
# Should return 500 with {"detail": "...", "request_id": "..."}
# Check logs for request_id correlation
```

### Step 2.4: Crash-Proof Background Jobs

**Files Modified**: `backend/app/services/scheduler.py`

**Changes**:
- Added `@crash_proof_job` decorator with exponential backoff
- Applied decorator to all background job methods
- Gated settlement jobs (`_auto_resolve_parlays`, `_resolve_saved_parlays`, `_process_ready_commissions`) behind `FEATURE_SETTLEMENT` flag

**Verification**:
```bash
# Start backend and check scheduler logs
# Jobs should log with [JOB] prefix and job_id
# Settlement jobs should be skipped if FEATURE_SETTLEMENT=false
```

### Step 2.5: Analytics Endpoint Hardening

**Files Modified**: `backend/app/api/routes/analytics.py`

**Changes**:
- Wrapped entire endpoint in try/except
- Returns empty state (200 with empty games array) on any error
- Checks `FEATURE_ANALYTICS` flag before processing
- Logs errors with request_id

**Verification**:
```bash
# Test analytics endpoint
curl http://localhost:8000/api/analytics/games
# Should always return 200, even on errors (empty games array)

# Test with feature flag disabled
export FEATURE_ANALYTICS=false
# Restart backend
curl http://localhost:8000/api/analytics/games
# Should return empty state
```

### Step 2.6: Frontend Graceful Degradation

**Files Modified**: `frontend/app/analytics/page.tsx`

**Changes**:
- Error handling shows empty state instead of error message
- Page loads even if backend returns empty data

**Verification**:
```bash
# Start frontend
cd frontend
npm run dev

# Navigate to /analytics
# Should show empty state gracefully if backend fails
```

## Phase 3: Commit Guardrails

### Step 3.1: Commit Changes

```bash
# Stage all guardrail changes
git add backend/app/core/config.py
git add backend/app/api/routes/health.py
git add backend/app/main.py
git add backend/app/services/scheduler.py
git add backend/app/api/routes/analytics.py
git add frontend/app/analytics/page.tsx
git add ops/incidents/root_cause.md
git add ops/plan/safe_fix_forward.md

# Commit with descriptive message
git commit -m "feat: Add production guardrails (feature flags, health checks, crash-proof jobs)

- Add feature flags: FEATURE_ANALYTICS, FEATURE_LIVE_SCORES, FEATURE_SETTLEMENT (OFF), FEATURE_LIVE_WALL
- Add /health/db endpoint for database health monitoring
- Enhance global exception handler with request_id tracking
- Wrap all background jobs with crash-proof decorator and exponential backoff
- Gate settlement jobs behind FEATURE_SETTLEMENT flag (defaults OFF)
- Add comprehensive error handling to analytics endpoint (graceful empty state)
- Add graceful error handling to frontend analytics page
- Create root cause analysis and deployment plan documents

This prevents future production outages by:
- Allowing instant kill switches via feature flags
- Ensuring health endpoints never crash
- Preventing background jobs from crashing the app
- Providing graceful degradation for all endpoints"
```

### Step 3.2: Test Locally

```bash
# Run backend tests (if available)
cd backend
pytest

# Test all endpoints manually
curl http://localhost:8000/health
curl http://localhost:8000/health/db
curl http://localhost:8000/api/analytics/games

# Verify no errors in logs
```

## Phase 4: Staging Deployment

### Step 4.1: Push to Staging

```bash
# Push branch to remote
git push origin hotfix/safe-forward

# Create PR to staging branch (or merge directly if using staging branch)
# Review PR carefully
```

### Step 4.2: Deploy to Staging

```bash
# Deploy to staging environment
# (Commands depend on your deployment setup - Render, AWS, etc.)

# Monitor deployment logs
# Verify:
# - Backend starts without errors
# - Health endpoints return 200
# - No 500 errors in logs
```

### Step 4.3: Staging Verification

```bash
# Test all critical endpoints
curl https://staging.parlaygorilla.com/health
curl https://staging.parlaygorilla.com/health/db
curl https://staging.parlaygorilla.com/api/analytics/games

# Test feature flags
# Set FEATURE_ANALYTICS=false in staging environment
# Verify analytics endpoint returns empty state

# Test with FEATURE_SETTLEMENT=false (should be default)
# Verify settlement jobs are skipped in logs
```

### Step 4.4: Staging Acceptance Checklist

- [ ] Backend boots without crash loop
- [ ] `/health` returns 200 always
- [ ] `/health/db` returns 200 when DB reachable, 503 when not
- [ ] Analytics page loads (or graceful empty state)
- [ ] LiveMarquee/feed does not crash dashboard
- [ ] Settlement system cannot crash app (feature-flagged + wrapped)
- [ ] No schema mismatch errors
- [ ] Request IDs appear in all error logs

## Phase 5: Production Deployment

### Step 5.1: Merge to Main

```bash
# After staging verification passes, merge to main
git checkout main
git merge hotfix/safe-forward

# Push to main
git push origin main
```

### Step 5.2: Deploy to Production

```bash
# Deploy to production
# (Commands depend on your deployment setup)

# Monitor deployment closely
# Watch for:
# - Backend startup errors
# - Health endpoint failures
# - 500 errors
```

### Step 5.3: Production Verification

```bash
# Test production endpoints
curl https://parlaygorilla.com/health
curl https://parlaygorilla.com/health/db
curl https://parlaygorilla.com/api/analytics/games

# Monitor error logs
# Verify request_ids in all error responses
```

### Step 5.4: Production Monitoring

**First 30 Minutes**:
- Monitor `/health` and `/health/db` endpoints (should always return 200/503, never 500)
- Check error logs for any 500 errors
- Verify request_ids in all error logs
- Monitor background job logs for any crashes

**First 24 Hours**:
- Continue monitoring health endpoints
- Check analytics page loads correctly
- Verify no increase in 500 errors
- Monitor feature flag usage

## Phase 6: Reintroduce Features (Optional - After Guardrails Stable)

### Step 6.1: Reintroduce Settlement System

**Only after guardrails are stable in production for 24+ hours**

```bash
# Enable settlement feature flag
export FEATURE_SETTLEMENT=true

# Restart backend
# Monitor logs for settlement jobs
# Verify jobs run without crashing
```

### Step 6.2: Reintroduce Other Features

If there were other features rolled back:
1. Cherry-pick low-risk commits first
2. Test thoroughly in staging
3. Enable via feature flags
4. Monitor closely in production

## Rollback Plan

If issues occur in production:

### Immediate Rollback

```bash
# Revert to rollback point
git checkout eb0d95e
git push origin main --force  # Only if necessary

# Or disable feature flags
export FEATURE_ANALYTICS=false
export FEATURE_SETTLEMENT=false
# Restart backend
```

### Feature Flag Kill Switch

If a specific feature is causing issues:

```bash
# Disable feature via environment variable
export FEATURE_ANALYTICS=false  # or FEATURE_SETTLEMENT, etc.

# Restart backend
# Feature is immediately disabled without code changes
```

## Success Criteria

- ✅ Backend never crashes on startup
- ✅ All endpoints return proper HTTP status codes (never 500 from unhandled exceptions)
- ✅ Health endpoints always respond
- ✅ Background jobs never crash the app
- ✅ Analytics page loads even if backend fails
- ✅ Feature flags allow instant kill switches
- ✅ Request IDs in all logs for debugging
- ✅ No increase in production errors after deployment

## Post-Deployment

1. **Documentation**: Update deployment docs with feature flag usage
2. **Monitoring**: Set up alerts for health endpoint failures
3. **Testing**: Add automated tests for guardrails
4. **Training**: Ensure team knows how to use feature flags

## Notes

- All guardrails are backward-compatible (defaults match current behavior)
- Feature flags can be toggled without code changes
- Health endpoints are lightweight and safe to call frequently
- Request IDs enable correlation of errors across logs
- Crash-proof jobs ensure background tasks never crash the app

## Commands Reference

### Health Check Validation
```bash
curl -v http://localhost:8000/health
curl -v http://localhost:8000/health/db
```

### Feature Flag Testing
```bash
# Disable analytics
export FEATURE_ANALYTICS=false
# Restart backend
# Verify analytics endpoint returns empty state
```

### Git Workflow
```bash
git checkout -b hotfix/safe-forward eb0d95e
# Make changes
git commit -m "feat: Add production guardrails"
# Test thoroughly
git push origin hotfix/safe-forward
# Create PR, review, merge to main
```
