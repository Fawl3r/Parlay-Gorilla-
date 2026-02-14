# Verification: Sports Enable/Disable + Games Rendering

## What was wrong (summary)

- **Sport selectors** used hardcoded sport lists and did not consistently use backend `is_enabled`; some pages (UpcomingGamesTab, AnalysisListClient) did not fetch `/api/sports` at all.
- **Games lists** in CustomParlayBuilder filtered out games with `markets.length === 0`, so scheduled games without odds were hidden.
- **Backend failure** was hidden: `listSports()` returned a hardcoded fallback on error, so the UI never showed "Couldn't reach backend." (Now `listSports()` rethrows; UI shows error and uses **stale-while-error** cache when available.)
- **Option A** (no games today → show next scheduled date) was implemented in `useGamesForSportDate` but the dashboard Games tab did not use `suggestedDate` for the banner or date sync.
- **Inconsistent availability** across AI Picks, Schedule/Analysis, and Parlay Builder: each page derived or fetched sports differently.

## Manual verification checklist

### 1. Sport selectors (all three surfaces)

- [ ] **AI Picks (Parlay Builder)**  
  - Open `/app` → AI Picks tab.  
  - For a sport in OFFSEASON or COMING_SOON (or `is_enabled: false`): the sport chip is disabled, non-clickable, and shows a badge (e.g. "Offseason", "Coming soon").  
  - Select an in-season sport, then (e.g. via backend or mock) set that sport to disabled: selection auto-switches to the first enabled sport.

- [ ] **Game Schedule / Game Analysis**  
  - Open `/analysis` (Game Analysis hub).  
  - Same as above: disabled sports are greyed out and non-clickable with a status label.  
  - Open `/app` → Games tab (Upcoming Games).  
  - Same: sport tabs from backend; disabled sports are disabled with badge.

- [ ] **Gorilla Parlay Builder (Custom)**  
  - Open `/app` → Gorilla Parlay Builder tab.  
  - Sport dropdown/tabs come from backend; disabled sports are not selectable and show status (e.g. "Coming soon", "Offseason").

### 2. Games lists

- [ ] **Schedule / Analysis**  
  - Pick an in-season sport.  
  - If there are no games today but there are games on a future date: the list shows games for the next available date, and a banner appears: "No games today — showing next scheduled games (DATE)."  
  - Scheduled games (no markets yet) are visible; only live/final logic applies (no filter on `markets.length`).

- [ ] **Gorilla Parlay Builder**  
  - Select a sport; games list shows all scheduled/live/final games returned by the API, including games without markets.

### 3. Empty and error states

- [ ] **Backend unreachable**  
  - With backend down or `/api/sports` failing: a clear message appears: "Couldn't reach backend. Try refresh." (no hardcoded fallback list).
  - **Stale-while-error:** If a previous successful load is cached (sessionStorage), sport selectors still show the last known good list and a banner indicates backend unreachable; optional subtext: "Showing last saved sports list."

- [ ] **Games fetch fails**  
  - Message: "Couldn't load games. Try refresh."  
  - Do **not** show "Failed to load" when the fetch actually succeeded and the list is just empty.

- [ ] **Games fetch succeeds, no games**  
  - Message: "No games scheduled." with backend status label if applicable (e.g. offseason).

### 4. Consistency

- [ ] One shared **sports availability** source: `useSportsAvailability()` used on AI Picks, Game Analysis, Upcoming Games, Analysis List, and both Parlay Builders.
- [ ] One **games** hook: `useGamesForSportDate`; no requirement for markets; Option A (suggestedDate) used where "today" has no games.
- [ ] One **date** helper: `isGameOnDate(start_time, selectedDateStr)` from `gamesDateUtils` used for filtering.

## How to run tests

**Unit tests:**
```bash
cd frontend
npm run test:unit -- --run tests/unit/ui/GameAnalysisHubClientTabs.test.tsx tests/unit/games/gamesDateUtils.test.ts
```

**E2E (Playwright) — sports availability + scheduled games + stale-while-error:**
```bash
cd frontend
npx playwright test tests/e2e/sports-availability-and-games.spec.ts --project=chromium
```
Covers: disabled sports non-clickable on Analysis and Parlay Builder; scheduled games with empty markets render; Option A banner when today has no games; stale cache shows last good sports list and error banner when `/api/sports` fails after a prior success.

## Stale-while-error behavior

- **Cache:** Last successful `/api/sports` response is stored in sessionStorage (key `pg_sports_availability_cache_v1`) and in-memory.
- **When `/api/sports` fails:** The UI shows "Couldn't reach backend. Try refresh." and, if cached data exists, sport selectors continue to show the last known good list. Optional subtext: "Showing last saved sports list."
- **When no cache exists and the request fails:** Sports list is empty and only the error message is shown.

## Files changed (reference)

- **New:** `frontend/lib/sports/useSportsAvailability.ts` — shared hook for `/api/sports`, `isSportEnabled`, `getSportBadge`, stale-while-error cache.
- **New:** `frontend/lib/sports/sportsAvailabilityCache.ts` — sessionStorage + in-memory cache for last good sports list.
- **New:** `frontend/tests/e2e/sports-availability-and-games.spec.ts` — E2E: disabled sports, scheduled games, Option A banner, stale cache.
- **New:** `frontend/docs/VERIFICATION_SPORTS_AND_GAMES.md` — this checklist.
- **Modified:** `frontend/lib/api/services/GamesApi.ts` — `listSports()` throws on failure (no fallback).
- **Modified:** `frontend/components/games/gamesConfig.ts` — added `SPORT_ICONS`.
- **Modified:** `frontend/app/analysis/GameAnalysisHubClient.tsx` — uses hook, backend sports list, error message for games.
- **Modified:** `frontend/app/app/_components/tabs/UpcomingGamesTab.tsx` — uses hook, suggestedDate banner and date sync, error/empty states.
- **Modified:** `frontend/app/analysis/AnalysisListClient.tsx` — uses hook, backend sports, disabled state.
- **Modified:** `frontend/components/parlay-builder/ParlayBuilder.tsx` — uses hook, disables sport chips, auto-switch.
- **Modified:** `frontend/components/custom-parlay/CustomParlayBuilder.tsx` — uses hook, removed markets filter, `gamesData.games`, error message.
- **Modified:** `frontend/app/sports/page.tsx` — error state when `listSports` fails.
- **Modified:** `frontend/tests/unit/ui/GameAnalysisHubClientTabs.test.tsx` — tests updated for `SportsUiPolicy` and `emptyStateContextLine`.
