# Sport Availability System — Canonical Spec

This document is the **single source of truth** for fully automated sport availability in Parlay Gorilla. The system must be hands-off, data-driven, and future-proof. No manual season toggles; all behavior is derived from game windows, policies, and coming-soon overrides.

---

## Core Principles (Non-Negotiable)

- **`is_enabled`** is the single source of truth for whether a sport can be interacted with anywhere in the app. **`in_season`** is legacy and may only be used as a fallback when `is_enabled` is missing.
- The **backend** owns all availability and visibility decisions; the **frontend** never decides seasonality.
- **No manual toggles.** All enable/disable behavior must be derived from:
  - Game windows (in-season, preseason, break)
  - Preseason thresholds
  - Postseason detection
  - Break detection
  - Coming-soon overrides
- **Cadence-based sports** (NFL, NBA, MLB, NHL, NCAAF, NCAAB, etc.) follow season cadence logic. **Event-based sports** (UFC, Boxing, MMA) use rolling windows (or coming-soon until ready).
- **Every regression** must be caught by CI before merge.

---

## Sport States (Backend)

**Allowed values:** `OFFSEASON`, `PRESEASON`, `IN_SEASON`, `IN_BREAK`, `POSTSEASON`.

The sport state engine lives in the backend and uses **per-sport policies** (see `sport_state_service`, `sport_state_policy`).

- **Cadence sports:** In-season window, preseason window, preseason enable threshold, break detection, postseason detection (e.g. `season_phase == postseason`).
- **Event-based sports:** Rolling windows (e.g. 30/90 days); no hard offseason unless coming-soon.

**State rules:**

| State       | Condition | is_enabled |
|------------|-----------|------------|
| IN_SEASON  | Upcoming games in short in-season window | true |
| PRESEASON  | Outside in-season but next game in preseason window | true only when `days_to_next <= preseason_enable_days` |
| IN_BREAK   | Recent games but no upcoming in in-season window | false |
| OFFSEASON  | No recent games and next game far away or missing | false |
| POSTSEASON | Upcoming games with `season_phase == postseason` | true |

**Payload:** Every sport state payload must include at least: `sport_state`, `is_enabled`, `next_game_at`, `days_to_next`, `preseason_enable_days`, `state_reason`, and policy metadata where applicable.

---

## Visibility & Coming-Soon (Backend-Owned)

- **Backend** defines `HIDDEN_SPORT_SLUGS` and `COMING_SOON_SPORT_SLUGS` (in `sports_config`). Hidden sports **never** appear in API responses. Coming-soon sports **appear** but are **always disabled**.
- **Coming-soon override** (applied in backend before response) **MUST** set:
  - `is_enabled` = false
  - `sport_state` = `"OFFSEASON"`
  - `state_reason` = `"coming_soon_override"`
  - `in_season` = false
  - `status_label` = `"Coming Soon"`
- Frontend must **never** override this; it only consumes the API.

---

## API Contracts

### `GET /api/sports`

For every **visible** sport, must return at least:

- **Required:** `slug` (string), `sport_state` (string), `is_enabled` (boolean).
- **Optional:** `next_game_at`, `days_to_next`, `preseason_enable_days`, `state_reason`, `status_label`, etc.

### `GET /ops/sport-state/{sport}`

- Exposes full decision inputs for debugging.
- Requires `OPS_DEBUG_ENABLED` and optional `X-Ops-Token`.
- Must return no-store headers; never cached.

### `GET /ops/availability-contract`

- Validates the availability contract: required fields present, correct types, no duplicate slugs (case-insensitive), valid `sport_state` values.
- Requires `OPS_DEBUG_ENABLED` and optional token.
- Returns `ok: true` when valid; `ok: false` with `issues` when invalid.
- Ops routes must always return **no-store** headers and must **never** be cached.

---

## CI Enforcement

- **Script:** `scripts/check_availability_contract.py` must be run in CI against a **live** backend instance with `OPS_DEBUG_ENABLED=true`.
- **CI must NOT set** `ALLOW_OPS_DISABLED`. If the endpoint is missing or contract is broken, CI must fail.
- **Flow:** CI spins up Postgres and Redis → runs migrations → starts the API → runs the contract check.
- The job may start as **report-only** (`continue-on-error: true`) but must be made **blocking** once stable (see VERIFICATION_PRODUCTION_CHECKLIST and workflow comments).

---

## Frontend Rules (Strict)

**Availability derivation (everywhere):**

```ts
isEnabled = typeof sport.is_enabled === "boolean" ? sport.is_enabled : (sport.in_season !== false)
```

- **Tabs and buttons:** Disabled when `isEnabled === false`; must not be clickable.
- If the **currently selected sport** becomes disabled, the UI must **automatically switch** to the first enabled sport.
- All sport keys (slug, tab id, lookups) must be **normalized to lowercase**.
- **Empty-state messaging** must be driven **solely** by backend metadata:
  - `OFFSEASON` → “Out of season — returns {date}”
  - `PRESEASON` locked → “Preseason starts {date} — unlocks in X days”
  - `PRESEASON` enabled → “Preseason — next game {date}”
  - `IN_BREAK` → “League break — next game {date}”

---

## Forbidden

- Manual toggles for season/availability
- Hardcoded season dates
- UI-side season logic (backend is source of truth)
- Enabling based on `in_season` alone (use `is_enabled` first)
- Ignoring `is_enabled`
- Caching any `/ops` route
- Adding new sports without CI contract validation

---

## Acceptance Checklist

- [ ] NFL/NCAAF in February are OFFSEASON and disabled; tabs are visibly disabled and non-clickable.
- [ ] Preseason auto-enables within the threshold (e.g. when `days_to_next <= preseason_enable_days`).
- [ ] Coming-soon sports never enable.
- [ ] `GET /ops/availability-contract` passes when backend is healthy.
- [ ] CI fails on any contract violation (once the job is blocking).

---

## Final Directive

This system must **never require manual intervention**. If a sport enables or disables incorrectly, the fix belongs in:

1. **Backend** sport state logic  
2. **Backend** visibility config (`HIDDEN_SPORT_SLUGS`, `COMING_SOON_SPORT_SLUGS`, `apply_sport_visibility_overrides`)  
3. **CI** contract enforcement  

— **never** in the UI.

---

## Related Docs

- [VERIFICATION_PRODUCTION_CHECKLIST.md](./VERIFICATION_PRODUCTION_CHECKLIST.md) — Ops curl, when to make CI blocking, optional nightly staging.
- [season_handling.md](./season_handling.md) — Legacy season-state and resolver context; canonical behavior is this document.
