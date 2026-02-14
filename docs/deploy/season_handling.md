# Out-of-Season Sport Logic

This document describes legacy/resolver context for how Parlay Gorilla detects out-of-season sports and prevents AI parlay generation, empty-game errors, and unnecessary API calls for inactive sports.

**Canonical spec:** For the full, non-negotiable sport availability system (is_enabled as source of truth, backend-owned visibility, CI enforcement, frontend rules), see **[SPORT_AVAILABILITY_SYSTEM.md](./SPORT_AVAILABILITY_SYSTEM.md)**.

---

## Failure Modes

- **AI parlay generation for unavailable sports:** Users select a sport with no upcoming games (e.g. NFL in July), leading to confusing "no candidates" or heavy fallback logic.
- **Empty-game errors:** APIs or UI show errors when the game pool is empty for that sport.
- **Wasted API calls:** Odds or games APIs are called for sports that are clearly off season.

---

## Guardrails

### Season state (existing)

- **SeasonStateService** computes and caches per-sport state using game counts in time windows:
  - **IN_SEASON:** Has scheduled games in the near window (e.g. next 10 days).
  - **PRESEASON:** No near games but has games in a wider window (e.g. next 30 days).
  - **POSTSEASON:** NFL-specific (week ≥ 19); other sports use same count-based logic.
  - **OFF_SEASON:** No upcoming scheduled games in the lookahead window.
- Cache TTL: 1 hour (`SEASON_STATE_TTL_SECONDS`). Stored in `sport_season_state` table.

### Central resolver

- **SportAvailabilityResolver** (new) is the single place that answers: “Is this sport available for parlay generation?”
- It uses **SeasonStateService.get_season_state(sport)**. If **OFF_SEASON**, it returns `available=False` and a **user-safe message**.
- If the season state call fails (DB/cache error), the resolver returns `available=True` so we do not block users on infrastructure issues.

### Where it is used

- **ParlayBuilderService.build_parlay()** calls the resolver at the start. If the sport is not available, it raises **InsufficientCandidatesException** with the resolver’s message. The API then returns a 409 (or appropriate) response with that message; no odds or candidate loading runs for that sport.

---

## Required Behavior (Checklist)

- [x] Detect if a sport is **OUT OF SEASON** (via existing SeasonStateService).
- [x] **Prevent AI parlay generation** for unavailable sports (resolver + exception in builder).
- [x] **Show user-safe fallback messaging** (resolver message in exception).
- [x] **Avoid empty-game errors** by failing fast before loading candidates.
- [x] **Skip API calls** for inactive sports (builder exits before odds/candidate loading).
- [x] **Centralized “sport availability resolver”** (SportAvailabilityResolver).
- [x] **Clear logs** when a sport is skipped intentionally (logger.info in builder and resolver).

---

## Logging

- When a sport is skipped because it is off season:
  - **SportAvailabilityResolver:** `"SportAvailabilityResolver: sport X is OFF_SEASON; skipping parlay generation intentionally"`.
  - **ParlayBuilderService:** `"Parlay build skipped: sport X is off_season; user message: ..."`.
- Season state computation is already logged via `log_event(..., "season_state.compute", ...)` in SeasonStateService.

---

## Preseason / Playoffs

- **PRESEASON:** When there are no games in the “near” window (e.g. next 10 days) but there are games in the “post” window (e.g. next 30 days), state is PRESEASON. So NFL preseason, MLB spring training, and early tournament phases (e.g. NCAA) that have scheduled games in the lookahead are **not** OFF_SEASON and are **available** for parlay generation.
- **POSTSEASON:** NFL week ≥ 19 → POSTSEASON; other sports use the same count-based logic. POSTSEASON is available.
- Only **OFF_SEASON** (no near and no post scheduled games) is blocked.

## Safety override

- **SPORT_FORCE_AVAILABLE:** Env var (or config) comma-separated list of sports to treat as available even when OFF_SEASON. Example: `SPORT_FORCE_AVAILABLE=MLB,NFL`. Use for emergencies or when heuristics lag (e.g. new season not yet in DB).

## Configuration

- Season windows and TTL are in **SeasonStateService** (`RECENT_FINAL_DAYS`, `NEAR_SCHEDULED_DAYS`, `POST_SCHEDULED_DAYS`, `SEASON_STATE_TTL_SECONDS`). Adjust there if you need different heuristics.
- **SPORT_FORCE_AVAILABLE** (optional): comma-separated sport codes to force-available.
