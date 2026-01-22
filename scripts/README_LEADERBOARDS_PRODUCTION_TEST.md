# Leaderboards Production Smoke Test

Comprehensive production smoke test for the leaderboards feature on parlaygorilla.com.

## Overview

This test suite validates all leaderboard functionality against production:
- Backend API endpoints (4 endpoints)
- Frontend UI and navigation
- Privacy controls
- Data accuracy
- Performance
- Error handling

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

## Running the Tests

### Basic Usage

Test against production (default):
```bash
python scripts/smoke_test_leaderboards_production.py
```

### Custom URLs

Test against different environments:
```bash
BACKEND_URL=https://api.parlaygorilla.com \
FRONTEND_URL=https://parlaygorilla.com \
python scripts/smoke_test_leaderboards_production.py
```

### Local Testing

Test against local development:
```bash
BACKEND_URL=http://localhost:8000 \
FRONTEND_URL=http://localhost:3000 \
python scripts/smoke_test_leaderboards_production.py
```

## Test Coverage

### Backend API Tests

1. **Verified Winners endpoint** (`/api/leaderboards/custom`)
   - Response structure validation
   - Entry field validation
   - Cache headers

2. **AI Usage endpoint** (`/api/leaderboards/ai-usage`)
   - Both periods (30d, all_time)
   - Period validation
   - Response structure

3. **Arcade Points endpoint** (`/api/leaderboards/arcade-points`)
   - Both periods (30d, all_time)
   - Entry structure validation

4. **Recent Wins feed** (`/api/leaderboards/arcade-wins`)
   - Feed structure
   - Entry validation

5. **Limit validation**
   - Valid limits (1-100)
   - Invalid limits (0, >100)

6. **Empty leaderboards handling**
   - All endpoints return empty arrays (not errors)

7. **Privacy controls**
   - Hidden users excluded
   - Anonymous users show as Gorilla_XXXX
   - No empty usernames

8. **Data accuracy**
   - Rankings are sequential
   - Period filtering works correctly
   - Values are valid (non-negative, ranges correct)
   - Sorting is correct

9. **API performance**
   - Response times < 5s
   - Cache headers present
   - Cached requests faster

### Frontend Tests

1. **Page load** - `/leaderboards` page loads correctly
2. **Alias redirect** - `/leaderboard` redirects to `/leaderboards`
3. **Tab switching** - All 3 tabs work (Verified Winners, AI Power Users, Arcade Points)
4. **Period filters** - Filter buttons work for AI Usage and Arcade Points
5. **Loading states** - Loading indicators display correctly
6. **Error handling** - No errors displayed on page
7. **Navigation integration** - Leaderboards link in nav works
8. **Frontend performance** - Page loads in reasonable time

## Output

The test provides color-coded output:
- ✓ **GREEN (PASS)**: Test passed
- ✗ **RED (FAIL)**: Test failed
- ⊘ **YELLOW (SKIP)**: Test skipped (non-critical)
- ℹ **BLUE (INFO)**: Informational message

## Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed

## Example Output

```
======================================================================
Production Smoke Test: Leaderboards
Backend:  https://api.parlaygorilla.com
Frontend: https://parlaygorilla.com
======================================================================

======================================================================
Backend API Tests
Base URL: https://api.parlaygorilla.com
======================================================================

✓ PASS: Verified Winners endpoint structure
✓ PASS: Verified Winners entry structure
ℹ INFO: Verified Winners Found 15 entries
✓ PASS: Verified Winners endpoint
✓ PASS: AI Usage endpoint (30d)
✓ PASS: AI Usage endpoint (all_time)
...

======================================================================
Summary
======================================================================

  PASS: Verified Winners endpoint
  PASS: AI Usage endpoint
  PASS: Arcade Points endpoint
  ...

14/14 tests passed
```

## Troubleshooting

### Playwright Not Found

If you get "playwright not found" errors:
```bash
pip install playwright
playwright install chromium
```

### Timeout Errors

If tests timeout, increase timeout values in the script or check network connectivity.

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

## CI/CD Integration

This test can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Leaderboards Production Tests
  run: |
    pip install playwright httpx
    playwright install chromium
    python scripts/smoke_test_leaderboards_production.py
  env:
    BACKEND_URL: https://api.parlaygorilla.com
    FRONTEND_URL: https://parlaygorilla.com
```

## Notes

- Tests are designed to be non-destructive (read-only)
- Tests may skip some checks if data doesn't exist yet (empty leaderboards)
- Performance thresholds are lenient to account for network variability
- Some tests may show INFO messages for expected conditions (e.g., anonymous users)
