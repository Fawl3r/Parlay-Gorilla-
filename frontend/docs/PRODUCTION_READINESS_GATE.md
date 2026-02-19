# PG — Production Readiness Gate (Frontend Conversion/Retention/Monetization)

**Role:** PG_ReleaseCaptain  
**Scope:** Frontend-only. No backend changes.  
**Status:** Completed.

---

## Phase 1 — Static Audit

### A) SSR Safety

| File | window/document/localStorage/sessionStorage | Status |
|------|--------------------------------------------|--------|
| `lib/retention/RetentionStorage.ts` | All access via `safeJsonParse`/`safeJsonSet` (guard `typeof window === "undefined"`). `recordVisit()` now has top guard. | **Safe** |
| `lib/monetization-timing/intentStorage.ts` | All access via `safeGet`/`safeSet` (guard `typeof window === "undefined"`). | **Safe** |
| `lib/monetization-timing/timingEngine.ts` | All `sessionStorage` use guarded by `typeof window === "undefined"`. | **Safe** |
| `lib/monetization-timing/intentEvents.ts` | `typeof window === "undefined"` return before any log. | **Safe** |
| `components/conversion/*` | No direct storage/window at module top-level; MonetizationTimingSurface uses hooks/state. | **Safe** |
| `app/_components/landing/LandingTodayTopPicksSection.tsx` | No storage; uses `useSubscription()` in client component. | **Safe** |
| `app/analysis/[...slug]/AnalysisPageClient.tsx` | `window.location` only in event handlers (share/copy). | **Safe** |
| `app/app/AppDashboardClient.tsx` | No storage; `recordReturnVisit`/`recordBuilderInteraction` called in `useEffect`. | **Safe** |

**Fix applied:** `RetentionStorage.recordVisit()` — added `if (typeof window === "undefined") return` at function start so it never touches `localStorage` on server.

---

### B) Route Safety

- **`/pricing`** — Exists at `app/pricing/page.tsx`. Build confirms route: `○ /pricing`. No placeholder needed.

---

### C) Premium Gating

- **Helper:** `lib/conversion/premiumGating.ts` — `isPremiumUser(isPremium)`, `isAuthResolved(loading)`, `shouldShowUpgradeSurface(state)`.
- **Gating in place:**
  - **AnalysisPageClient:** `InlineUpgradeCta` and `MonetizationTimingSurface` render only when `!subscriptionLoading && !isPremium`. Limited-analysis line same.
  - **MonetizationTimingSurface:** Accepts `isPremium` and `authResolved`; returns `null` when `isPremium` or `!authResolved`. Effect that sets surface also skips when `isPremium || !authResolved`.
  - **LandingTodayTopPicksSection:** `showLockedOverlay` and upgrade copy/CTA use `showUpgradeUi = !subscriptionLoading && !isPremium`.
- **Tests:** `tests/unit/conversion/premiumGating.test.ts`, `tests/unit/conversion/MonetizationTimingSurface.premium.test.tsx` (premium user and unresolved auth render nothing).

---

### D) Console Logging (Production)

- **`lib/monetization-timing/intentEvents.ts`:**  
  `emitIntentEvent` returns immediately when `process.env.NODE_ENV === "production"` unless `NEXT_PUBLIC_PG_DEBUG_INTENT === "true"`. No production console spam.
- **Test:** `tests/unit/monetization-timing/intentEvents.production.test.ts` — with `NODE_ENV=production`, `console.debug` is not called.

---

## Phase 2 — Runtime Safety (No New API Calls)

- **No new fetch:** No `fetch` in `lib/monetization-timing/*` or `components/conversion/*`. Intent tracking is localStorage/sessionStorage only.
- **Existing network usage (unchanged):**
  - **Landing:** `/api/public/todays-top-picks` (existing).
  - **Analysis detail:** `/api/analysis/{sport}/{slug}/view` (existing POST), plus normal data loading.
  - **Dashboard:** Existing games/analytics/feed APIs.
