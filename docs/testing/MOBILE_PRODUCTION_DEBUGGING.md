# Mobile Production Debugging With Cursor

## Purpose

Enable Cursor to **detect, reason about, and fix mobile-only production issues** using **real mobile emulator artifacts** (screenshots, DOM, console, network) from the **live production site**.

- **Playwright = Eyes** (captures layout, traces, screenshots).
- **Cursor = Brain** (reasons from artifacts and proposes fixes).

## One-Time Setup

Playwright is already installed. Ensure browsers are installed:

```bash
cd frontend
npx playwright install --with-deps
```

## Folder Structure

```
frontend/
  playwright.mobile.config.ts      # Mobile regression (iPhone 14, Pixel 7, iPhone SE)
  playwright.mobile-prod.config.ts  # Legacy single-project mobile prod
  tests/mobile/
    helpers/
      urls.ts      # Prod routes
      wait.ts     # gotoAndStabilize + age-gate bypass
      selectors.ts # data-testid / data-page selectors + fallbacks
    prod/
      gorilla-builder.spec.ts   # Gorilla Parlay Builder regression
      ai-picks.spec.ts          # AI Picks regression
      pwa-install-cta.spec.ts   # PWA install CTA visibility (no overlap)
```

**Page-loaded markers:** Key routes expose `data-page="..."` (e.g. `custom-builder`, `ai-builder`, `games`) so tests can assert “page loaded” without guessing from text. Key UI uses `data-testid` (e.g. `custom-builder-page`, `parlay-slip`, `get-ai-analysis-btn`, `parlay-breakdown-modal`, `pwa-install-cta`).

Artifacts: `frontend/test-results/mobile/` (screenshots, video, trace on failure). HTML report: `frontend/playwright-report/`.

## Running Mobile Tests Against Production

**Recommended — full mobile regression suite (iPhone 14 + Pixel 7):**

```bash
cd frontend
npm run test:mobile
```

Other commands:

```bash
npm run test:mobile:headed   # Run with browser visible
npm run test:mobile:ui        # Playwright UI mode
npm run test:mobile:report    # Open last HTML report
```

Single spec or project:

```bash
npx playwright test tests/mobile/prod/gorilla-builder.spec.ts -c playwright.mobile.config.ts --project=mobile-iphone-14
```

Legacy (single-project) config:

```bash
npm run test:e2e:mobile-prod
```

Artifacts produced:

- `artifacts/mobile-builder.png` (Gorilla Builder)
- `artifacts/mobile-ai-picks.png` (AI Picks)
- Video and trace on first retry (in `artifacts/playwright/`).

## Cursor Debug Loop (Mandatory)

When a mobile issue occurs:

1. **Paste into Cursor:**
   - Screenshot (e.g. `artifacts/mobile-builder.png`)
   - Console errors (if any)
   - Network failure (Copy as cURL if relevant)
   - The test file that failed
   - Short description: expected vs actual

2. **Cursor will:**
   - Identify layout / CSS / logic issue
   - Propose a minimal fix
   - Modify code
   - Ask you to re-run Playwright
   - Confirm green

This is the only supported mobile debugging loop.

## High-ROI Regressions Covered

- **Gorilla Parlay Builder:** sticky CTA overlap, Analyze button off-screen, slip overflow, paywall modal scroll, safe-area, template button wrap.
- **AI Picks:** Install CTA overlap, copy overflow, quick actions clipped, error cards hidden, fallback banners off-screen.

## Production Safety

- Tests are **read-only** (no destructive actions).
- No auth-required routes in the default specs unless using test accounts.
- Never mutate prod data; only navigate, click, inspect.

## Test account / test mode (recommended for bulletproof suite)

If the mobile suite needs to **hit auth-required flows** (e.g. full Gorilla Builder + Get AI Analysis) in CI or locally against prod:

1. **Use a dedicated test account** — Create a real user used only for E2E (e.g. `e2e-mobile@yourdomain.com`). Do **not** use a shared or personal account that might change state.
2. **Env-based credentials** — Store credentials in CI secrets (e.g. `PG_MOBILE_TEST_EMAIL`, `PG_MOBILE_TEST_PASSWORD`) and in local `.env.local` for `npm run test:mobile`. Never commit credentials.
3. **Read-only behavior** — Even with a test account, specs must not create real orders, delete data, or change billing. Use the account only to log in and assert on layout/visibility.
4. **Optional test mode** — If your app supports a “test mode” or feature flag that disables writes or uses a sandbox backend, enable it via env when running mobile tests (e.g. `E2E_TEST_MODE=true`).

Current specs are written to **skip** when the Sign In page is shown, so the suite passes without a test account. Add login steps and remove the skip only when you introduce a dedicated test account and env vars.

## CI

- **Mobile Gate (PROD):** `.github/workflows/mobile-gate.yml` runs on PRs and pushes to `main`. Runs `npm run test:mobile` in `frontend`, uploads `playwright-report` and `test-results/mobile` as artifacts (7-day retention). **Fails the workflow if mobile tests fail** (no continue-on-error).
- **Main CI:** `ci.yml` also has an optional `frontend-mobile-prod` job (continue-on-error) using the legacy config.

## Cursor Role

Cursor is expected to:

- Treat screenshots as source of truth.
- Infer layout bugs from CSS + DOM.
- Propose minimal, production-safe fixes.
- Never guess without artifacts.
- Ask for a Playwright re-run if uncertain.
