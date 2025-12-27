# Temporarily Disable Rate Limits for Testing

## Quick Guide

To disable rate limits for production testing:

### 1. Disable Rate Limits

In Render → Your Backend Service → Environment Variables:
```
DISABLE_RATE_LIMITS=true
```

Then **redeploy** the service.

### 2. Run Tests

```bash
python scripts/test_password_and_token_fixes.py --base-url https://api.parlaygorilla.com --verbose
```

### 3. Re-enable Rate Limits

**IMPORTANT:** After testing, immediately set:
```
DISABLE_RATE_LIMITS=false
```

Or remove the variable entirely, then **redeploy**.

## Security Warning

⚠️ **NEVER leave `DISABLE_RATE_LIMITS=true` in production!**

This disables all rate limiting, making your API vulnerable to:
- Brute force attacks
- DDoS attacks
- Resource exhaustion
- Abuse and spam

## What This Does

When `DISABLE_RATE_LIMITS=true`:
- All `@rate_limit()` decorators are bypassed
- No rate limiting is applied to any endpoint
- Useful for running comprehensive test suites

When `DISABLE_RATE_LIMITS=false` (default):
- Normal rate limiting applies:
  - Registration: 5/minute
  - Login: 10/minute
  - Password reset: 5/hour
  - etc.

## Current Rate Limits (when enabled)

- **Registration**: 5/minute per IP
- **Login**: 10/minute per IP
- **Password Reset**: 5/hour per IP
- **Password Reset Attempts**: 10/hour per IP

## Testing Workflow

1. Set `DISABLE_RATE_LIMITS=true` in Render
2. Wait for deployment to complete
3. Run test suite
4. **Immediately** set `DISABLE_RATE_LIMITS=false`
5. Redeploy

## Alternative: Increase Limits Temporarily

Instead of disabling, you could temporarily increase limits:
- Change `@rate_limit("5/minute")` to `@rate_limit("100/minute")` for testing
- But disabling is cleaner for comprehensive test runs

