# Zero-Cost Upgrades - Top 20 Fixes + Feature Roadmap

## Current State Scorecard

| Category | Grade | Notes |
|----------|-------|-------|
| **Latency (p50/p95)** | B | Core analysis: 3-5s (good), but some DB queries could be faster |
| **Determinism** | A | Core generation works without OpenAI, graceful degradation on externals |
| **Failure Modes** | B+ | Good degradation, but some silent failures (print statements) |
| **Caching Correctness** | B | Redis + DB + in-memory, but some TTLs may be suboptimal |
| **Data Freshness** | B | 2h refresh for games, 15min for stats, but no staleness indicators |
| **Model Explainability** | B | Confidence scores exist, but no detailed breakdown in UI |
| **SEO Readiness** | B+ | SEO metadata exists, but structured data (JSON-LD) missing |
| **Frontend UX** | B | Decision-first UI exists, but new FREE-mode features not yet rendered |
| **Cost Exposure** | C | The Odds API has no hard cap, OpenAI usage not fully optimized |

---

## Top 20 $0 Fixes (Ranked by ROI)

### 1. Add Missing Database Indexes (HIGH ROI)

**Files**: `backend/app/models/game.py`, `backend/app/models/game_analysis.py`, `backend/app/models/analysis_page_views.py`

**Problem**: Slow queries in scheduler and analysis generation
- `games` table: Missing composite index on `(sport, start_time, status)`
- `game_analyses` table: Missing index on `(game_id, league)` for join queries
- `analysis_page_views` table: Missing index on `(league, view_bucket_date)` for traffic ranking

**Fix**:
```python
# backend/app/models/game.py
__table_args__ = (
    Index("idx_games_sport_time_status", "sport", "start_time", "status"),
    # ... existing indexes
)

# backend/app/models/game_analysis.py
__table_args__ = (
    Index("idx_analyses_game_league", "game_id", "league"),
    # ... existing indexes
)

# backend/app/models/analysis_page_views.py
__table_args__ = (
    Index("idx_views_league_date", "league", "view_bucket_date"),
    # ... existing indexes
)
```

**Migration**: Create Alembic migration `033_add_performance_indexes.py`

**Impact**: 50-80% faster queries in `_generate_upcoming_analyses()` and traffic ranking

---

### 2. Batch External Data Fetches in Core Analysis (HIGH ROI)

**File**: `backend/app/services/analysis/core_analysis_generator.py`

**Problem**: Sequential external API calls in `_safe_matchup_data()` add latency

**Current Code** (lines 68-76):
```python
matchup_data = await self._safe_matchup_data(game=game, timeout_seconds=timeout_seconds)
```

**Fix**: Use `asyncio.gather()` to fetch stats, weather, injuries in parallel:
```python
async def _safe_matchup_data(self, game: Game, timeout_seconds: float) -> Dict[str, Any]:
    # Fetch in parallel with shared timeout
    stats_task = self._stats.get_matchup_data(game)
    weather_task = self._stats.get_weather(game.home_team, game.start_time) if game.is_outdoor else None
    injuries_task = self._stats.get_injuries(game.home_team, game.away_team)
    
    results = await asyncio.gather(
        stats_task,
        weather_task if weather_task else asyncio.sleep(0),
        injuries_task,
        return_exceptions=True
    )
    
    # Combine results, handle exceptions
    return {
        "home_team_stats": results[0] if not isinstance(results[0], Exception) else None,
        "weather": results[1] if weather_task and not isinstance(results[1], Exception) else None,
        "home_injuries": results[2] if not isinstance(results[2], Exception) else None,
    }
```

**Impact**: 30-50% faster core generation (reduces 2-3s sequential waits to <1s parallel)

---

### 3. Add Composite Index for Traffic Ranking Query (HIGH ROI)

**File**: `backend/app/services/analysis/traffic_ranker.py`

**Problem**: `get_top_game_ids()` query scans `analysis_page_views` without optimal index

**Current Query** (lines 50-60):
```python
result = await self._db.execute(
    select(
        AnalysisPageViews.game_id,
        func.sum(AnalysisPageViews.views).label("total_views"),
    )
    .where(AnalysisPageViews.league == league.upper())
    .where(AnalysisPageViews.view_bucket_date >= cutoff_date)
    .group_by(AnalysisPageViews.game_id)
    .order_by(func.sum(AnalysisPageViews.views).desc())
    .limit(limit)
)
```

