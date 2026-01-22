# Implementation Plan - 7-Day Focused Roadmap

## Overview

This plan prioritizes **hardening the core** and **building intelligence moats** that differentiate without adding cost. All work is $0 cost and uses existing infrastructure.

**Total Estimated Time**: 7 days (assuming 1 developer, 6-8 hours/day)

**Strategic Focus**: Build a **decision engine**, not a content site. This framing prevents overbuilding and overspending.

---

## Day 1: Database Performance (High ROI)

### Morning (3-4 hours)

**Task 1.1: Add Missing Database Indexes**
- **Files**: 
  - `backend/app/models/game.py`
  - `backend/app/models/game_analysis.py`
  - `backend/app/models/analysis_page_views.py`
- **Migration**: Create `backend/alembic/versions/033_add_performance_indexes.py`
- **Indexes to Add**:
  ```python
  # games table
  Index("idx_games_sport_time_status", "sport", "start_time", "status")
  
  # game_analyses table
  Index("idx_analyses_game_league", "game_id", "league")
  
  # analysis_page_views table
  Index("idx_views_league_date", "league", "view_bucket_date")
  
  # markets table (if missing)
  Index("idx_markets_game_type", "game_id", "market_type")
  ```
- **Test**: Run `alembic upgrade head`, verify indexes created
- **Expected Impact**: 50-80% faster queries

**Task 1.2: Add Index on Markets Table**
- **File**: `backend/app/models/market.py`
- **Add**: `Index("idx_markets_game_type", "game_id", "market_type")`
- **Test**: Verify index exists after migration

### Afternoon (3-4 hours)

**Task 1.3: Optimize Scheduler Analysis Generation Query**
- **File**: `backend/app/services/scheduler.py` (lines 358-378)
- **Change**: Refactor `_generate_upcoming_analyses()` to use subquery pattern
- **Test**: Run scheduler job manually, verify it's faster
- **Expected Impact**: 40-60% faster scheduler job

**Task 1.4: Add Database Query Timeout**
- **File**: `backend/app/database/session.py`
- **Add**: Connection pool tuning + statement timeout
- **Test**: Verify connections don't hang

---

## Day 2: Core Analysis Performance (High ROI)

### Morning (3-4 hours)

**Task 2.1: Batch External Data Fetches**
- **File**: `backend/app/services/analysis/core_analysis_generator.py`
- **Change**: Refactor `_safe_matchup_data()` to use `asyncio.gather()`
- **Test**: Generate analysis, verify parallel fetching works
- **Expected Impact**: 30-50% faster core generation

**Task 2.2: Cache Team Stats Queries**
- **File**: `backend/app/services/analysis/core_analysis_generator.py`
- **Change**: Prefetch both teams in single batch
- **Test**: Verify stats are fetched in parallel

### Afternoon (3-4 hours)

**Task 2.3: Add Request-Scoped Caching**
- **File**: `backend/app/services/analysis/core_analysis_generator.py`
- **Change**: Add `_request_cache` to prevent duplicate fetches
- **Test**: Verify same data isn't fetched twice in one request

**Task 2.4: Add Staleness Indicators**
- **File**: `backend/app/services/analysis/core_analysis_generator.py`
- **Change**: Add `data_freshness` to `generation.metrics`
- **Test**: Verify freshness data is included in response

---

## Day 3: Odds & Market Performance (Medium ROI)

### Morning (3-4 hours)

**Task 3.1: Optimize Odds Snapshot Builder**
- **File**: `backend/app/services/odds_snapshot_builder.py`
- **Change**: Single-pass aggregation instead of multiple iterations
- **Test**: Verify snapshot building is faster

**Task 3.2: Batch Save Operations in Odds Data Store**
- **File**: `backend/app/services/odds_api/odds_api_data_store.py`
- **Change**: Use `db.add_all()` for bulk inserts
- **Test**: Verify odds storage is faster

### Afternoon (3-4 hours)

**Task 3.3: Add Query Result Caching for Game Lists**
- **File**: `backend/app/services/odds_fetcher.py`
- **Change**: Add 1-minute in-memory cache for `get_or_fetch_games()`
- **Test**: Verify repeated requests use cache

