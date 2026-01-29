# System Map - Parlay Gorilla Codebase Audit

## Executive Summary

**Stack**: Next.js (Frontend) + FastAPI (Backend) + PostgreSQL (Database)  
**Architecture**: Monolithic backend with async job scheduler, distributed caching (Redis optional), deterministic core analysis generation  
**External APIs**: The Odds API (odds + primary scheduling), API-Sports (sports data + scheduling fallback), OpenWeather, ESPN (stats fallback), OpenAI (optional polish)  
**Deployment**: Render.com (backend), Vercel (frontend)

---

## 1. Folder Structure

```
F3 Parlay Gorilla/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # 42 route files (181 endpoints)
│   │   ├── models/              # 64 database models
│   │   ├── services/            # Core business logic
│   │   │   ├── analysis/        # Analysis generation pipeline
│   │   │   ├── gorilla_bot/     # Q&A bot with KB
│   │   │   ├── odds_api/        # Odds API integration
│   │   │   ├── scheduler_jobs/  # Background job implementations
│   │   │   └── ...
│   │   ├── workers/             # Background workers
│   │   ├── core/                # Config, dependencies, middleware
│   │   └── database/            # DB session, types
│   ├── alembic/versions/        # 33 migrations
│   ├── scripts/                 # Backfill, utilities
│   └── tests/                   # Pytest test suite
├── frontend/
│   ├── app/                     # Next.js app router
│   │   ├── analysis/            # Analysis detail/list pages
│   │   ├── admin/               # Admin dashboard
│   │   ├── parlays/             # Parlay builder pages
│   │   └── ...
│   ├── components/              # React components (164 files)
│   ├── lib/                     # Utilities, API clients, types
│   └── public/                  # Static assets
└── content_engine/              # Content generation (separate module)
```

---

## 2. Service Map

### Backend Services (Core)

#### Analysis Pipeline
- **`AnalysisOrchestratorService`** (`backend/app/services/analysis/analysis_orchestrator.py`)
  - Entry point: `get_or_generate_for_slug()`, `ensure_core_for_game()`
  - Responsibilities: Slug resolution, cache management, generation coordination
  - Uses: `AnalysisRepository`, `CoreAnalysisGenerator`, `FullArticleJobRunner`

- **`CoreAnalysisGenerator`** (`backend/app/services/analysis/core_analysis_generator.py`)
  - Entry point: `generate(game, timeout_seconds=8.0)`
  - Responsibilities: Fast deterministic analysis (< 8s), picks, trends, edges
  - Dependencies: `StatsScraperService`, `OddsSnapshotBuilder`, `compute_game_win_probability()`
  - New FREE-mode builders: `OutcomePathsBuilder`, `ConfidenceBreakdownBuilder`, `MarketDisagreementBuilder`, `PortfolioGuidanceBuilder`, `PropRecommendationsBuilder`

- **`AnalysisRepository`** (`backend/app/services/analysis/analysis_repository.py`)
  - CRUD for `GameAnalysis` model
  - Methods: `get_by_slug()`, `get_by_game_id()`, `upsert_core()`, `core_lock()`
  - Cache TTL: NFL 48h, others 24h

#### Odds & Markets
- **`OddsFetcherService`** (`backend/app/services/odds_fetcher.py`)
  - Entry point: `fetch_odds_for_sport()`, `get_or_fetch_games()`
  - Caching: Redis distributed cache (48h TTL), in-process rate limiter
  - External: The Odds API (primary + fallback key)

- **`OddsSnapshotBuilder`** (`backend/app/services/odds_snapshot_builder.py`)
  - Methods: `build()`, `build_props_snapshot()`
  - Aggregates spread/total/moneyline from multiple books

- **`OddsHistoryProvider`** (`backend/app/services/odds_history/odds_history_provider.py`)
  - Tracks line movement over time
  - Stores snapshots in `odds_history_snapshots` table

#### Probability & Modeling
- **`compute_game_win_probability()`** (`backend/app/services/model_win_probability.py`)
  - Weighted combination: Market (50%), Stats (30%), Situational (20%)
  - Returns: `home_model_prob`, `away_model_prob`, `ai_confidence`, `calculation_method`

