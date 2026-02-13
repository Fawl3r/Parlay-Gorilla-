# PG_PicksEngine

**Mission:** Make parlay generation accurate, season-aware, and resistant to "not enough games" false failures.

## Non-Negotiables

- Never duplicate pick logic; reuse existing selectors/filters/scorers.
- Season awareness: in-season vs out-of-season per sport; graceful degradation (exclude or switch leagues only if supported).
- "Not enough games" resilience: log pool size per filter step, structured reason which filter removed games, fallback to less strict tier when allowed.

## Required Flow

1. **Repo scan** — locate pick pipeline (filters, scoring, selection, constraints).
2. **Trace game pool:** raw → post-filter → post-constraints → final.
3. **Minimal fixes** — improve filtering clarity; add deterministic fallback tiers.
4. **Regression test** — test that fails before fix and passes after.

## Output Format

1. **Pipeline map** (files + symbols)
2. **Root cause hypothesis** with counts
3. **Patch** (files + code)
4. **Test + verification**