**Task 3.4: Cache Probability Calculations**
- **File**: `backend/app/services/model_win_probability.py`
- **Change**: Add in-memory cache with game_id + odds_hash key
- **Test**: Verify probabilities are cached

---

## Day 4: Observability & Logging (Medium ROI)

### Morning (3-4 hours)

**Task 4.1: Add Structured Logging**
- **Files**: All service files using `print()`
- **Priority Files**:
  - `backend/app/services/analysis/core_analysis_generator.py`
  - `backend/app/services/analysis/analysis_orchestrator.py`
  - `backend/app/services/odds_fetcher.py`
  - `backend/app/services/scheduler.py`
- **Change**: Replace `print()` with `logger.error()`, `logger.info()`, etc.
- **Test**: Verify logs are structured and searchable

**Task 4.2: Add Request ID Tracking**
- **File**: `backend/app/middleware/request_id.py` (new)
- **Change**: Add middleware to track request IDs
- **Test**: Verify request IDs appear in logs and response headers

### Afternoon (3-4 hours)

**Task 4.3: Add Health Check Endpoint**
- **File**: `backend/app/api/routes/health.py` (extend existing)
- **Change**: Add `/health/detailed` endpoint with external API checks
- **Test**: Verify health checks work

**Task 4.4: Add Graceful Degradation Logging**
- **File**: `backend/app/services/odds_api/distributed_odds_api_cache.py`
- **Change**: Add structured logging when Redis is unavailable
- **Test**: Verify logs are clear when Redis fails

---

## Day 5: Intelligence Upgrades - Part 1 (High Impact)

### Morning (3-4 hours)

**Task 5.1: Add "What Changed" Delta Summaries**
- **File**: `backend/app/services/analysis/core_analysis_generator.py`
- **Change**: Add `generate_delta_summary()` method
- **Logic**: Compare current vs previous analysis (line movement, injuries)
- **Store**: In `analysis_content.delta_summary` (array of strings)
- **Test**: Verify deltas are generated correctly

**Task 5.2: Add Template-Based NLG for Explanations**
- **File**: `backend/app/services/analysis/explanation_generator.py` (new)
- **Change**: Create template-based explanation generator
- **Templates**: Spread pick, total pick, edge explanations
- **Test**: Verify explanations are data-driven and engaging

### Afternoon (3-4 hours)

