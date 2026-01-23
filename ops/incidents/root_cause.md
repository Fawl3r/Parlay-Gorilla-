# Production 500 Error Root Cause Analysis

**Date**: 2026-01-22  
**Rollback Point**: `eb0d95e` (known-good state)  
**Status**: Resolved via rollback, implementing preventive measures

## Executive Summary

Production experienced widespread 500 errors that affected:
- Analytics endpoint (`/api/analytics/games`)
- Game fetching endpoints
- Parlay generation endpoints
- Background job scheduler

The system was rolled back to commit `eb0d95e` to restore service. This document identifies the likely root causes and preventive measures.

## Potential Root Causes

### 1. Schema Mismatch: metadata vs event_metadata

**Status**: NOT FOUND in current codebase (may have been rolled back)

**Description**: 
- User mentioned commits `f24d036` and `196c285` that renamed `metadata` to `event_metadata` in `ParlayFeedEvent`
- SQLAlchemy reserves `metadata` as an attribute name
- If migration was incomplete or code expected new column name but DB had old name, this would cause AttributeError

**Evidence**:
- No `ParlayFeedEvent` model found in current codebase
- `AppEvent` model uses `metadata_` as Python attribute with `Column("metadata", ...)` mapping (safe pattern)
- If similar pattern was attempted without proper migration, would cause 500s

**Impact**: High - Would cause all endpoints using the model to return 500

**Prevention**: Two-phase migration with compatibility layer (see Phase 3 in plan)

---

### 2. Startup Crash: Background Scheduler/Settlement Jobs

**Status**: LIKELY CAUSE

**Description**:
- Background scheduler starts on app startup (`main.py` line 400-418)
- Settlement/parlay resolution jobs run automatically
- If any job crashes during startup, it could prevent app from starting or cause cascading failures

**Evidence**:
- `scheduler.py` has many background jobs that could fail
- Startup code has try/except but may not be comprehensive enough
- Jobs like `_resolve_saved_parlays`, `_award_arcade_points` could fail if DB schema mismatches

**Impact**: Critical - Could prevent app from starting entirely

**Prevention**: 
- Wrap all job methods with try/except
- Gate risky jobs behind feature flags
- Never allow job exceptions to crash app startup

**File**: `backend/app/services/scheduler.py`
**Lines**: All `_*` job methods (lines 222-565)

---

### 3. Analytics Endpoint Runtime Errors

**Status**: LIKELY CAUSE

**Description**:
- `/api/analytics/games` endpoint performs complex queries and data processing
- Multiple potential failure points:
  - Database queries could fail
  - `TrafficRanker` could fail
  - `AnalysisRepository` could fail
  - Data processing loops could raise exceptions

**Evidence**:
- `analytics.py` line 93-299 has complex logic with multiple service calls
- No comprehensive try/except wrapper around entire endpoint
- Individual operations may have error handling but endpoint itself could still 500

**Impact**: High - Analytics page would be unusable

**Prevention**:
- Wrap entire endpoint in try/except
- Return graceful empty state on any error
- Check feature flag before processing

**File**: `backend/app/api/routes/analytics.py`
**Lines**: 93-299 (get_analytics_games endpoint)

---

### 4. Missing Error Handling in Global Exception Handler

**Status**: PARTIAL - Handler exists but may not be comprehensive

**Description**:
- Global exception handler in `main.py` (line 205-242) exists
- However, if handler itself crashes, no fallback exists
- Request ID may not be included in all error responses

**Evidence**:
- Handler has try/except for getting origin, but handler logic itself could fail
- Request ID is available via `request.state.request_id` but may not be logged consistently

**Impact**: Medium - Would cause 500s to not be properly handled/logged

**Prevention**:
- Add try/except around handler logic itself
- Ensure request_id is always included in responses and logs
- Never allow handler to crash

**File**: `backend/app/main.py`
**Lines**: 205-242 (global_exception_handler)

---

## Commits That May Have Introduced Issues

Based on user description (not found in current branch - may have been rolled back):

1. `96496b2` - "feat: Implement live scores + parlay settlement system"
   - **Risk**: Settlement system could crash on startup
   - **Action**: Gate behind `FEATURE_SETTLEMENT` flag, disable by default

2. `f24d036` - "fix: Rename metadata to event_metadata in ParlayFeedEvent"
   - **Risk**: Schema mismatch if migration incomplete
   - **Action**: Two-phase migration with compatibility layer

3. `196c285` - "fix: Update feed API to use event_metadata field"
   - **Risk**: Code expects new column but DB has old column
   - **Action**: Compatibility layer that reads from both

4. `151452d` - "fix: Fix remaining indentation issues in analytics endpoint"
   - **Risk**: Syntax errors or logic errors
   - **Action**: Comprehensive error handling

5. `4833ce6` - "fix: Add error handling to analytics endpoint and remove dashboard UI from analytics page"
   - **Risk**: Error handling may be incomplete
   - **Action**: Verify and enhance error handling

## Files Requiring Immediate Attention

1. **backend/app/services/scheduler.py**
   - All background job methods need try/except wrappers
   - Settlement jobs need feature flag gating

2. **backend/app/api/routes/analytics.py**
   - Endpoint needs comprehensive error handling
   - Should return empty state on any error

3. **backend/app/main.py**
   - Global exception handler needs hardening
   - Request ID must be in all error responses

4. **backend/app/core/config.py**
   - Add feature flags for risky features
   - Default settlement to OFF

5. **backend/app/api/routes/health.py**
   - Add `/health/db` endpoint
   - Ensure `/health` never crashes

## Prevention Strategy

1. **Feature Flags**: Gate all risky features behind flags
2. **Health Checks**: Add database health endpoint
3. **Crash-Proof Jobs**: Never allow background jobs to crash app
4. **Graceful Degradation**: All endpoints should fail gracefully
5. **Request ID Tracking**: All errors must include request_id for debugging

## Next Steps

See `ops/plan/safe_fix_forward.md` for step-by-step implementation plan.