- **Scroll sentinel:** Uses `IntersectionObserver` only; no API calls.

---

## Phase 3 — Performance & UX

- **Production build:** `npm run build` completes successfully (Next.js 16, Turbopack).
- **Motion:** MonetizationTimingSurface has no motion; conversion components use static layout. Landing motion (e.g. `LandingTodayTopPicksSection`) uses `whileInView` with `once: true` and stable easing — no added spring/bounce from this gate.
- **Layout:** Upgrade surfaces are block-level; no intentional layout shift. Value strip and cards use existing glass styles.

---

## Phase 4 — Tests Added

| Test | Purpose |
|------|--------|
| `tests/unit/retention/RetentionStorage.ssr.test.ts` | SSR: `recordVisit`, `getProgression`, `getStreak`, `getLastResearchAsOf`, `hasViewedSlug`, `getMarketSnapshotEntries` do not throw when `window` is undefined. |
| `tests/unit/monetization-timing/intentEvents.production.test.ts` | Production: `emitIntentEvent` does not call `console.debug` when `NODE_ENV=production`. |
| `tests/unit/conversion/premiumGating.test.ts` | `isPremiumUser`, `isAuthResolved`, `shouldShowUpgradeSurface` behavior. |
| `tests/unit/conversion/MonetizationTimingSurface.premium.test.tsx` | Premium user and unresolved auth: MonetizationTimingSurface renders nothing (no upgrade copy). |

**Run:**  
`cd frontend && npx vitest run tests/unit/retention/RetentionStorage.ssr.test.ts tests/unit/monetization-timing/intentEvents.production.test.ts tests/unit/conversion/premiumGating.test.ts tests/unit/conversion/MonetizationTimingSurface.premium.test.tsx tests/unit/monetization-timing/intentScore.test.ts`

---

## Phase 5 — GO / NO-GO Checklist

### Commands and Expected Results

| Step | Command | Expected |
|------|--------|----------|
| 1 | `cd frontend && npm run lint` | Exit 0; no errors. |
| 2 | `cd frontend && npx vitest run` (or `npm test`) | All tests pass (including new production-readiness tests). |
| 3 | `cd frontend && npm run build` | Build succeeds; `/pricing` and other routes listed. |
| 4 | `cd frontend && npm run start` | Server starts; no hydration errors in console. |

### Manual Clickpath (after `npm run start`)

1. **Landing** — Visit `/`. Blurred picks and upgrade copy only when not premium and subscription resolved. No new network calls beyond existing.
2. **Analysis** — Open any analysis; scroll to bottom. Upgrade surface (if any) appears only after scroll completion and only when not premium and subscription resolved.
3. **Dashboard** — Retention strip and market snapshot; no upgrade prompts for premium.
4. **Premium path** — As premium user: no InlineUpgradeCta, no MonetizationTimingSurface, no blurred overlay on landing picks.
5. **/pricing** — Navigate to `/pricing`. No 404; page loads.

### Network

- No new API calls introduced by conversion/retention/monetization layers.  
- Landing: existing `/api/public/todays-top-picks`.  
- Analysis: existing view POST and data fetches.  
- Dashboard: existing APIs.

### “AI Active” / Pulse

- No change to “AI Active” or pulse behavior from this gate. If present elsewhere, ensure it does not log to console in production (separate from intent events).

### GO Criteria

- [x] Lint passes.  
- [x] All unit tests pass (including SSR, production emit, premium gating).  
- [x] Production build passes.  
- [x] `/pricing` exists and builds.  
- [x] No new fetch in monetization/conversion.  
- [x] Premium users never see upgrade surfaces (gated + tested).  
- [x] Intent events silent in production (code + test).  
- [x] SSR-safe storage access (guards + RetentionStorage test).

**Verdict:** **GO** for deploy of frontend conversion/retention/authority/monetization layers, provided the manual clickpath and `npm run start` check show no hydration or runtime errors in your environment.