**Task 5.3: Add Structured Data (JSON-LD) for SEO**
- **File**: `backend/app/services/analysis/core_analysis_generator.py`
- **Change**: Add `build_structured_data()` method
- **Store**: In `analysis_content.seo_metadata.structured_data`
- **Test**: Verify JSON-LD is valid (use Google's Rich Results Test)

**Task 5.4: Enhance Confidence Breakdown with Trends**
- **File**: `backend/app/services/analysis/builders/confidence_breakdown_builder.py`
- **Change**: Add `confidence_trend` (increasing/decreasing/stable)
- **Store**: In `analysis_content.confidence_breakdown.confidence_trend`
- **Test**: Verify trends are calculated correctly

---

## Day 6: Intelligence Upgrades - Part 2 (High Impact)

### Morning (3-4 hours)

**Task 6.1: Add Sharp Money Indicator**
- **File**: `backend/app/services/analysis/builders/market_disagreement_builder.py`
- **Change**: Detect sharp vs public book splits
- **Logic**: Compare Pinnacle/Circa odds vs FanDuel/DraftKings
- **Store**: In `analysis_content.market_disagreement.sharp_indicator`
- **Test**: Verify sharp indicators are accurate

**Task 6.2: Add Prop Value Score (EV)**
- **File**: `backend/app/services/analysis/builders/prop_recommendations_builder.py`
- **Change**: Calculate expected value for each prop
- **Store**: In `analysis_content.prop_recommendations.top_props[].ev_score`
- **Test**: Verify EV calculations are correct

### Afternoon (3-4 hours)

**Task 6.3: Add Correlation Matrix for Same-Game Parlays**
- **File**: `backend/app/services/analysis/builders/portfolio_guidance_builder.py`
- **Change**: Calculate correlation between legs
- **Store**: In `analysis_content.portfolio_guidance.correlation_warnings`
- **Test**: Verify correlations are calculated correctly

**Task 6.4: Add Model Calibration Tracking**
- **File**: `backend/app/services/model_win_probability.py`
- **Change**: Track prediction accuracy in `model_predictions` table
- **Test**: Verify predictions are tracked

---

## Day 7: Product Loop (Simple & Focused)

### Morning (3-4 hours)

**Task 7.1: Add "Watchlist" for Games (Simplified)**
- **Files**:
  - `backend/app/models/watched_game.py` (new)
  - `backend/app/api/routes/games.py` (add endpoints)
  - `backend/alembic/versions/034_add_watched_games.py` (new)
- **Endpoints**:
  - `POST /api/games/{game_id}/watch`
  - `DELETE /api/games/{game_id}/watch`
  - `GET /api/user/watchlist`
- **Scope**: **ONLY** saved games. No alerts, no schedulers, no notifications.
- **Purpose**: Faster access, personal relevance, future monetization hook
- **Test**: Verify watchlist works end-to-end

**Task 7.2: Add "Daily Top Edges" Feed**
- **File**: `backend/app/api/routes/analytics/top_edges.py` (new)
- **Endpoint**: `GET /api/analytics/top-edges?sport=nfl&limit=10`
- **Logic**: Query `game_analyses` for high-confidence edges (using `confidence_breakdown.confidence_total` and model vs market edge)
- **Test**: Verify top edges are returned correctly

### Afternoon (3-4 hours)

**Task 7.3: Ensure Page View Tracking is Complete**
- **Status**: Already implemented in `analysis_page_views` table and `POST /api/analysis/{sport}/{slug}/view` endpoint
- **Verify**: Frontend is firing view events correctly
- **Test**: Confirm page views are being tracked for traffic ranking

**Task 7.4: Frontend Integration for Watchlist & Top Edges**
- **Files**:
  - `frontend/components/games/WatchButton.tsx` (new)
  - `frontend/app/user/watchlist/page.tsx` (new)
  - `frontend/app/analytics/top-edges/page.tsx` (new)
- **Integration**: Add watch button to analysis pages
- **Test**: Verify all UI works end-to-end

---

## Day 6: Props (Traffic-Gated) - COMPLETE

**Status**: ✅ Already implemented in previous work
- `PropRecommendationsBuilder` exists
- `TrafficRanker` gates props to top 5 games by traffic
- `FetchBudgetManager` limits props fetches to 6h TTL
- `build_props_snapshot()` in `OddsSnapshotBuilder` exists

**Verification Tasks** (1-2 hours):
- Verify props are only generated for top-traffic games
- Verify fetch budget is respected
- Test props recommendations with real data

---

## Frontend Integration (Day 7 Afternoon, continued)

**Task 7.5: Add UI Components for New Analysis Features**
- **Files**:
  - `frontend/components/analysis/OutcomePathsCard.tsx` (new)
  - `frontend/components/analysis/ConfidenceBreakdownMeter.tsx` (new)
  - `frontend/components/analysis/MarketDisagreementBadge.tsx` (new)
  - `frontend/components/analysis/PortfolioGuidancePanel.tsx` (new)
  - `frontend/components/analysis/PropsPanel.tsx` (new)
- **Integration**: Add to `frontend/app/analysis/[...slug]/AnalysisPageClient.tsx`
- **Test**: Verify all components render correctly

**Task 7.6: Add Delta Summary Display**
- **File**: `frontend/components/analysis/DeltaSummary.tsx` (new)
- **Display**: Show "What Changed" section at top of analysis
- **Test**: Verify deltas are displayed

---

## DEFERRED (Post-Traction Phase)

### ❌ Backtesting & Calibration (DEFERRED)
- **Reason**: Not enough volume yet, results will be statistically noisy
- **When**: After you have 1000+ predictions with outcomes
- **Includes**: Model weight adjustment, Brier scores, calibration curves, outcome path history

### ❌ User Session Tracking (DEFERRED)
- **Reason**: Page views + repeat visits are enough for now
- **When**: After you have clear product-market fit
- **Includes**: Session tables, page unload tracking, session analytics

### ❌ Line Alerts Job (DEFERRED)
- **Reason**: Polling every 15 minutes scales badly, creates expectations
- **When**: After users explicitly ask for alerts
- **Includes**: Line alert tables, polling job, notification system

---

## Risk Mitigation

### Database Migrations
- **Risk**: Migrations may fail in production
- **Mitigation**: Test all migrations in staging first, have rollback plan

### Performance Regressions
- **Risk**: Changes may slow down system
- **Mitigation**: Benchmark before/after, monitor p50/p95 latencies

### Breaking Changes
- **Risk**: API changes may break frontend
- **Mitigation**: All changes are additive (new fields only), maintain backward compatibility

### External API Failures
- **Risk**: Changes may increase external API calls
- **Mitigation**: All changes respect existing fetch budgets and caching

---

## Success Metrics

### Performance
- **Target**: 30-50% faster analysis generation
- **Target**: 50-80% faster database queries
- **Target**: p95 latency < 5s (currently ~8s)

### User Engagement
- **Target**: 20-30% increase in repeat visits (via alerts + top edges)
- **Target**: 10-15% increase in time on page (via better explanations)

### SEO
- **Target**: 15-25% improvement in search rankings (structured data)
- **Target**: Rich snippets in Google search results

### Cost
- **Target**: $0 additional infrastructure costs
- **Target**: No increase in external API usage (via better caching)

---

## Dependencies

### Required
- PostgreSQL database (already exists)
- Alembic for migrations (already exists)
- Redis (optional, but recommended for production)

### Optional
- pgvector extension (for Gorilla Bot vector search, already exists if using)

---

## Rollout Plan

### Phase 1: HARDEN CORE (Days 1-3)
- **Deploy**: Database indexes, query optimizations, fetch caps, structured logging
- **Monitor**: Query times, analysis generation times, external API usage
- **Rollback**: If performance degrades, revert migrations
- **Why**: Protects from surprise API spend, slow p95s, outages on traffic spikes

### Phase 2: INTELLIGENCE MOAT (Days 4-5)
- **Deploy**: Outcome Paths, Confidence Breakdown, Market Disagreement, Sharp/Public signals, Portfolio Guidance, Delta summaries
- **Monitor**: Analysis quality, SEO rankings, user engagement
- **Rollback**: If features break, disable via feature flags
- **Why**: This is your competitive edge vs Covers/Action/Rotowire

### Phase 3: PROPS (Day 6)
- **Deploy**: Props recommendations (already implemented, verify)
- **Monitor**: Props generation rate, traffic ranking accuracy
- **Rollback**: If props cause issues, disable via feature flag
- **Why**: Traffic-gated props add value without cost

### Phase 4: PRODUCT LOOP (Day 7)
- **Deploy**: Watchlist, Top Edges feed, page view tracking verification
- **Monitor**: User engagement, retention
- **Rollback**: If features cause issues, disable endpoints
- **Why**: Simple retention hooks without complexity

---

## Post-Implementation

### Week 1 After Launch
- Monitor performance metrics daily (p50/p95 latencies, query times)
- Review error logs for new issues
- Verify external API usage stays within budgets
- Collect user feedback on new intelligence features

### Week 2 After Launch
- Analyze engagement metrics (repeat visits, watchlist usage, top edges views)
- Review SEO rankings (Google Search Console) - expect 15-25% improvement
- Verify structured data (JSON-LD) appears in search results
- Optimize based on data

### Month 1 After Launch
- Full performance audit (before/after benchmarks)
- User survey on new features (especially intelligence moat features)
- Plan next iteration based on results
- **Decision Point**: Re-evaluate deferred features (backtesting, alerts) based on traction

---

## Strategic Notes

### What You're Building
**A decision engine, not a content site.**

This framing ensures:
- ✅ You won't overbuild
- ✅ You won't overspend
- ✅ You'll monetize at the right time

### What This Leaves You With

After 7 days, you will have:
- ✅ A faster system (30-50% improvement)
- ✅ A safer system (fetch caps, graceful degradation)
- ✅ A smarter system (intelligence moat features)
- ✅ A system that:
  - Explains why (confidence breakdown, outcome paths)
  - Shows risk (portfolio guidance, correlation warnings)
  - Adapts to traffic (props gating)
  - Costs $0 extra

**A platform that feels institutional, not "AI blog"**

This is exactly where you want to be before monetization.

---

## Notes

- All tasks are designed to be independent (can be done in parallel if multiple developers)
- All changes are backward-compatible (additive only)
- All external API usage respects existing fetch budgets
- All database changes are additive (no data loss risk)
