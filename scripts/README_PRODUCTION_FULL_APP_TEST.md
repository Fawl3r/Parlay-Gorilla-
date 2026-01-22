# Comprehensive Production Test - Full Parlay Gorilla App

Complete production smoke test suite for the entire Parlay Gorilla application at parlaygorilla.com.

## Overview

This test suite validates:
- All public pages and routes
- All protected routes (with authentication)
- All backend API endpoints
- Critical user flows
- Error handling
- Performance metrics

## Prerequisites

1. **Python 3.11+** with async support
2. **Playwright** for browser automation:
   ```bash
   pip install playwright
   playwright install chromium
   ```
3. **httpx** for HTTP requests:
   ```bash
   pip install httpx
   ```

## Quick Start

### Basic Usage

Run comprehensive test against production:
```bash
python scripts/smoke_test_production_full_app.py
```

### Quick Test (5-10 minutes)

Run quick smoke test (health checks + key pages only):
```bash
QUICK=true python scripts/smoke_test_production_full_app.py
```

### With Authentication

Test protected routes with authentication:
```bash
TEST_EMAIL=your@email.com \
TEST_PASSWORD=yourpassword \
python scripts/smoke_test_production_full_app.py
```

### Custom URLs

Test against different environments:
```bash
BACKEND_URL=https://api.parlaygorilla.com \
FRONTEND_URL=https://parlaygorilla.com \
python scripts/smoke_test_production_full_app.py
```

### Local Testing

Test against local development:
```bash
BACKEND_URL=http://localhost:8000 \
FRONTEND_URL=http://localhost:3000 \
python scripts/smoke_test_production_full_app.py
```

## Test Coverage

### Backend API Tests

#### Core & Health
- `GET /health` - Health check
- `GET /api/health/detailed` - Detailed health check
- `GET /api/metrics` - Application metrics

#### Games & Odds
- `GET /api/sports/{sport}/games` - Get games for sports (NFL, NBA)
- `GET /api/weeks/nfl` - NFL week information

#### Parlays
- `GET /api/parlay/history` - Get parlay history (requires auth)
- `POST /api/parlay/suggest` - Generate AI parlay (requires auth)

#### Social Features
- `GET /api/social/feed` - Get social feed

#### Analysis
- `GET /api/analysis/{sport}/upcoming` - List upcoming analyses

#### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/forgot-password` - Password reset request

#### Profile & Billing
- `GET /api/profile/me` - Get user profile (requires auth)
- `GET /api/subscription/me` - Get subscription status (requires auth)

### Frontend Page Tests

#### Public Pages
- `/` - Landing page
- `/pricing` - Pricing page
- `/leaderboards` - Leaderboards page
- `/analysis` - Game Analytics page
- `/tutorial` - Tutorial page (comprehensive mode)
- `/docs` - Documentation page (comprehensive mode)
- `/auth/login` - Login page (comprehensive mode)
- `/auth/signup` - Signup page (comprehensive mode)

#### Protected Routes
- `/app` - Main Dashboard (requires auth)
- `/analytics` - Analytics Dashboard (requires auth)
- `/profile` - Profile page (requires auth)
- `/billing` - Billing page (requires auth)

#### Dashboard Tabs
- Games tab
- AI Picks tab
- Custom Builder tab
- Insights tab

### User Flow Tests

1. **Signup Flow** - Signup form loads correctly
2. **Login Flow** - Login form loads correctly
3. **Parlay Generation Flow** - AI Picks tab accessible and functional
4. **Navigation Flow** - Navigation between pages works

### Error Handling Tests

- 404 error pages handled correctly
- Unauthenticated access to protected routes redirects properly

### Performance Tests

#### Page Performance (Comprehensive Mode)
- Landing page load time
- Leaderboards page load time
- Pricing page load time
- Target: < 5 seconds per page

#### API Performance (Comprehensive Mode)
- Health endpoint response time
- Leaderboards API response time
- Social feed API response time
- Target: < 2 seconds per API call

## Test Modes

### Quick Mode (`QUICK=true`)

