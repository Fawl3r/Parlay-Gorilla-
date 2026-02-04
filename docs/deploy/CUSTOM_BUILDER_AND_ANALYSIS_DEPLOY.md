# Custom Builder + Game Analysis Detail — Deploy & Verification

## Merge + deploy order (clean + low risk)

1. **Merge Commit 4** (analysis-detail data_quality + badges) first.
2. **Deploy backend + frontend together** (same release window).
   - Backward-safe: badges only show when `data_quality.roster` / `data_quality.injuries` exist; old responses show nothing new.
   - You still want both sides live so good/bad pages behave as designed.

---

## Commit 4 — Post-deploy: 10-minute verification

### 1) Validate the API contract (2 pages)

| Page | Expectation |
|------|-------------|
| **Good** (e.g. NFL in-season game) | Key Players + Availability render; **no badges**. |
| **Bad** (e.g. NBA with no adapter, or any page that used to show dead modules) | Modules hidden; **badges**: "Fetching…" (spinner) if `missing`, "Limited…" (no spinner) if `stale`. |

### 2) Confirm backend emits new fields

In Render logs, find one analysis request and confirm the JSON includes:

- `ugie_v2.data_quality.roster`
- `ugie_v2.data_quality.injuries`

Use `request_id` (if you log it) to match frontend → backend.

### 3) Watch for silent failure (badges stuck on “Fetching…”)

- **Risk:** Backend sets `roster`/`injuries` to `missing` forever and never flips to `ready` → no crash, but UX smell.
- **Check:** Refresh the same (bad) page after 30–60 seconds. Confirm **at least some** pages eventually show Key Players / Availability or "Limited…" (i.e. something flips to `ready` or `stale`).
- **If nothing flips:** Plan the optional follow-up below (non-blocking refresh + data_quality update). Don’t block Commit 4 on it.

### Next high-ROI step (after Commit 4 is proven in prod)

**“Non-blocking refresh on detail view”** — so badges feel alive without new background jobs:

- On analysis detail request: return response **immediately** (current behavior).
- Kick off a **lightweight async task** to refresh roster/injuries for that matchup.
- Set `data_quality` to `missing`/`stale` in the initial response; **update in DB** when refresh completes.
- Then “Fetching roster…” / “Limited injury data” actually mean “we’re working on it.”

Do **not** implement this until Commit 4 is proven in production.

---

## Feature flags (when ready)

Backend flags live in `backend/app/core/config.py`. Env vars:

- `FEATURE_COUNTER_TICKET=true` — enable Counter Ticket (hedge) in Custom Builder
- `FEATURE_COVERAGE_PACK=true` — enable Coverage Pack

**Rollout:** Turn on Counter first, then Coverage. Rollback = set to `false`.

See root `.env.example` for commented examples.

---

## Load-slip mapping (verify before flipping flags)

Builder "Load slip" maps backend `HedgePick.market_type` to frontend builder markets:

| Backend (`HedgePick.market_type`) | Frontend builder |
|-----------------------------------|------------------|
| `h2h`, `moneyline`                | h2h (moneyline)  |
| `spread`, `spreads`               | spreads         |
| `total`, `totals`                 | totals          |

- Backend hedge engine normalizes to: `h2h` \| `moneyline` \| `spread` \| `total` (see `backend/app/schemas/custom_builder_hedge.py`).
- Frontend `CustomParlayBuilder.tsx` uses `marketTypeMap` to map all of these to `h2h` / `spreads` / `totals` for the slip.
- If the backend ever returns `market_type="totals"`, the map already includes `totals` → `totals`. No change needed unless you add new market types.

---

## Post-deploy checklist

1. **Game Analysis detail (dead modules)**
   - Open a Game Analysis detail page with known missing roster data.
   - Key Players and Availability should **not** render (no dead "Roster unavailable" / "Unable to assess" block).

2. **AI parlay + candidate legs**
   - Generate an AI parlay once.
   - If candidate legs = 0, check the new breakdown counts in logs:
     - `games_with_odds = 0` → ingestion/cache
     - `games_with_odds > 0` but h2h/spreads/totals = 0 → market mapping / normalizer
     - `rejected_below_confidence` large → thresholds or model scoring

3. **Builder: Counter/Coverage with 1 pick**
   - With flags still off: Counter/Coverage should show guardrail copy (no API call).

4. **After flipping `FEATURE_COUNTER_TICKET=true`**
   - Generate counter ticket → "Load slip" → Analyze should work.
   - If "Load slip" fails for some games, confirm backend `market_type` matches the map above (moneyline→h2h, spread→spreads, total→totals).