- **`BaseProbabilityEngine`** (`backend/app/services/probability_engine_impl/base_engine.py`)
  - Used by parlay builder for leg probability calculations
  - Prefetch system: `ExternalDataRepository` with concurrency limits

#### Stats & Data
- **`StatsScraperService`** (`backend/app/services/stats_scraper.py`)
  - Methods: `get_team_stats()`, `get_matchup_data()`, `get_weather()`, `get_injuries()`
  - Cache: 15-minute in-memory TTL
  - External: ESPN scraper, OpenWeather API

#### Parlay Generation
- **`ParlayBuilderService`** (`backend/app/services/parlay_builder_impl/parlay_builder_service.py`)
  - Entry point: `build_parlay(num_legs, risk_profile)`
  - Uses: `BaseProbabilityEngine`, `CandidateLegService`

- **`CustomParlayAnalysisService`** (`backend/app/services/custom_parlay_analysis_service.py`)
  - Analyzes user-built parlays
  - Premium-only for player props

#### Background Jobs
- **`BackgroundScheduler`** (`backend/app/services/scheduler.py`)
  - Jobs:
    - Cache cleanup (daily 2 AM)
    - Games refresh (every 2 hours)
    - Analysis generation (daily 6 AM)
    - Odds sync (configurable interval, default 24h)
    - Scraper (daily 1 AM)
    - Game results sync (every 2 hours)
    - Saved parlay resolution (every 6 hours)
    - Arcade points award (every 3 hours)

#### Fetch Budget & Traffic
- **`FetchBudgetManager`** (`backend/app/services/fetch_budget.py`)
  - TTL tracking: DB-first, in-memory fallback
  - TTL defaults: Odds 6h, Weather 24h, Injuries 12h, Props 6h

- **`TrafficRanker`** (`backend/app/services/analysis/traffic_ranker.py`)
  - Ranks games by page views for props gating
  - Cache: 5-minute in-memory TTL

#### Gorilla Bot (Q&A)
- **`GorillaBotManager`** (`backend/app/services/gorilla_bot/gorilla_bot_manager.py`)
  - Entry point: `chat()` method
  - Uses: `GorillaBotKnowledgeRetriever` (vector search), `GorillaBotOpenAIClient`
  - KB: Stored in `gorilla_bot_kb_documents` and `gorilla_bot_kb_chunks` tables

---

## 3. API Routes (42 files, 181 endpoints)

### Analysis Routes
- **`GET /api/analysis/{sport}/{slug}`** (`analysis_detail_routes.py`)
  - Returns: `GameAnalysisResponse` with core content
  - Query params: `refresh` (admin-only)
  
- **`POST /api/analysis/{sport}/{slug}/view`** (`analysis_detail_routes.py`)
  - Increments `analysis_page_views` for traffic ranking

- **`GET /api/analysis`** (`analysis_list_routes.py`)
  - Lists upcoming analyses

- **`GET /api/analysis/feed`** (`analysis_feed.py`)
  - RSS/JSON feed of analyses

### Games Routes
- **`GET /api/games`** (`games.py`)
  - Returns: `List[GameResponse]` with markets/odds
  - Uses: `OddsFetcherService.get_or_fetch_games()`

- **`GET /api/games/{sport}`** (`games_public_routes.py`)
  - Sport-specific game list

### Parlay Routes
- **`POST /api/parlay`** (`parlay.py`)
  - Generates AI parlay: `suggest_parlay(num_legs, risk_profile)`

- **`POST /api/parlay/extended`** (`parlay_extended.py`)
  - Extended parlay with filters

- **`POST /api/parlay/analyze`** (`custom_parlay.py`)
  - Analyzes custom parlay (premium-only for props)

### User & Auth Routes
- **`POST /api/auth/register`**, **`POST /api/auth/login`** (`auth.py`)
- **`GET /api/user/me`**, **`PUT /api/user/me`** (`user.py`)
- **`GET /api/profile`**, **`PUT /api/profile`** (`profile.py`)

