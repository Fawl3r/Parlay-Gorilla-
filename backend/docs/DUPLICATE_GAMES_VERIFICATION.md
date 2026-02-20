# Duplicate Games Fix — Rollout Verification

Use this checklist when deploying the canonical-key dedupe fix (migration 059 + backend/frontend changes).

## Pre-deploy

1. **Run targeted tests**
   ```bash
   cd backend && python -m pytest tests/test_games_deduplication.py tests/test_odds_fetcher_espn_fallback.py tests/test_odds_api_data_store_soccer_draw.py -v
   cd frontend && npm test -- --testPathPattern="GameDeduper|GameListDeduplication" --run
   ```

2. **Staging: run migration**
   ```bash
   cd backend && alembic upgrade head
   ```

3. **Staging: verify duplicate count is zero** (after migration)
   ```sql
   -- Expect 0 rows if migration cleaned all duplicates
   SELECT canonical_match_key, count(*) AS cnt
   FROM games
   WHERE canonical_match_key IS NOT NULL
   GROUP BY canonical_match_key
   HAVING count(*) > 1;
   ```

## Deploy order

1. Deploy backend (code + migration 059).
2. Run migration: `alembic upgrade head`.
3. Deploy frontend (GamesApi dedupe safety net).

## Post-deploy

1. **Duplicate count**
   - Re-run the SQL above; expect 0 duplicate groups.

2. **APIs**
   - `GET /api/sports/{sport}/games?refresh=true` — no duplicate matchup/time in response.
   - `GET /api/games/feed?window=today` — no duplicate matchup/time in response.

3. **UI**
   - Dashboard and game table views show one row per matchup/time.
