# Game Analysis System - Comprehensive Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture & Components](#architecture--components)
3. [Data Flow](#data-flow)
4. [Core Services](#core-services)
5. [API Endpoints](#api-endpoints)
6. [Database Schema](#database-schema)
7. [AI Generation Process](#ai-generation-process)
8. [Probability Engine](#probability-engine)
9. [Stats & Data Sources](#stats--data-sources)
10. [Caching & Performance](#caching--performance)
11. [Background Jobs](#background-jobs)
12. [Frontend Integration](#frontend-integration)
13. [Configuration](#configuration)
14. [Error Handling](#error-handling)

---

## System Overview

The Game Analysis System is a comprehensive, AI-powered sports betting analysis platform that generates Covers.com-style game breakdowns for NFL, NBA, NHL, MLB, and other sports. The system combines real-time odds data, team statistics, weather conditions, injury reports, and machine learning models to produce actionable betting insights.

**See also:** [PARLAY_GORILLA_GAME_ANALYSIS_V2.md](PARLAY_GORILLA_GAME_ANALYSIS_V2.md) (Universal Game Intelligence Engine design), [PARLAY_GORILLA_WEATHER_INTELLIGENCE.md](PARLAY_GORILLA_WEATHER_INTELLIGENCE.md) (Weather Impact Engine).

### Key Features
- **Fast Core Analysis**: Deterministic, sub-10-second generation for instant UI rendering
- **Long-Form Articles**: Background-generated 1200-2000 word SEO-optimized articles
- **Model-Based Predictions**: Win probabilities calculated from weighted combination of odds, stats, and situational factors
- **Same-Game Parlays**: AI-generated parlay recommendations (3-leg safe, 6-leg balanced, 15-leg degen)
- **Real-Time Odds Integration**: Live odds from The Odds API with line movement tracking
- **Multi-Sport Support**: NFL, NBA, NHL, MLB, NCAAF, NCAAB, Soccer leagues

---

## Architecture & Components

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                        │
│  - Analysis detail pages (/analysis/{sport}/{slug})         │
│  - Analysis list/feed                                        │
│  - Real-time updates via API                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTP/REST API
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              FastAPI Backend                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Analysis Orchestrator Service                │  │
│  │  - Slug resolution                                     │  │
│  │  - Cache management                                    │  │
│  │  - Generation coordination                             │  │
│  └──────────────┬─────────────────────────────────────────┘  │
│                 │                                            │
│  ┌──────────────▼─────────────────────────────────────────┐ │
│  │      Core Analysis Generator                            │ │
│  │  - Fast deterministic generation (< 8s)                │ │
│  │  - No OpenAI dependency for core                       │ │
│  │  - Picks, trends, edges, model probs                    │ │
│  └──────────────┬─────────────────────────────────────────┘ │
│                 │                                            │
│  ┌──────────────▼─────────────────────────────────────────┐ │
│  │      Full Article Generator (Background)                │ │
│  │  - OpenAI GPT-4o-mini                                   │ │
│  │  - 1200-2000 word articles                             │ │
│  │  - SEO-optimized HTML                                   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Supporting Services                            │  │
│  │  - StatsScraperService (team stats, weather, injuries)│  │
│  │  - Probability Engine (win probability calculation)   │  │
│  │  - OddsSnapshotBuilder (market data aggregation)      │  │
│  │  - OddsHistoryProvider (line movement tracking)      │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ SQLAlchemy ORM
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              PostgreSQL Database                              │
│  - game_analyses (analysis content, metadata)                │
│  - games (game info, teams, start times)                     │
│  - markets (spread, total, moneyline markets)                 │
│  - odds (odds prices, implied probabilities)                   │
│  - team_stats (season stats, ATS trends, O/U trends)         │
└───────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### 1. **Analysis Orchestrator Service**
**Location**: `backend/app/services/analysis/analysis_orchestrator.py`

**Responsibilities**:
- Coordinates the entire analysis generation workflow
- Resolves slugs to games
- Manages cache/refresh policies
- Ensures core analysis is generated before full articles
- Handles concurrency with per-game locks

**Key Methods**:
- `get_or_generate_for_slug()`: Main entry point for API requests
- `ensure_core_for_game()`: Used by schedulers to pre-generate analyses

#### 2. **Core Analysis Generator**
**Location**: `backend/app/services/analysis/core_analysis_generator.py`

**Responsibilities**:
- Generates fast, deterministic core analysis (< 8 seconds)
- Builds picks, trends, edges without OpenAI dependency
- Calculates model win probabilities
- Creates score projections
- Generates UI blocks for frontend

**Key Components**:
- `CorePickBuilders`: Spread/total picks with confidence scores
- `CoreAnalysisEdgesBuilder`: Offensive/defensive matchup edges
- `CoreAnalysisUiBlocksBuilder`: Decision-first UI components

#### 3. **Full Article Generator**
**Location**: `backend/app/services/analysis/full_article_generator.py`

**Responsibilities**:
- Generates long-form 1200-2000 word articles
- Uses OpenAI GPT-4o-mini
- SEO-optimized HTML with proper heading structure
- Runs asynchronously in background

#### 4. **Analysis AI Writer**
**Location**: `backend/app/services/analysis/analysis_ai_writer.py`

**Responsibilities**:
- Polishes core copy with OpenAI (optional, best-effort)
- Rewrites UI blocks for better readability
- Strict timeout (4 seconds) to not block core generation

#### 5. **Analysis Repository**
**Location**: `backend/app/services/analysis/analysis_repository.py`

**Responsibilities**:
- Database CRUD operations for `GameAnalysis` model
- Merges core updates without losing full articles
- Provides per-game concurrency locks
- Manages cache TTL by league (NFL: 48h, others: 24h)

#### 6. **Stats Scraper Service**
**Location**: `backend/app/services/stats_scraper.py`

**Responsibilities**:
- Fetches team statistics from database or external APIs
- Aggregates matchup data (stats, injuries, weather)
- Caches data for 15 minutes
- Supports multiple leagues (NFL, NBA, NHL, MLB, Soccer)

#### 7. **Probability Engine**
**Location**: `backend/app/services/model_win_probability.py`

**Responsibilities**:
- Calculates win probabilities using weighted combination:
  - Market odds (implied probabilities): 50% weight
  - Team statistics: 30% weight
  - Situational factors (rest, travel, weather, injuries): 20% weight
- Generates confidence scores (0-100)
- Accounts for home advantage by sport

#### 8. **Odds Snapshot Builder**
**Location**: `backend/app/services/odds_snapshot_builder.py`

**Responsibilities**:
- Aggregates market data (spread, total, moneyline)
- Extracts best odds from multiple books
- Calculates implied probabilities
- Normalizes odds format

#### 9. **Odds History Provider**
**Location**: `backend/app/services/odds_history/odds_history_provider.py`

**Responsibilities**:
- Tracks line movement over time
- Identifies sharp money indicators
- Provides movement summaries for analysis

---

## Data Flow

### Analysis Generation Flow

```
1. API Request
   └─> GET /api/analysis/{sport}/{slug}?refresh=false
       │
       ├─> AnalysisOrchestrator.get_or_generate_for_slug()
       │   │
       │   ├─> Check cache (AnalysisRepository.get_by_slug())
       │   │   └─> If cached & core ready: Return immediately
       │   │
       │   ├─> Resolve slug to game (AnalysisSlugResolver)
       │   │   └─> Find game by slug pattern or game_id
       │   │
       │   ├─> Acquire per-game lock (prevent concurrent generation)
       │   │
       │   └─> CoreAnalysisGenerator.generate()
       │       │
       │       ├─> Load markets & odds (from database)
       │       │   └─> OddsSnapshotBuilder.build()
       │       │
       │       ├─> Get line movement (OddsHistoryProvider)
       │       │
       │       ├─> Fetch matchup data (StatsScraperService)
       │       │   ├─> Team stats (offense, defense, ATS, O/U)
       │       │   ├─> Injury reports
       │       │   ├─> Weather conditions (outdoor sports)
       │       │   └─> Recent form
       │       │
       │       ├─> Calculate win probability (Probability Engine)
       │       │   ├─> Market odds (50% weight)
       │       │   ├─> Team stats (30% weight)
       │       │   └─> Situational factors (20% weight)
       │       │
       │       ├─> Generate score projection (ScoreProjector)
       │       │
       │       ├─> Build picks (CorePickBuilders)
       │       │   ├─> Spread pick with confidence
       │       │   └─> Total pick with confidence
       │       │
       │       ├─> Build edges (CoreAnalysisEdgesBuilder)
       │       │   ├─> Offensive matchup edges
       │       │   └─> Defensive matchup edges
       │       │
       │       ├─> Build trends (ATS & Totals)
       │       │
       │       ├─> Build UI blocks (CoreAnalysisUiBlocksBuilder)
       │       │
       │       └─> Polish with AI (AnalysisAiWriter) [optional, 4s timeout]
       │
       ├─> Save to database (AnalysisRepository.upsert_core())
       │   └─> Merge with existing full article (if present)
       │
       └─> Enqueue full article generation (FullArticleJobRunner)
           └─> Background task (async, non-blocking)
               └─> FullArticleGenerator.generate()
                   └─> OpenAI GPT-4o-mini (90s timeout)
```

### Full Article Generation Flow

```
Background Job (FullArticleJobRunner)
│
├─> Check if full article already exists
│   └─> If yes: Skip
│
├─> Acquire per-analysis lock
│
├─> Load game & core content
│
├─> FullArticleGenerator.generate()
│   ├─> Build prompt from core content
│   ├─> Call OpenAI GPT-4o-mini
│   │   └─> 900-1400 word article
│   │       └─> Structured with H2/H3 headings
│   └─> Return HTML article
│
└─> Save to database (AnalysisRepository.update_full_article())
    └─> Update analysis_content["full_article"]
```

---

## Core Services

### CoreAnalysisGenerator

**Purpose**: Fast, deterministic core analysis generation

**Key Methods**:

```python
async def generate(
    self,
    *,
    game: Game,
    timeout_seconds: float = 8.0
) -> Dict[str, Any]
```

**Output Structure**:
```python
{
    "headline": str,
    "subheadline": str,
    "opening_summary": str,
    "offensive_matchup_edges": {
        "home_advantage": str,
        "away_advantage": str,
        "key_matchup": str
    },
    "defensive_matchup_edges": {
        "home_advantage": str,
        "away_advantage": str,
        "key_matchup": str
    },
    "key_stats": List[str],
    "ats_trends": {
        "home_team_trend": str,
        "away_team_trend": str,
        "analysis": str
    },
    "totals_trends": {
        "home_team_trend": str,
        "away_team_trend": str,
        "analysis": str
    },
    "market_movement": Dict[str, Any],
    "weather_considerations": str,
    "model_win_probability": {
        "home_win_prob": float,
        "away_win_prob": float,
        "ai_confidence": float,
        "calculation_method": str,
        "score_projection": str,
        "explanation": str
    },
    "ai_spread_pick": {
        "pick": str,
        "confidence": float,
        "rationale": str
    },
    "ai_total_pick": {
        "pick": str,
        "confidence": float,
        "rationale": str
    },
    "best_bets": [
        {
            "bet_type": str,
            "pick": str,
            "confidence": float,
            "rationale": str
        }
    ],
    "same_game_parlays": {
        "safe_3_leg": {...},
        "balanced_6_leg": {...},
        "degen_10_20_leg": {...}
    },
    "full_article": "",  # Generated in background
    "ui_quick_take": {...},
    "ui_key_drivers": {...},
    "ui_bet_options": [...],
    "ui_matchup_cards": [...],
    "ui_trends": [...]
}
```

**Timeout Handling**:
- Matchup data fetch: 8 seconds (configurable)
- AI polish: 4 seconds (best-effort, never blocks)
- Total generation: < 10 seconds target

### AnalysisOrchestratorService

**Purpose**: Coordinates analysis generation and caching

**Key Methods**:

```python
async def get_or_generate_for_slug(
    self,
    *,
    sport_identifier: str,
    slug: str,
    refresh: bool,
    core_timeout_seconds: float = 8.0
) -> OrchestratorResult
```

**Cache Strategy**:
- Check by slug first (supports prefixed and legacy formats)
- If cached & core ready: Return immediately
- If cached but core incomplete: Regenerate core
- If not cached: Generate new analysis

**Concurrency Control**:
- Per-game locks prevent concurrent generation
- Lock acquired before database check (double-check pattern)
- Ensures only one generation per game at a time

### StatsScraperService

**Purpose**: Aggregates team statistics and matchup data

**Key Methods**:

```python
async def get_matchup_data(
    self,
    home_team: str,
    away_team: str,
    league: str,
    season: str,
    game_time: datetime
) -> Dict[str, Any]
```

**Returns**:
```python
{
    "home_team_stats": {
        "record": {...},
        "offense": {...},
        "defense": {...},
        "ats_trends": {...},
        "over_under_trends": {...}
    },
    "away_team_stats": {...},
    "home_injuries": [...],
    "away_injuries": [...],
    "weather": {
        "temperature": float,
        "wind_speed": float,
        "condition": str,
        "is_outdoor": bool,
        "affects_game": bool
    },
    "rest_days_home": int,
    "rest_days_away": int,
    "travel_distance": float,
    "is_divisional": bool,
    "head_to_head": {...}
}
```

**Caching**:
- 15-minute TTL for team stats
- Cache key: `team_stats:{team}:{season}:{week}`
- Can bypass cache with `bypass_cache=True`

---

## API Endpoints

### Get Analysis by Slug

**Endpoint**: `GET /api/analysis/{sport}/{slug}`

**Parameters**:
- `sport`: Sport identifier (e.g., "nfl", "nba")
- `slug`: Analysis slug (e.g., "bears-vs-packers-week-14-2025")
- `refresh`: Boolean query param (admin-only, forces regeneration)

**Response**: `GameAnalysisResponse`

**Example**:
```bash
GET /api/analysis/nfl/bears-vs-packers-week-14-2025
```

**Response Schema**:
```typescript
{
  id: string;
  slug: string;
  league: string;
  matchup: string;
  game_id: string;
  game_time: datetime;
  analysis_content: {
    headline: string;
    opening_summary: string;
    offensive_matchup_edges: {...};
    defensive_matchup_edges: {...};
    key_stats: string[];
    ats_trends: {...};
    totals_trends: {...};
    model_win_probability: {...};
    ai_spread_pick: {...};
    ai_total_pick: {...};
    best_bets: [...];
    same_game_parlays: {...};
    full_article: string;  // May be empty if still generating
    ui_quick_take: {...};
    ui_key_drivers: {...};
    ui_bet_options: [...];
    ui_matchup_cards: [...];
    ui_trends: [...];
  };
  seo_metadata: {
    title: string;
    description: string;
    keywords: string;
  };
  generated_at: datetime;
  expires_at: datetime;
  version: number;
}
```

### Generate Analysis

**Endpoint**: `POST /api/analysis/generate`

**Request Body**:
```json
{
  "game_id": "uuid-here",
  "force_regenerate": false
}
```

**Response**: `GameAnalysisResponse`

### List Analyses

**Endpoint**: `GET /api/analysis/list`

**Query Parameters**:
- `sport`: Filter by sport
- `limit`: Number of results (default: 20)
- `offset`: Pagination offset

**Response**: `List[GameAnalysisListItem]`

---

## Database Schema

### GameAnalysis Model

**Table**: `game_analyses`

**Schema**:
```python
class GameAnalysis(Base):
    id: GUID (primary key)
    game_id: GUID (foreign key -> games.id, indexed)
    slug: String (unique, indexed)  # e.g., "nfl/bears-vs-packers-week-14-2025"
    league: String (indexed)  # NFL, NBA, etc.
    matchup: String  # "Chicago Bears @ Green Bay Packers"
    
    # Full analysis content as structured JSON
    analysis_content: JSON  # Contains all sections
    
    # SEO metadata
    seo_metadata: JSON  # title, description, keywords
    
    # Generation tracking
    generated_at: DateTime (timezone-aware)
    expires_at: DateTime (nullable)
    version: Integer (default: 1)
```

**Indexes**:
- `idx_game_analysis_slug` on `slug`
- `idx_game_analysis_league` on `league`
- `idx_game_analysis_expires` on `expires_at`
- `idx_game_analysis_game_league` on `(game_id, league)`

**analysis_content Structure**:
```json
{
  "headline": "...",
  "opening_summary": "...",
  "offensive_matchup_edges": {...},
  "defensive_matchup_edges": {...},
  "key_stats": [...],
  "ats_trends": {...},
  "totals_trends": {...},
  "model_win_probability": {...},
  "ai_spread_pick": {...},
  "ai_total_pick": {...},
  "best_bets": [...],
  "same_game_parlays": {...},
  "full_article": "...",
  "ui_quick_take": {...},
  "ui_key_drivers": {...},
  "ui_bet_options": [...],
  "ui_matchup_cards": [...],
  "ui_trends": [...],
  "generation": {
    "core_status": "ready" | "partial",
    "full_article_status": "queued" | "ready" | "error" | "disabled",
    "last_error": string | null
  }
}
```

### Related Models

**Game**: `games` table
- Contains game info (teams, start_time, sport)
- Related via `game_id` foreign key

**Market**: `markets` table
- Contains market definitions (spread, total, moneyline)
- Related via `game_id`

**Odds**: `odds` table
- Contains odds prices and implied probabilities
- Related via `market_id`

**TeamStats**: `team_stats` table
- Contains season statistics, ATS trends, O/U trends
- Used by StatsScraperService

---

## AI Generation Process

### Core Analysis AI Polish

**Service**: `AnalysisAiWriter`

**Purpose**: Optional polish of UI blocks for better readability

**Process**:
1. Extract UI subset from core draft
2. Build prompt with matchup context, model probs, odds
3. Call OpenAI GPT-4o-mini with 4-second timeout
4. Parse JSON response
5. Apply polished blocks back to draft

**Timeout**: 4 seconds (best-effort, never blocks core generation)

**Prompt Structure**:
```
Polish the following UI copy blocks for a game analysis detail page.

Goals:
- Clear, confident, non-technical
- No jargon
- No stats (other than provided confidence percent and bet line)
- One recommendation per section

LEAGUE: {league}
MATCHUP: {matchup}
CONTEXT_MODEL: {model_probs JSON}
CONTEXT_ODDS: {odds_snapshot JSON}

DRAFT_UI: {ui_blocks JSON}
```

### Full Article Generation

**Service**: `FullArticleGenerator`

**Purpose**: Generate 1200-2000 word SEO-optimized articles

**Process**:
1. Build prompt from core content
2. Call OpenAI GPT-4o-mini with 90-second timeout
3. Generate structured HTML with H2/H3 headings
4. Save to database

**Prompt Structure**:
```
Write a 900-1400 word game preview for: {matchup} ({sport}).

FORMATTING RULES:
- Use markdown-style headings for structure
- Use EXACTLY these H2 headings:
  ## Opening Summary
  ## Matchup Breakdown
  ## ATS Trends
  ## Totals Trends
  ## Model Projection
  ## Best Bets
  ## Responsible Gambling Note
- Under 'Matchup Breakdown' and 'Best Bets', you MAY use H3 subheadings
- Do NOT use bullet lists or numbered lists
- Write short paragraphs

Use the following precomputed info:
- Model win prob: home={home_prob}, away={away_prob}
- Score projection: {score_proj}
- Spread pick: {spread_pick}
- Total pick: {total_pick}
- ATS: {ats_trends}
- Totals: {totals_trends}
- Best bets: {best_bets}
```

**Timeout**: 90 seconds (background job, non-blocking)

**Status Tracking**:
- `queued`: Enqueued for generation
- `ready`: Successfully generated
- `error`: Generation failed or timed out
- `disabled`: Full article generation disabled

---

## Probability Engine

### Model Win Probability Calculator

**Location**: `backend/app/services/model_win_probability.py`

**Purpose**: Calculate win probabilities using weighted combination of factors

**Weighting**:
- **Market Odds (50% weight)**: Implied probabilities from betting markets
- **Team Statistics (30% weight)**: Season stats, efficiency metrics, recent form
- **Situational Factors (20% weight)**: Rest days, travel distance, weather, injuries, divisional matchups

**Calculation Process**:

1. **Extract Market Probabilities**:
   - Get moneyline odds from odds snapshot
   - Convert to implied probabilities
   - Remove vig (bookmaker margin)
   - Normalize to sum to 1.0

2. **Calculate Stats-Based Probabilities**:
   - Compare team offensive/defensive ratings
   - Factor in recent form (last 5 games)
   - Account for head-to-head history
   - Apply league-specific adjustments

3. **Calculate Situational Adjustments**:
   - **Rest Days**: More rest = advantage (up to ±3%)
   - **Travel Distance**: Long travel = disadvantage (up to ±2%)
   - **Weather**: Extreme conditions affect scoring (up to ±2%)
   - **Injuries**: Key player injuries reduce team strength (up to ±5%)
   - **Divisional Matchup**: Rivalry games are closer (reduce edge by 10%)

4. **Apply Home Advantage**:
   - NFL: +2.5%
   - NBA: +3.5%
   - NHL: +2.5%
   - MLB: +2.0%
   - NCAAF: +2.0%
   - NCAAB: +3.0%

5. **Combine Weighted Probabilities**:
   ```python
   final_prob = (
       0.50 * market_prob +
       0.30 * stats_prob +
       0.20 * situational_prob
   )
   ```

6. **Calculate Confidence Score**:
   - **Data Quality (0-50 points)**: How much data is available
     - Market odds present: +20
     - Team stats present: +15
     - Situational factors present: +10
     - Recent form available: +5
   - **Model Edge (0-50 points)**: How much model differs from market
     - Large edge (>10%): +30
     - Medium edge (5-10%): +20
     - Small edge (2-5%): +10
     - No edge (<2%): +5

**Output**:
```python
{
    "home_model_prob": float,  # 0.0-1.0
    "away_model_prob": float,     # 0.0-1.0
    "ai_confidence": float,     # 0-100
    "calculation_method": str,  # "weighted_combination" | "market_only" | "stats_only"
    "score_projection": str,    # "24-21"
    "explanation": str
}
```

**Fallback Behavior**:
- If market odds unavailable: Use stats-only (70% weight) + situational (30% weight)
- If stats unavailable: Use market-only (80% weight) + situational (20% weight)
- If both unavailable: Return 50/50 with low confidence

---

## Stats & Data Sources

### StatsScraperService

**Data Sources**:

1. **Database (Primary)**:
   - `team_stats` table: Pre-calculated season statistics
   - Updated by background jobs from external APIs

2. **External APIs (Fallback)**:
   - **ESPN**: Team stats, records, recent form
   - **Covers.com**: ATS trends, O/U trends
   - **Rotowire**: Injury reports
   - **OpenWeather API**: Weather conditions

**Data Structure**:

**Team Stats**:
```python
{
    "record": {
        "wins": int,
        "losses": int,
        "ties": int,
        "win_percentage": float
    },
    "offense": {
        "points_per_game": float,
        "yards_per_game": float,
        "passing_yards_per_game": float,
        "rushing_yards_per_game": float
    },
    "defense": {
        "points_allowed_per_game": float,
        "yards_allowed_per_game": float,
        "turnovers_forced": float
    },
    "ats_trends": {
        "wins": int,
        "losses": int,
        "pushes": int,
        "win_percentage": float,
        "recent": str,  # "3-2"
        "home": str,
        "away": str
    },
    "over_under_trends": {
        "overs": int,
        "unders": int,
        "over_percentage": float,
        "recent_overs": int,
        "recent_unders": int,
        "avg_total_points": float
    },
    "recent_form": {
        "recent_wins": int,
        "recent_losses": int,
        "home_record": str,
        "away_record": str
    },
    "strength_ratings": {
        "offensive_rating": float,
        "defensive_rating": float,
        "overall_rating": float
    }
}
```

**Weather Data**:
```python
{
    "temperature": float,
    "feels_like": float,
    "condition": str,
    "description": str,
    "wind_speed": float,
    "wind_direction": float,
    "humidity": float,
    "precipitation": float,
    "is_outdoor": bool,
    "affects_game": bool
}
```

**Injury Data**:
```python
{
    "players": [
        {
            "name": str,
            "position": str,
            "status": str,  # "Out" | "Questionable" | "Doubtful"
            "injury": str,
            "importance": str  # "High" | "Medium" | "Low"
        }
    ],
    "key_injuries": [...],  # High importance only
    "summary": str
}
```

### Odds Data

**Source**: The Odds API

**Structure**:
```python
{
    "home_spread_point": float,      # e.g., -3.5
    "away_spread_point": float,       # e.g., +3.5
    "total_line": float,              # e.g., 44.5
    "home_ml": str,                   # e.g., "-150"
    "away_ml": str,                   # e.g., "+130"
    "home_implied_prob": float,       # 0.0-1.0
    "away_implied_prob": float,       # 0.0-1.0
    "best_book": str,                 # Bookmaker name
    "last_updated": datetime
}
```

---

## Caching & Performance

### Analysis Caching

**Strategy**: Two-tier caching

1. **Database Cache**:
   - Analysis stored in `game_analyses` table
   - TTL by league:
     - NFL: 48 hours
     - Other sports: 24 hours
   - Expires at `expires_at` timestamp

2. **In-Memory Cache** (StatsScraperService):
   - Team stats: 15 minutes TTL
   - Weather data: 15 minutes TTL
   - Injury reports: 15 minutes TTL

**Cache Invalidation**:
- Manual refresh via `?refresh=true` (admin-only)
- Automatic expiration based on `expires_at`
- Force refresh on `force_regenerate=True`

### Performance Targets

- **Core Analysis Generation**: < 8 seconds
- **API Response Time**: < 10 seconds (including generation)
- **Full Article Generation**: 60-90 seconds (background)
- **Cache Hit Response**: < 100ms

### Optimization Techniques

1. **Parallel Data Fetching**:
   - Team stats, injuries, weather fetched in parallel
   - Uses `asyncio.gather()` for concurrent requests

2. **Timeout Management**:
   - Matchup data: 8 seconds (configurable)
   - AI polish: 4 seconds (best-effort)
   - Full article: 90 seconds (background)

3. **Graceful Degradation**:
   - Core analysis works without OpenAI
   - Falls back to deterministic picks if stats unavailable
   - Returns partial analysis if some data missing

4. **Concurrency Control**:
   - Per-game locks prevent duplicate generation
   - Double-check pattern after lock acquisition

---

## Background Jobs

### Full Article Job Runner

**Location**: `backend/app/services/analysis/full_article_job_runner.py`

**Purpose**: Generate long-form articles asynchronously

**Process**:
1. Enqueued after core analysis generation
2. Runs in background (non-blocking)
3. Checks if article already exists
4. Acquires per-analysis lock
5. Generates article with OpenAI
6. Saves to database

**Job Queue**:
- In-process async tasks (may be lost on restart)
- Can be extended with Redis/RabbitMQ for persistence

### Scheduled Analysis Generation

**Location**: `backend/app/services/scheduler.py`

**Purpose**: Pre-generate analyses for upcoming games

**Schedule**:
- Daily at 6 AM: Generate analyses for all upcoming games
- Can be triggered manually via API

**Process**:
```python
for game in upcoming_games:
    orchestrator.ensure_core_for_game(
        game=game,
        core_timeout_seconds=8.0,
        force_regenerate=False
    )
```

---

## Frontend Integration

### Analysis Detail Page

**Route**: `/analysis/[...slug]`

**File**: `frontend/app/analysis/[...slug]/page.tsx`

**Features**:
- Server-side rendering (SSR)
- Real-time updates when analysis ready
- Responsive design
- SEO-optimized meta tags

**Data Fetching**:
```typescript
const response = await fetch(
  `/api/analysis/${sport}/${slug}?refresh=${refresh}`
);
const analysis: GameAnalysisResponse = await response.json();
```

**UI Components**:
- Quick Take (decision-first summary)
- Key Drivers (positives & risks)
- Bet Options (moneyline/spread/total tabs)
- Matchup Cards (offensive/defensive edges)
- Trends (ATS & Totals)
- Best Bets
- Same-Game Parlays
- Full Article (if ready)

### Analysis API Client

**File**: `frontend/lib/api/services/AnalysisApi.ts`

**Methods**:
- `getAnalysis(sport, slug, refresh?)`: Get analysis by slug
- `generateAnalysis(gameId, forceRegenerate?)`: Generate new analysis
- `listAnalyses(sport?, limit?, offset?)`: List analyses

---

## Configuration

### Environment Variables

**Analysis Settings**:
```bash
# Core generation timeout (seconds)
ANALYSIS_CORE_TIMEOUT_SECONDS=8.0

# AI polish timeout (seconds)
ANALYSIS_CORE_AI_POLISH_TIMEOUT_SECONDS=4.0

# Full article timeout (seconds)
ANALYSIS_FULL_ARTICLE_TIMEOUT_SECONDS=90.0

# Enable full article generation
ANALYSIS_FULL_ARTICLE_ENABLED=true

# Cache TTL (hours) - NFL
ANALYSIS_CACHE_TTL_HOURS=48.0

# Cache TTL (hours) - Non-NFL
ANALYSIS_CACHE_TTL_HOURS_NON_NFL=24.0

# Probability prefetch timeout (seconds)
PROBABILITY_PREFETCH_TOTAL_TIMEOUT_SECONDS=12.0
```

**OpenAI Settings**:
```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_ENABLED=true
```

**External API Keys**:
```bash
ODDS_API_KEY=...
OPENWEATHER_API_KEY=...
```

### Settings Object

**Location**: `backend/app/core/config.py`

**Usage**:
```python
from app.core.config import settings

timeout = settings.analysis_core_timeout_seconds
enabled = settings.analysis_full_article_enabled
```

---

## Error Handling

### Error Types

1. **LookupError**: Game or analysis not found
   - Status: 404
   - Action: Attempt warmup and retry once

2. **TimeoutError**: Generation exceeded timeout
   - Status: 200 (partial analysis)
   - Action: Return partial analysis, log error

3. **External API Errors**: Stats/odds unavailable
   - Status: 200 (partial analysis)
   - Action: Graceful degradation, use available data

4. **Database Errors**: Connection/query failures
   - Status: 500
   - Action: Log error, return error response

### Error Response Format

```json
{
  "detail": "Error message",
  "status_code": 404,
  "analysis": null  // Or partial analysis if available
}
```

### Logging

**Error Logging**:
- All errors logged with context
- Includes game_id, sport, slug for debugging
- Stack traces for exceptions

**Performance Logging**:
- Generation time tracked
- Timeout warnings logged
- Cache hit/miss rates tracked

---

## Summary

The Game Analysis System is a sophisticated, production-ready platform that combines:

1. **Fast Core Generation**: Deterministic, sub-10-second analysis for instant UI
2. **AI-Powered Content**: OpenAI GPT-4o-mini for polished copy and long-form articles
3. **Model-Based Predictions**: Weighted probability calculations from multiple data sources
4. **Real-Time Data**: Live odds, stats, weather, injuries
5. **SEO Optimization**: Structured articles with proper metadata
6. **Scalable Architecture**: Caching, concurrency control, background jobs
7. **Multi-Sport Support**: NFL, NBA, NHL, MLB, NCAA, Soccer

The system is designed for reliability, performance, and maintainability, with graceful degradation when external services are unavailable.