### Subscription & Billing
- **`GET /api/subscription`**, **`POST /api/subscription`** (`subscription.py`)
- **`POST /api/billing/stripe/checkout`** (`billing/stripe_checkout_routes.py`)
- **`POST /api/webhooks/stripe`** (`webhooks/stripe_webhook_routes.py`)

### Admin Routes
- **`GET /api/admin/users`**, **`PUT /api/admin/users/{id}`** (`admin/users.py`)
- **`GET /api/admin/metrics`** (`admin/metrics.py`)
- **`GET /api/admin/logs`** (`admin/logs.py`)

### Other Routes
- **`GET /api/health`** (`health.py`)
- **`GET /api/sports`** (`sports.py`)
- **`GET /api/leaderboards`** (`leaderboards.py`)
- **`POST /api/gorilla-bot/chat`** (`gorilla_bot.py`)

---

## 4. Database Schema (64 Models)

### Core Game Data
- **`games`**: Game info (teams, start_time, status, sport)
  - Indexes: `idx_games_sport_time`, `idx_games_status`
  
- **`markets`**: Market definitions (spread, total, moneyline, player_props)
  - Foreign key: `game_id`
  
- **`odds`**: Odds prices per market/book
  - Foreign keys: `market_id`, `book` (string)
  - Indexes: `idx_odds_market_id`, `idx_odds_book`

- **`game_analyses`**: Analysis content (JSON), metadata, SEO
  - Foreign keys: `game_id`, `league`
  - Indexes: `idx_analyses_game_id`, `idx_analyses_slug`, `idx_analyses_league`

### Stats & Results
- **`team_stats`**: Season/week stats, ATS/O/U trends
  - Indexes: `idx_team_stats_team_season`, `idx_team_stats_season_week`

- **`game_results`**: Final scores, outcomes
  - Foreign key: `game_id`
  - Indexes: `idx_game_results_game_id`, `idx_game_results_sport_date`

- **`odds_history_snapshots`**: Historical odds for line movement
  - Foreign key: `game_id`
  - Indexes: `idx_odds_history_game_time`

### User & Subscription
- **`users`**: User accounts, plans, subscription status
  - Indexes: `idx_user_email`, `idx_user_account_number`, `idx_user_plan`

- **`subscriptions`**: Subscription records
  - Foreign key: `user_id`
  - Indexes: `idx_subscriptions_user_id`, `idx_subscriptions_status`

- **`payments`**: Payment transactions
  - Foreign keys: `user_id`, `subscription_id`
  - Indexes: `idx_payments_user_id`, `idx_payments_status`

### Parlays & Saved Picks
- **`parlays`**: Generated parlay definitions
  - Indexes: `idx_parlays_user_id`, `idx_parlays_created_at`

- **`saved_parlays`**: User-saved parlays
  - Foreign keys: `user_id`, `parlay_id`
  - Indexes: `idx_saved_parlays_user_id`, `idx_saved_parlays_status`

- **`parlay_results`**: Parlay outcomes
  - Foreign key: `parlay_id`

### Analytics & Tracking
- **`app_events`**: Generic analytics events
  - Indexes: `idx_app_events_type_date`, `idx_app_events_user_date`

- **`analysis_page_views`**: Page view tracking (for props gating)
  - Foreign keys: `analysis_id`, `game_id`
  - Indexes: `idx_analysis_page_views_analysis_id`, `uq_analysis_page_views_analysis_date`

- **`fetch_budget_tracking`**: External API fetch TTL tracking
  - Indexes: `ix_fetch_budget_tracking_fetch_key`, `ix_fetch_budget_tracking_last_fetched`

### Verification & Badges
- **`verification_records`**: On-chain verification proofs
  - Indexes: `idx_verification_records_user_created`, `unique_verification_records_parlay_fingerprint`

- **`user_badges`**: User badge assignments
  - Foreign keys: `user_id`, `badge_id`

### Affiliate System
- **`affiliates`**: Affiliate accounts
- **`affiliate_commissions`**: Commission tracking
- **`affiliate_payouts`**: Payout records