Runs essential tests only:
- Health checks
- Key public pages (landing, pricing, leaderboards, analysis)
- Basic API endpoints
- Error handling

**Duration:** 5-10 minutes

### Comprehensive Mode (default)

Runs full test suite:
- All public pages
- All protected routes
- All API endpoints
- User flows
- Error handling
- Performance metrics

**Duration:** 20-30 minutes

## Output

The test provides color-coded output:
- ✓ **GREEN (PASS)**: Test passed
- ✗ **RED (FAIL)**: Test failed
- ⊘ **YELLOW (SKIP)**: Test skipped (non-critical)
- ℹ **BLUE (INFO)**: Informational message

## Example Output

```
======================================================================
Comprehensive Production Test: Full Parlay Gorilla App
Backend:  https://api.parlaygorilla.com
Frontend: https://parlaygorilla.com
Mode:     Comprehensive
======================================================================

======================================================================
Backend API Tests
======================================================================

✓ PASS: Health endpoint (/health)
✓ PASS: Health endpoint (/api/health/detailed)
✓ PASS: Games API (nfl)
ℹ INFO: Games API (nfl) - Found 12 games
✓ PASS: Social feed API
...

======================================================================
Frontend Tests
======================================================================

✓ PASS: Landing page
✓ PASS: Pricing page
✓ PASS: Leaderboards page
...

======================================================================
Summary
======================================================================

  PASS: Health /health
  PASS: Health /api/health/detailed
  PASS: Games API nfl
  ...

45/45 tests passed (100%)
```

## Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed

## Authentication

To test protected routes, provide credentials via environment variables:

```bash
TEST_EMAIL=your@email.com \
TEST_PASSWORD=yourpassword \
python scripts/smoke_test_production_full_app.py
```

The test will:
1. Authenticate using provided credentials
2. Test protected routes with authentication
3. Test dashboard tabs and functionality
4. Test parlay generation flow

**Note:** The test does NOT create new accounts or modify data. It only reads/validates existing functionality.

## Troubleshooting

### Playwright Not Found

If you get "playwright not found" errors:
```bash
pip install playwright
playwright install chromium
```

### Timeout Errors

If tests timeout:
1. Check network connectivity
2. Verify URLs are correct
3. Increase timeout values in script if needed

### Authentication Failures

If protected route tests fail:
1. Verify TEST_EMAIL and TEST_PASSWORD are correct
2. Check that the account exists and is active
3. Verify backend authentication is working

### API Errors

If API endpoints return errors:
1. Check that the backend URL is correct
2. Verify the API is accessible
3. Check for CORS issues (frontend tests)

### Frontend Errors

If frontend tests fail:
1. Verify the frontend URL is correct
2. Check that the page is accessible
3. Ensure JavaScript is enabled
4. Check browser console for errors

## CI/CD Integration

This test can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Full App Production Tests
  run: |
    pip install playwright httpx
    playwright install chromium
    python scripts/smoke_test_production_full_app.py
  env:
    BACKEND_URL: https://api.parlaygorilla.com
    FRONTEND_URL: https://parlaygorilla.com
    TEST_EMAIL: ${{ secrets.TEST_EMAIL }}
    TEST_PASSWORD: ${{ secrets.TEST_PASSWORD }}
```

## Test Categories

### Backend API Tests
- Health & Metrics
- Games & Odds
- Parlays
- Social Features
- Analysis
- Authentication
- Profile & Billing
- Performance

### Frontend Tests
- Public Pages
- Protected Routes
- Dashboard Tabs
- User Flows
- Navigation
- Error Handling
- Performance

## Notes

- Tests are designed to be non-destructive (read-only)
- Some tests may skip if data doesn't exist (e.g., no games available)
- Performance thresholds are lenient to account for network variability
- Protected route tests require valid authentication credentials
- The test does not create or modify user accounts or data

## Related Test Scripts

- `smoke_test_leaderboards_production.py` - Detailed leaderboards testing
- `smoke_test_auth_and_billing.py` - Auth and billing flow testing
- `smoke_test_verification.py` - Verification flow testing
