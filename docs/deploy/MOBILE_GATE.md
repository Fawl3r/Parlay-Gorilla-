# Mobile UX + Performance Gate

Pre-deploy gate that runs Playwright mobile tests against **production** (or staging) to enforce UX and performance budgets. **Fails CI if budgets are exceeded or auth/health checks fail** (no skip on prod).

## Auth: required for Gorilla Builder gate

The Gorilla Builder gate uses a **dedicated E2E account** and **never skips**:

- Create a prod user (e.g. `qa+e2e@yourdomain.com`). Use it only for E2E.
- Put credentials in **CI secrets**: `PG_MOBILE_TEST_EMAIL`, `PG_MOBILE_TEST_PASSWORD`.
- Put the same in **frontend/.env.local** for local gate runs.
- If credentials are missing or login fails → **test fails** (not skip). This makes the builder gate a hard stop for deployments.

## Quick start

```bash
cd frontend
# Set PG_MOBILE_TEST_EMAIL and PG_MOBILE_TEST_PASSWORD in .env.local
npm ci
npm run test:mobile:gate
```

## Environment variables

| Variable | Default | Description |
|----------|--------|-------------|
| `PG_E2E_BASE_URL` | `https://www.parlaygorilla.com` | Base URL for gate (production or staging). |
| `PG_MOBILE_BACKEND_URL` | same as base | Backend used for auth and health probe; set if front and API differ. |
| `PG_MOBILE_TEST_EMAIL` | — | **Required for gate.** E2E account email. |
| `PG_MOBILE_TEST_PASSWORD` | — | **Required for gate.** E2E account password. |
| `PG_BUDGET_TAP_FEEDBACK_MS` | 350 | Max ms from tap to loading/feedback visible. |
| `PG_BUDGET_API_MS` | 2500 | Max ms for key API responses. |
| `PG_BUDGET_RESULTS_MS` | 6000 | Max ms until results container visible. |
| `PG_BUDGET_WORST_LONG_TASK_MS` | 120 | Max single long-task duration (ms). |
| `PG_BUDGET_LONG_TASKS_COUNT` | 3 | Max number of long tasks during critical flow. |
| `PG_BUDGET_TIME_TO_FIRST_SKELETON_MS` | 500 | LCP-ish: max ms until first skeleton visible. |
| `PG_BUDGET_SPINNER_DURATION_MS` | 4500 | Max spinner visible duration (feedback → results). |
| `PG_BUDGET_RESULTS_VISIBLE_MS` | 6000 | Max ms from tap to results container visible. |
| `PG_BUDGET_COLD_RESULTS_MS` | 7000 | Cold load: max ms until results (stricter). |
| `PG_BUDGET_COLD_TAP_FEEDBACK_MS` | 450 | Cold load: max tap-to-feedback ms. |

Create `.env.local` in `frontend/` with:

- **Gate (required):** `PG_MOBILE_TEST_EMAIL`, `PG_MOBILE_TEST_PASSWORD`.
- For staging: `PG_E2E_BASE_URL=https://staging.parlaygorilla.com`.
- If backend is on another host: `PG_MOBILE_BACKEND_URL=https://api.yourdomain.com` (used for auth and health probe).

## Commands

| Command | Description |
|---------|-------------|
| `npm run test:mobile` | Full mobile suite (all specs under `tests/mobile`). |
| `npm run test:mobile:gate` | **Gate only**: runs `tests/e2e/mobile-gate` (Gorilla Builder + AI Picks budgets). |
| `npm run test:mobile:gate:ci` | Same as gate (use in CI; report in `playwright-report-gate`). |
| `npm run test:mobile:report` | Open last HTML report (`playwright-report`). |

## CI (GitHub Actions) — pre-deploy gate

**Rule: deploys only on green.** Run the gate in CI; if it fails, block the deploy.

1. Install: `npm ci`, install Playwright browsers (chromium).
2. Run gate: `npm run test:mobile:gate:ci` (use in workflow).
3. **Set `PG_MOBILE_BACKEND_URL`** to your API host (e.g. `https://api.parlaygorilla.com`) so the health/odds probe hits the backend, not the frontend.
4. On failure: upload `playwright-report-gate/` and `test-results/mobile-gate/` (screenshots, video, trace) so you can debug.

**Branch protection (recommended):** Require the "Mobile Gate (PROD)" status check to pass before merging to `main`. That way merges only happen when the gate is green, and Render (or any deploy-on-push) will only deploy passing code.

Example (GitHub Actions) — see `.github/workflows/mobile-gate.yml`:

```yaml
- name: Run Mobile Gate (PROD) — must pass
  env:
    CI: true
    PG_E2E_BASE_URL: https://www.parlaygorilla.com
    PG_MOBILE_BACKEND_URL: https://api.parlaygorilla.com   # required for health/odds probe
    PG_MOBILE_TEST_EMAIL: ${{ secrets.PG_MOBILE_TEST_EMAIL }}
    PG_MOBILE_TEST_PASSWORD: ${{ secrets.PG_MOBILE_TEST_PASSWORD }}
  run: npm run test:mobile:gate:ci

- uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: playwright-gate-report
    path: frontend/playwright-report-gate/

- uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: mobile-gate-results
    path: frontend/test-results/mobile-gate
```

## What the gate tests

- **Backend health + odds** (`backend-health.gate.spec.ts`): `GET /health` (200, status healthy/degraded), `GET /health/games` (at least one sport with games with markets). If total games with markets = 0 → fail with message: *Odds provider returned 0 odds; check provider config/rate limit/sport season logic.* Uses `PG_MOBILE_BACKEND_URL` (set in CI to API host).
- **Gorilla Builder** (`gorilla-builder.gate.spec.ts`): **Requires auth.** Cold load (new context). Navigate (with E2E login) → add picks (template) → tap Analyze → assert:
  - **LCP-ish:** time to first skeleton/feedback, spinner visible duration, results visible (tap → results).
  - Tap-to-feedback and cold budgets.
  - API timing, long-task counts.
  **Never skips;** missing creds or Sign In still visible → fail.
- **AI Picks**: Navigate → tap Generate → if paywall appears, skip (do not fail) → else assert same budgets.

Artifacts on failure: screenshot, video, trace (config: `retain-on-failure`). CI uploads `playwright-report-gate` and `test-results/mobile-gate`.

## Config

- Gate config: `frontend/playwright.mobile-gate.config.ts`
- Test dir: `frontend/tests/e2e/mobile-gate/`
- Projects: iPhone 14, Pixel 7 (Chromium)
- Timeouts: test 60s, expect 10s, navigation 45s
- Retries: 2 in CI, 0 locally