### Gorilla Bot
- **`gorilla_bot_conversations`**: Chat sessions
- **`gorilla_bot_messages`**: Chat messages
- **`gorilla_bot_kb_documents`**: Knowledge base documents
- **`gorilla_bot_kb_chunks`**: Vector-embedded chunks

---

## 5. Data Flow Maps

### Analysis Generation Flow

```
User Request: GET /api/analysis/nfl/bears-vs-packers-week-14
    │
    ├─> AnalysisOrchestrator.get_or_generate_for_slug()
    │   │
    │   ├─> AnalysisRepository.get_by_slug()
    │   │   └─> If cached & core ready: Return immediately
    │   │
    │   ├─> AnalysisSlugResolver.find_game()
    │   │   └─> Query games table by slug pattern
    │   │
    │   ├─> Acquire per-game lock (AnalysisRepository.core_lock())
    │   │
    │   └─> CoreAnalysisGenerator.generate()
    │       │
    │       ├─> Load markets (selectinload Markets + Odds)
    │       ├─> OddsSnapshotBuilder.build()
    │       ├─> OddsHistoryProvider.get_line_movement()
    │       │
    │       ├─> StatsScraperService.get_matchup_data()
    │       │   ├─> get_team_stats() [DB query + 15min cache]
    │       │   ├─> get_weather() [OpenWeather API + 15min cache]
    │       │   └─> get_injuries() [ESPN scraper + 15min cache]
    │       │
    │       ├─> compute_game_win_probability()
    │       │   └─> Weighted combination: Market (50%) + Stats (30%) + Situational (20%)
    │       │
    │       ├─> CorePickBuilders.build_spread_pick()
    │       ├─> CorePickBuilders.build_total_pick()
    │       ├─> CoreAnalysisEdgesBuilder.build()
    │       │
    │       ├─> FREE-mode builders (NEW):
    │       │   ├─> OutcomePathsBuilder.build()
    │       │   ├─> ConfidenceBreakdownBuilder.build()
    │       │   ├─> MarketDisagreementBuilder.build()
    │       │   ├─> PortfolioGuidanceBuilder.build()
    │       │   └─> PropRecommendationsBuilder.build() [traffic-gated]
    │       │
    │       └─> AnalysisAiWriter.polish_core_copy() [optional, 4s timeout]
    │
    ├─> AnalysisRepository.upsert_core()
    │   └─> Store in game_analyses table (JSON content)
    │
    └─> FullArticleJobRunner.enqueue() [background, async]
        └─> FullArticleGenerator.generate() [OpenAI GPT-4o-mini, 90s timeout]
```

### Odds Fetching Flow

```
Request: GET /api/games?sport=nfl
    │
    ├─> OddsFetcherService.get_or_fetch_games()
    │   │
    │   ├─> Check DB cache (games with markets/odds)
    │   │   └─> If fresh (< 2h old): Return immediately
    │   │
    │   └─> fetch_odds_for_sport()
    │       │
    │       ├─> DistributedOddsApiCache.get_or_fetch()
    │       │   └─> Redis cache (48h TTL) [if available]
    │       │
    │       ├─> Rate limiter (in-process, 1 call per 10s)
    │       │
    │       ├─> TheOddsApiClient.get_current_odds()
    │       │   └─> HTTP GET https://api.the-odds-api.com/v4/sports/{sport}/odds
    │       │
    │       ├─> OddsApiDataStore.store_games()
    │       │   └─> Upsert games, markets, odds tables
    │       │
    │       └─> GameResponseConverter.to_response()
    │           └─> Transform to API response format
```

### Parlay Generation Flow

```
Request: POST /api/parlay?num_legs=5&risk_profile=balanced
    │
    ├─> ParlayBuilderService.build_parlay()
    │   │
    │   ├─> BaseProbabilityEngine.initialize()
    │   │   └─> ExternalDataRepository.prefetch_for_games()
    │   │       ├─> Batch fetch team stats (concurrency: 8)
    │   │       ├─> Batch fetch injuries (concurrency: 8)
    │   │       └─> Batch fetch weather (concurrency: 8)
    │   │
    │   ├─> CandidateLegService.get_candidate_legs()
    │   │   └─> Query games (limit: 50), load markets/odds
    │   │
    │   ├─> ProbabilityEngine.calculate_leg_probability()
    │   │   └─> For each leg: compute win probability
    │   │
    │   └─> ParlayBuilderService.select_legs()
    │       └─> Filter by confidence, build parlay
    │
    └─> Return ParlayResponse
```

