# Custom Builder + Game Analysis Detail — Deploy & Verification

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