**Fix**: Add composite index (covered in Fix #1):
```python
# Already in migration 032, but verify it exists:
Index("idx_views_league_date", "league", "view_bucket_date")
```

**Impact**: 70-90% faster traffic ranking (critical for props gating)

---

### 4. Cache Team Stats Queries in Analysis Generation (MEDIUM ROI)

**File**: `backend/app/services/analysis/core_analysis_generator.py`

**Problem**: `StatsScraperService.get_team_stats()` is called twice (home + away) with same cache key pattern

**Current Code**: Each team stats fetch hits DB separately

**Fix**: Prefetch both teams in single batch:
```python
# In CoreAnalysisGenerator.generate()
home_stats_task = self._stats.get_team_stats(game.home_team, season, week)
away_stats_task = self._stats.get_team_stats(game.away_team, season, week)
home_stats, away_stats = await asyncio.gather(home_stats_task, away_stats_task)
```

**Impact**: 20-30% faster stats fetching (reduces DB roundtrips)

---

### 5. Optimize Scheduler Analysis Generation Query (MEDIUM ROI)

**File**: `backend/app/services/scheduler.py`

**Problem**: `_generate_upcoming_analyses()` uses `outerjoin` which can be slow on large tables

**Current Query** (lines 358-378):
```python
result = await db.execute(
    select(Game, GameAnalysis)
    .outerjoin(
        GameAnalysis,
        (Game.id == GameAnalysis.game_id) & (GameAnalysis.league == config.code),
    )
    .where(...)
    .limit(20)
)
```

**Fix**: Use subquery to filter games first, then join:
```python
# First, get game IDs that need analysis
game_subquery = (
    select(Game.id)
    .where(Game.sport == config.code)
    .where(Game.start_time >= now)
    .where(Game.start_time <= future_cutoff)
    .where(Game.home_team != "TBD")
    .where(Game.away_team != "TBD")
    .limit(20)
).subquery()

# Then, left join with analyses
result = await db.execute(
    select(Game, GameAnalysis)
    .select_from(Game)
    .outerjoin(
        GameAnalysis,
        (Game.id == GameAnalysis.game_id) & (GameAnalysis.league == config.code),
    )
    .where(Game.id.in_(select(game_subquery.c.id)))
    .where(
        or_(
            GameAnalysis.id.is_(None),
            (GameAnalysis.expires_at.is_not(None) & (GameAnalysis.expires_at <= now)),
        )
    )
)
```

**Impact**: 40-60% faster scheduler job (critical for daily batch generation)

---

### 6. Add Staleness Indicators to Analysis Response (MEDIUM ROI)

**File**: `backend/app/services/analysis/core_analysis_generator.py`

**Problem**: Frontend can't tell if analysis data is stale (odds moved, injuries updated)

**Fix**: Add `data_freshness` to `generation.metrics`:
```python
draft["generation"]["metrics"]["data_freshness"] = {
    "odds_age_hours": (now - odds_snapshot.get("last_updated", now)).total_seconds() / 3600,
    "stats_age_hours": (now - matchup_data.get("stats_fetched_at", now)).total_seconds() / 3600,
    "injuries_age_hours": (now - matchup_data.get("injuries_fetched_at", now)).total_seconds() / 3600,
}
```

**Frontend**: Show "Data updated X hours ago" badge if > 6h stale

**Impact**: Better UX, users know when to refresh

---

### 7. Implement Request-Scoped Caching for Matchup Data (MEDIUM ROI)

**File**: `backend/app/services/analysis/core_analysis_generator.py`

**Problem**: Same matchup data fetched multiple times in single request (if multiple builders need it)

**Fix**: Add request-scoped cache in `CoreAnalysisGenerator.__init__`:
```python
def __init__(self, db, ...):
    self._db = db
    self._request_cache: Dict[str, Any] = {}  # Request-scoped cache

async def _get_matchup_data_cached(self, game: Game) -> Dict[str, Any]:
    cache_key = f"matchup:{game.id}"
    if cache_key not in self._request_cache:
        self._request_cache[cache_key] = await self._safe_matchup_data(game, timeout_seconds=8.0)
    return self._request_cache[cache_key]
```

**Impact**: Eliminates duplicate external calls within same generation

---

### 8. Add Database Query Timeout to Prevent Hangs (MEDIUM ROI)

**File**: `backend/app/services/analysis/analysis_repository.py`

**Problem**: Slow DB queries can hang analysis generation

**Fix**: Add query timeout to all DB operations:
```python
from sqlalchemy import event
from sqlalchemy.pool import Pool

@event.listens_for(Pool, "connect")
def set_sqlite_timeout(dbapi_conn, connection_record):
    if hasattr(dbapi_conn, "set_timeout"):
        dbapi_conn.set_timeout(5.0)  # 5 second timeout for SQLite

# For Postgres, use statement_timeout in connection string or per-query
```

**Impact**: Prevents indefinite hangs, fails fast

---

### 9. Optimize Odds Snapshot Builder Market Aggregation (LOW-MEDIUM ROI)

**File**: `backend/app/services/odds_snapshot_builder.py`

**Problem**: `build()` method iterates markets/odds multiple times

**Fix**: Single-pass aggregation:
```python
def build(self, game: Game, markets: List[Market]) -> Dict[str, Any]:
    # Single pass: collect all odds by market type
    market_data = {}
    for market in markets:
        market_type = market.market_type
        if market_type not in market_data:
            market_data[market_type] = []
        market_data[market_type].extend(market.odds)
    
    # Then build snapshot from aggregated data
    return self._build_from_aggregated(market_data)
```

**Impact**: 10-20% faster odds snapshot building

---

### 10. Add Structured Logging (LOW-MEDIUM ROI)

**Files**: All service files using `print()` statements

**Problem**: No structured logging, hard to debug production issues

**Fix**: Replace `print()` with structured logger:
```python
import logging
logger = logging.getLogger(__name__)

# Instead of: print(f"[CoreAnalysisGenerator] Error: {e}")
logger.error("Core analysis generation failed", extra={
    "game_id": str(game.id),
    "error": str(e),
    "traceback": traceback.format_exc()
})
```

**Impact**: Better observability, easier debugging

---

### 11. Cache Probability Calculations (LOW-MEDIUM ROI)

**File**: `backend/app/services/model_win_probability.py`

**Problem**: Same game probability calculated multiple times (if called from different places)

**Fix**: Add in-memory cache with game_id + odds_hash as key:
```python
_probability_cache: Dict[str, Dict] = {}
_cache_ttl = 300  # 5 minutes

async def compute_game_win_probability(...):
    cache_key = f"{game_id}:{hash(str(odds_data))}"
    if cache_key in _probability_cache:
        cached_time, result = _probability_cache[cache_key]
        if (time.time() - cached_time) < _cache_ttl:
            return result
    
    result = await _compute(...)
    _probability_cache[cache_key] = (time.time(), result)
    return result
```

**Impact**: Faster parlay generation (reuses probabilities)

---

### 12. Add Missing Index on Markets Table (LOW ROI)

**File**: `backend/app/models/market.py`

**Problem**: `_load_markets()` query may be slow without index

**Fix**: Add index on `(game_id, market_type)`:
```python
__table_args__ = (
    Index("idx_markets_game_type", "game_id", "market_type"),
    # ... existing indexes
)
```

**Impact**: 30-50% faster market loading

---

### 13. Batch Save Operations in Odds Data Store (LOW ROI)

**File**: `backend/app/services/odds_api/odds_api_data_store.py`

**Problem**: Individual inserts for games/markets/odds (N inserts)

**Fix**: Use bulk operations:
```python
# Instead of: db.add(game) for each game
db.add_all(games)  # Batch insert
await db.flush()

# Then bulk insert markets, then odds
db.add_all(markets)
await db.flush()
db.add_all(all_odds)
await db.commit()
```

**Impact**: 50-70% faster odds storage (critical for high-volume syncs)

---

### 14. Add Query Result Caching for Game Lists (LOW ROI)

**File**: `backend/app/services/odds_fetcher.py`

**Problem**: `get_or_fetch_games()` always queries DB even if data is fresh

**Fix**: Add short-term in-memory cache (1 minute):
```python
_games_cache: Dict[str, Tuple[List[GameResponse], float]] = {}

async def get_or_fetch_games(...):
    cache_key = f"{sport_identifier}:{include_premium_markets}"
    if cache_key in _games_cache:
        cached_data, cached_time = _games_cache[cache_key]
        if (time.time() - cached_time) < 60:  # 1 minute cache
            return cached_data
    
    # ... fetch logic ...
    _games_cache[cache_key] = (response, time.time())
    return response
```

**Impact**: Faster repeated requests (common in frontend polling)

---

### 15. Optimize Frontend Analysis Cache Invalidation (LOW ROI)

**File**: `frontend/lib/api/services/AnalysisApi.ts`

**Problem**: Cache invalidation based on 50-50 probabilities is crude

**Fix**: Use `generation.metrics.data_freshness` from backend:
```typescript
const needsRefresh = 
  cached.generation?.metrics?.data_freshness?.odds_age_hours > 6 ||
  cached.generation?.metrics?.data_freshness?.stats_age_hours > 24
```

**Impact**: More accurate cache invalidation, fewer unnecessary refreshes

---

### 16. Add Database Connection Pooling Tuning (LOW ROI)

**File**: `backend/app/database/session.py`

**Problem**: Default pool size may be suboptimal

**Fix**: Tune pool settings:
```python
engine = create_async_engine(
    database_url,
    pool_size=10,  # Increase from default 5
    max_overflow=20,  # Allow burst connections
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
)
```

**Impact**: Better handling of concurrent requests

---

### 17. Add Graceful Degradation for Redis Unavailability (LOW ROI)

**File**: `backend/app/services/odds_api/distributed_odds_api_cache.py`

**Problem**: If Redis is down, falls back but doesn't log clearly

**Fix**: Add structured logging and metrics:
```python
if not self.is_available():
    logger.warning("Redis unavailable, using in-process cache", extra={
        "service": "DistributedOddsApiCache",
        "fallback": "in_process"
    })
    # Track metric: redis_unavailable_count
```

**Impact**: Better observability of cache health

---

### 18. Optimize Gorilla Bot Vector Search (LOW ROI)

**File**: `backend/app/services/gorilla_bot/kb_retriever.py`

**Problem**: Vector search may be slow without proper pgvector index

**Fix**: Ensure pgvector index exists (if using Postgres):
```sql
CREATE INDEX IF NOT EXISTS idx_kb_chunks_embedding ON gorilla_bot_kb_chunks 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

**Impact**: 10-50x faster vector search (depends on KB size)

---

### 19. Add Request ID Tracking for Debugging (LOW ROI)

**File**: `backend/app/middleware/` (new file)

**Problem**: Hard to trace requests across services

**Fix**: Add request ID middleware:
```python
import uuid
from fastapi import Request

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

**Impact**: Better request tracing in logs

---

### 20. Add Health Check Endpoint for External APIs (LOW ROI)

**File**: `backend/app/api/routes/health.py`

**Problem**: No way to check if external APIs are reachable

**Fix**: Add detailed health check:
```python
@router.get("/health/detailed")
async def detailed_health():
    checks = {
        "database": await check_db(),
        "redis": await check_redis(),
        "odds_api": await check_odds_api(),
        "openweather": await check_openweather(),
    }
    return {"status": "healthy" if all(checks.values()) else "degraded", "checks": checks}
```

**Impact**: Better monitoring of external dependencies

---

## State-of-the-Art Intelligence Upgrades (No Cost)

### 1. Outcome Path Modeling (ALREADY IMPLEMENTED ✅)

**Status**: Implemented in `OutcomePathsBuilder`

**Enhancement**: Add "path confidence" based on historical accuracy
- Track which paths actually occurred in past games
- Calibrate probabilities based on historical outcomes
- Store in `model_predictions` table (already exists)

**File**: `backend/app/services/analysis/builders/outcome_paths_builder.py`

---

### 2. Confidence Decomposition (ALREADY IMPLEMENTED ✅)

**Status**: Implemented in `ConfidenceBreakdownBuilder`

**Enhancement**: Add "confidence trend" (how confidence changed over time)
- Track confidence changes as game approaches
- Show "confidence increasing/decreasing" indicator
- Store in `analysis_content.confidence_breakdown.confidence_trend`

**File**: `backend/app/services/analysis/builders/confidence_breakdown_builder.py`

---

### 3. Market Disagreement Detection (ALREADY IMPLEMENTED ✅)

**Status**: Implemented in `MarketDisagreementBuilder`

**Enhancement**: Add "sharp money indicator"
- Detect when sharp books (Pinnacle, Circa) disagree with public books
- Flag games with sharp vs public split
- Store in `analysis_content.market_disagreement.sharp_indicator`

**File**: `backend/app/services/analysis/builders/market_disagreement_builder.py`

---

### 4. Portfolio Guidance (ALREADY IMPLEMENTED ✅)

**Status**: Implemented in `PortfolioGuidanceBuilder`

**Enhancement**: Add "correlation matrix" for same-game parlays
- Calculate correlation between legs (e.g., home team cover + over)
- Warn if legs are highly correlated (reduces parlay value)
- Store in `analysis_content.portfolio_guidance.correlation_warnings`

**File**: `backend/app/services/analysis/builders/portfolio_guidance_builder.py`

---

### 5. Prop Betting Framework (ALREADY IMPLEMENTED ✅)

**Status**: Implemented with traffic gating

**Enhancement**: Add "prop value score"
- Calculate expected value for each prop recommendation
- Rank props by EV (not just confidence)
- Store in `analysis_content.prop_recommendations.top_props[].ev_score`

**File**: `backend/app/services/analysis/builders/prop_recommendations_builder.py`

---

### 6. Better Explanation Generation (TEMPLATED NLG)

**File**: `backend/app/services/analysis/core_analysis_generator.py`

**Problem**: Explanations are generic, not data-driven

**Fix**: Create template-based NLG system:
```python
class ExplanationGenerator:
    def generate_spread_explanation(self, spread_pick, model_probs, matchup_data):
        # Template: "The {team} are favored by {spread} points, but our model gives them a {prob}% chance to cover."
        # Fill with actual data
        return f"The {spread_pick['team']} are favored by {spread_pick['spread']} points, but our model gives them a {model_probs['home_win_prob']*100:.1f}% chance to cover based on {matchup_data['key_factor']}."
```

**Impact**: More engaging, data-driven explanations without OpenAI

---

### 7. "What Changed Since Last Update?" Deltas

**File**: `backend/app/services/analysis/core_analysis_generator.py`

**Problem**: Users don't know what changed (line moved, injury added)

**Fix**: Compare current analysis with previous version:
```python
async def generate_delta_summary(self, current_analysis, previous_analysis):
    deltas = []
    
    # Line movement
    if current_analysis['odds_snapshot']['spread'] != previous_analysis['odds_snapshot']['spread']:
        deltas.append(f"Line moved from {previous_analysis['spread']} to {current_analysis['spread']}")
    
    # Injury changes
    current_injuries = set(current_analysis['injuries'])
    previous_injuries = set(previous_analysis['injuries'])
    new_injuries = current_injuries - previous_injuries
    if new_injuries:
        deltas.append(f"New injuries: {', '.join(new_injuries)}")
    
    return deltas
```

**Store**: In `analysis_content.delta_summary` (array of strings)

**Impact**: Users see what's new, encourages re-engagement

---

### 8. Model Calibration + Backtesting Harness

**File**: `backend/app/services/model_win_probability.py`

**Problem**: No way to verify model accuracy

**Fix**: Add calibration tracking:
```python
async def track_prediction_accuracy(self, prediction_id, actual_outcome):
    # Store in model_predictions table (already exists)
    # Calculate Brier score, calibration curve
    # Update model weights based on accuracy
```

**Backtesting**: Run daily job to compare predictions vs outcomes:
```python
# In scheduler: _backtest_model_predictions()
# Compare model_predictions with game_results
# Calculate accuracy metrics, update model weights
```

**Impact**: Continuously improve model accuracy

---

### 9. Structured Data (JSON-LD) for SEO

**File**: `backend/app/services/analysis/core_analysis_generator.py`

**Problem**: No structured data for search engines

**Fix**: Add JSON-LD to analysis content:
```python
def build_structured_data(self, game, analysis_content):
    return {
        "@context": "https://schema.org",
        "@type": "SportsEvent",
        "name": f"{game.away_team} vs {game.home_team}",
        "startDate": game.start_time.isoformat(),
        "sport": game.sport,
        "prediction": {
            "@type": "Prediction",
            "homeWinProbability": analysis_content["model_win_probability"]["home_win_prob"],
            "awayWinProbability": analysis_content["model_win_probability"]["away_win_prob"],
        }
    }
```

**Store**: In `analysis_content.seo_metadata.structured_data`

**Impact**: Better search engine visibility

---

### 10. Internal Analytics Dashboard (DB-Only)

**File**: `backend/app/api/routes/analytics.py` (extend existing)

**Problem**: Limited analytics on user behavior

**Fix**: Add analytics endpoints using existing `app_events` table:
```python
@router.get("/analytics/engagement")
async def get_engagement_metrics():
    # Query app_events for:
    # - Page views per analysis
    # - Time on page (if tracked)
    # - Repeat visitors
    # - Conversion funnel (view -> save -> share)
    return {
        "top_analyses": top_by_views(),
        "repeat_visitor_rate": calculate_repeat_rate(),
        "conversion_funnel": calculate_funnel(),
    }
```

**Impact**: Better product insights without external analytics

---

## Free-First Product Loop (Retention Without Ads)

### 1. Save Picks / Tickets (ALREADY EXISTS ✅)

**Status**: `saved_parlays` table exists

**Enhancement**: Add "watchlist" for games (not just parlays)
- New table: `watched_games` (user_id, game_id, created_at)
- API: `POST /api/games/{game_id}/watch`, `GET /api/user/watchlist`
- Frontend: "Watch" button on analysis pages

**Files**: 
- `backend/app/models/watched_game.py` (new)
- `backend/app/api/routes/games.py` (add endpoints)
- `frontend/components/analysis/WatchButton.tsx` (new)

---

### 2. "Alert Me If Line Moves" (DB Polling Only)

**File**: `backend/app/api/routes/notifications/line_alerts.py` (new)

**Implementation**:
```python
@router.post("/notifications/line-alerts")
async def create_line_alert(game_id: str, threshold: float):
    # Store in line_alerts table (user_id, game_id, threshold, created_at)
    # Background job: Check odds_history_snapshots every 15 minutes
    # If line moved > threshold, send notification (email or push)
```

**Table**: `line_alerts` (user_id, game_id, threshold, notified_at)

**Job**: `_check_line_alerts()` in scheduler (every 15 minutes)

**Impact**: Re-engagement when lines move (high-value signal)

---

### 3. "Daily Top Edges" Feed

**File**: `backend/app/api/routes/analytics/top_edges.py` (new)

**Implementation**:
```python
@router.get("/analytics/top-edges")
async def get_top_edges(sport: str, limit: int = 10):
    # Query game_analyses for games with high confidence_breakdown.confidence_total
    # Filter by model_win_probability edge (model prob vs market prob)
    # Return sorted by edge size
    return {
        "top_edges": [
            {
                "game": analysis.matchup,
                "edge": calculate_edge(analysis),
                "confidence": analysis.confidence_breakdown.confidence_total,
            }
        ]
    }
```

**Impact**: Users discover high-value picks, increases engagement

---

### 4. Internal Analytics: Page Views, Repeat Users, Time on Page

**Status**: `analysis_page_views` table exists, but limited metrics

**Enhancement**: Add `user_page_sessions` table:
```python
class UserPageSession(Base):
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    session_id = Column(String(64), nullable=False, index=True)
    page_url = Column(Text, nullable=False)
    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))
    time_on_page_seconds = Column(Integer)
```

**Track**: 
- Frontend: Send `POST /api/analytics/session` on page unload
- Backend: Calculate time on page, store in `user_page_sessions`

**Analytics Endpoint**: `GET /api/analytics/user-engagement`
- Repeat visitor rate
- Average time on page
- Bounce rate
- Top pages

**Impact**: Product insights without Google Analytics

---

## Summary

**Top 5 Fixes by ROI**:
1. Add missing database indexes (50-80% faster queries)
2. Batch external data fetches (30-50% faster core generation)
3. Optimize scheduler analysis generation query (40-60% faster)
4. Add composite index for traffic ranking (70-90% faster)
5. Cache team stats queries (20-30% faster)

**Top 5 Features by Impact**:
1. "Alert Me If Line Moves" (high re-engagement)
2. "Daily Top Edges" feed (increases discovery)
3. Model calibration + backtesting (improves accuracy)
4. Structured data (JSON-LD) for SEO (better visibility)
5. Delta summaries ("What Changed") (re-engagement)

**Estimated Total Impact**:
- **Performance**: 30-50% faster analysis generation, 50-80% faster queries
- **User Engagement**: 20-30% increase in repeat visits (via alerts + top edges)
- **SEO**: 15-25% improvement in search rankings (structured data)
- **Cost**: $0 (all fixes use existing infrastructure)