### Background Job Flow

```
Scheduler (APScheduler, leader-elected via Redis)
    │
    ├─> Daily 6 AM: _generate_upcoming_analyses()
    │   └─> For each sport: Query upcoming games (next 7 days)
    │       └─> AnalysisOrchestrator.ensure_core_for_game()
    │
    ├─> Every 2h: _refresh_games()
    │   └─> OddsFetcherService.get_or_fetch_games() [force_refresh=False]
    │
    ├─> Configurable: _sync_odds()
    │   └─> OddsSyncWorker.sync_all_sports()
    │
    ├─> Daily 1 AM: _run_scraper()
    │   └─> ScraperWorker.run_full_scrape()
    │       └─> Update team_stats, injuries
    │
    └─> Every 2h: _sync_game_results()
        └─> GameResultsSyncJob.run()
            └─> ESPN API → game_results table
```

---

## 6. External API Calls & Caching

### The Odds API
- **Service**: `TheOddsApiClient` (`backend/app/services/the_odds_api_client.py`)
- **Caching**: 
  - Redis distributed cache: 48h TTL (`DistributedOddsApiCache`)
  - In-process rate limiter: 1 call per 10s (`OddsApiRateLimiter`)
- **Usage**: Primary for **odds** and **scheduling** (games list); fallback key supported
- **Cost Risk**: HIGH (credits-based pricing, no hard cap in code)

### OpenWeather API
- **Service**: `StatsScraperService.get_weather()`
- **Caching**: 15-minute in-memory cache
- **Usage**: Weather conditions for outdoor games
- **Cost Risk**: LOW (free tier: 1000 calls/day)

### API-Sports
- **Service**: `ApiSportsClient` (`backend/app/services/apisports/client.py`), `SportsRefreshService`, `SportsDataRepository`
- **Caching**: DB-first (apisports_fixtures, apisports_standings, etc.); quota 100/day
- **Usage**: Primary **sports data** (stats, results, form, standings); **scheduling fallback** when The Odds API does not have schedule data
- **Cost Risk**: LOW (quota-managed, 100 requests/day free tier)

### OpenAI API
- **Service**: `OpenAIService` (`backend/app/services/openai_service.py`)
- **Usage**: 
  - Core analysis polish (optional, 4s timeout)
  - Full article generation (background, 90s timeout)
  - Gorilla Bot chat (30s timeout)
- **Caching**: None (deterministic prompts, but outputs not cached)
- **Cost Risk**: MEDIUM (GPT-4o-mini is cheap, but full articles are long)

### ESPN Scraper
- **Service**: `ESPNScraper` (`backend/app/services/data_fetchers/espn_scraper.py`)
- **Usage**: Team stats, injuries (free, no API key)
- **Caching**: 15-minute in-memory cache
- **Cost Risk**: NONE (free scraping)

---

## 7. Caching Strategy

### Database-Level Caching
- **Games/Markets/Odds**: Stored in DB, refreshed every 2h (scheduler)
- **Team Stats**: Stored in `team_stats` table, updated daily (scraper)
- **Game Analyses**: Stored in `game_analyses` table, TTL: NFL 48h, others 24h

### Application-Level Caching
- **Redis** (optional, required in production):
  - Distributed odds API cache (48h TTL)
  - Scheduler leader election
  - If unavailable: Falls back to in-process caching

- **In-Memory Caches**:
  - `StatsScraperService`: 15-minute TTL
  - `OddsApiRateLimiter`: 10-second minimum between calls
  - `TrafficRanker`: 5-minute TTL for top games
  - `FetchBudgetManager`: In-memory fallback (5-minute TTL)

### Frontend Caching
- **Analysis API**: Client-side cache (`cacheManager` in `AnalysisApi.ts`)
  - TTL: NFL 48h, others 24h
  - Auto-refresh if probabilities are 50-50 (indicates stale data)

---

## 8. Concurrency & Locking

### Analysis Generation
- **Per-Game Lock**: `AnalysisRepository.core_lock()` uses database-level advisory locks
- **Lock Scope**: Prevents concurrent generation for same game
- **Lock Duration**: Entire core generation (< 8s)

### Background Jobs
- **Leader Election**: `SchedulerLeaderLock` (Redis-based)
- **Prevents**: Multiple instances running duplicate jobs
- **Fallback**: In dev/test, scheduler disabled if Redis unavailable

### Odds Fetching
- **Rate Limiter**: In-process semaphore (1 call per 10s)
- **Distributed Cache**: Redis prevents duplicate fetches across instances

---

## 9. Failure Modes & Degradation

### Core Analysis Generation
- **External API Failures**: Graceful degradation
  - Stats missing → Uses odds-only model
  - Weather missing → Skips weather section
  - Injuries missing → Skips injury section
- **Timeout**: 8s hard timeout, returns partial analysis
- **OpenAI Polish**: Optional, 4s timeout, never blocks core

### Odds Fetching
- **API Failure**: Returns stale DB cache (up to 48h old)
- **Redis Unavailable**: Falls back to in-process rate limiter
- **Rate Limit Hit**: Returns cached data, logs warning

### Background Jobs
- **Job Failure**: Logged, doesn't crash scheduler
- **DB Unavailable**: Job skipped, retries on next run
- **Redis Unavailable**: Scheduler disabled in non-production

---

## 10. Performance Characteristics

### Analysis Generation
- **Core Generation**: < 8s (target), typically 3-5s
- **Full Article**: 90s (background, async)
- **Bottlenecks**: 
  - External API calls (stats, weather, injuries)
  - Database queries (markets/odds with selectinload)

### API Response Times
- **GET /api/analysis/{slug}**: 50-200ms (cached), 3-8s (generation)
- **GET /api/games**: 100-500ms (cached), 2-5s (fresh fetch)
- **POST /api/parlay**: 2-10s (depends on prefetch concurrency)

### Database Query Patterns
- **N+1 Queries**: Prevented with `selectinload()` for relationships
- **Slow Queries**: Potential in `_generate_upcoming_analyses()` (outerjoin on large tables)
- **Missing Indexes**: See ZERO_COST_UPGRADES.md for recommendations

---

## 11. Security & Access Control

### Authentication
- **JWT**: `jwt_secret`, 24h expiration
- **Routes**: Protected via `Depends(get_optional_user)` or `Depends(require_auth)`

### Rate Limiting
- **Global**: 100 requests per 60s (configurable)
- **Per-Endpoint**: Custom limits via `@rate_limit()` decorator
- **Odds API**: 1 call per 10s (in-process)

### Admin Access
- **Role Check**: `user.is_admin()` property
- **Routes**: `/api/admin/*` require admin role

---

## 12. Monitoring & Observability

### Logging
- **System Logs**: `system_logs` table (admin viewable)
- **App Events**: `app_events` table (analytics)
- **Print Statements**: Used extensively (should migrate to structured logging)

### Metrics
- **Admin Dashboard**: `/api/admin/metrics` (revenue, users, usage)
- **Analysis Metrics**: Stored in `analysis_content.generation.metrics` (core_ms, external_calls_count, cache_hit)

### Error Tracking
- **Bug Reports**: `bug_reports` table (user-submitted)
- **Exception Handling**: Try/except blocks with logging (no external service)

---

## Summary

**Strengths**:
- Deterministic core generation (works without OpenAI)
- Comprehensive caching strategy (DB + Redis + in-memory)
- Graceful degradation on external failures
- Well-structured service layer

**Weaknesses**:
- Some N+1 query risks in analysis generation
- Missing indexes on some frequently queried columns
- No structured logging (relies on print statements)
- Limited observability (no APM, no error tracking service)
- Fetch budget tracking is new (may have gaps)

**Cost Exposure**:
- The Odds API: HIGH (no hard cap, credits-based)
- OpenAI: MEDIUM (full articles are expensive, but optional)
- Redis: Required for production (distributed cache + leader election)
