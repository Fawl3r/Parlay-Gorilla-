# How API-Sports is Used in Parlay Gorilla

## Current Status: Infrastructure Ready, Integration Pending

API-Sports integration is **fully implemented** as infrastructure (quota management, data caching, refresh pipeline), but it's **not yet wired into the prediction flow**. This document explains what's built and how to integrate it.

---

## Data Source Roles

| Purpose | Primary | Fallback |
|--------|---------|----------|
| **Odds** | The Odds API | — |
| **Scheduling (games list)** | The Odds API | API-Sports |
| **Sports data** (stats, results, form, standings) | API-Sports | ESPN |

- **The Odds API** is the single source for odds and the primary source for scheduling (upcoming games). When games or times are missing or need validation, API-Sports fixtures can be used as a scheduling fallback.
- **API-Sports** is the primary sports data source (fixtures, results, team stats, standings, form). It is also the scheduling fallback when The Odds API does not have schedule data.

---

## What API-Sports Provides

API-Sports is a **multi-sport data source** that provides:

1. **Fixtures** (upcoming games) - schedules, dates, teams
2. **Results** (completed games) - scores, outcomes, timestamps
3. **Team Statistics** - season stats, performance metrics
4. **Standings** - league tables, rankings
5. **Injuries** (optional) - player injury reports

**Key advantage:** Multi-sport coverage (football, basketball, hockey, baseball, soccer) with consistent API format.

---

## Current Architecture (What's Built)

### 1. Data Collection (Background Only)

**`SportsRefreshService`** runs every 60 minutes via scheduler:
- Fetches fixtures for today + tomorrow (1 call per sport/league), using the correct API-Sports base URL per sport (soccer: v3 football; NFL/NBA/NHL/MLB: v1 hosts).
- Fetches standings once per day per active sport; **TTL-skip:** if standings for that sport/league are still fresh (within `APISPORTS_TTL_STANDINGS_SECONDS`), the fetch is skipped to save quota.
- After standings refresh, derives normalized per-team stats and upserts into `apisports_team_stats` (no extra API calls).
- Stores everything in DB tables: `apisports_fixtures`, `apisports_standings`, `apisports_team_stats`, etc.
- **Quota-safe:** Stops when remaining < 5 calls (reserve).

**Never called from user-facing endpoints** - all API calls happen in background.

### 2. Data Storage (DB-First)

**`SportsDataRepository`** provides:
- `get_fixtures(sport, from_date, to_date)` - Read upcoming games
- `get_team_stats(sport, team_id)` - Read team statistics
- `get_standings(sport, league_id)` - Read league standings
- `is_fresh(entity, stale_after_seconds)` - Check data freshness

All reads are **DB-only** (no live API calls in request path).

### 3. Feature Engineering (Ready to Use)

**`FeatureBuilderService`** computes:
- **Last N form** (wins/losses in recent games)
- **Home/away splits** (performance by venue)
- **Rest days** (days since last game)
- **Opponent strength proxy** (from standings)

Stores to `apisports_features` table.

### 4. Confidence Blending (Ready to Use)

**`ConfidenceEngine`** blends:
- `model_prob` (from your ML model)
- `implied_prob` (from market odds)
- `final_prob = w * model_prob + (1-w) * implied_prob`

Where `w` depends on:
- Data freshness (stale data → lower model weight)
- Sample size (more data → higher model weight)

Returns confidence meter: "50-60", "60-70", "70-80", "80-90", "90+"

---

## How to Integrate API-Sports into Predictions

### Integration Point 1: Feature Pipeline

**Current:** `FeaturePipeline` uses API-Sports (primary), ESPN (fallback), Weather

**Add API-Sports:**

```python
# In app/services/feature_pipeline.py

from app.repositories.sports_data_repository import SportsDataRepository
from app.services.feature_builder_service import FeatureBuilderService

class FeaturePipeline:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._apisports_repo = SportsDataRepository(db)
        self._feature_builder = FeatureBuilderService(db)
    
    async def _fetch_recent_form(self, home_team, away_team, sport):
        # Use API-Sports results for form
        # Map team names to API-Sports team_ids (you'll need a mapping)
        home_features = await self._feature_builder.build_team_features(
            sport=sport,
            team_id=home_team_id,
            last_n=5
        )
        # Extract: wins, losses, home/away splits, rest days
        # Add to MatchupFeatureVector
```

### Integration Point 2: Probability Engine

**Current:** `BaseProbabilityEngine` uses heuristics + team strength

**Add API-Sports features:**

```python
# In app/services/probability_engine_impl/base_engine.py

from app.repositories.sports_data_repository import SportsDataRepository

class BaseProbabilityEngine:
    async def _get_team_form_from_apisports(self, team_id, sport):
        repo = SportsDataRepository(self.db)
        features = await repo.get_team_features(sport, team_id)
        if features:
            return {
                "recent_wins": features.last_n_form_wins,
                "recent_losses": features.last_n_form_losses,
                "rest_days": features.rest_days,
                "home_away_split": features.home_away_split_json
            }
        return None
```

### Integration Point 3: Confidence Calculation

**Current:** Confidence is calculated from model edge

**Use ConfidenceEngine:**

```python
# In app/services/model_win_probability.py or analysis_generator.py

from app.services.confidence_engine import get_confidence_engine
from app.repositories.sports_data_repository import SportsDataRepository

async def calculate_with_confidence(model_prob, implied_prob, sport, team_id):
    repo = SportsDataRepository(db)
    team_stats = await repo.get_team_stats(sport, team_id)
    
    # Calculate freshness score (0-1)
    freshness = 1.0
    if team_stats:
        is_fresh = SportsDataRepository.is_fresh(
            team_stats.last_fetched_at,
            team_stats.stale_after_seconds
        )
        freshness = 1.0 if is_fresh else 0.5
    
    # Calculate sample size score (0-1)
    sample_score = 1.0  # Based on number of games in stats
    
    # Blend
    engine = get_confidence_engine()
    result = engine.blend(
        model_prob=model_prob,
        implied_prob=implied_prob,
        data_freshness_score=freshness,
        sample_size_score=sample_score
    )
    
    return {
        "final_prob": result.final_prob,
        "confidence_meter": result.confidence_meter,
        "explanation": result.explanation
    }
```

---

## Example: Using API-Sports Data in Predictions

### Scenario: Calculate Win Probability for EPL Match

```python
from app.repositories.sports_data_repository import SportsDataRepository
from app.services.feature_builder_service import FeatureBuilderService
from app.services.confidence_engine import get_confidence_engine

async def predict_game(home_team_id, away_team_id, sport="football"):
    repo = SportsDataRepository(db)
    
    # 1. Get team features (form, rest days, splits)
    home_features = await FeatureBuilderService(db).build_team_features(
        sport=sport,
        team_id=home_team_id,
        last_n=5
    )
    away_features = await FeatureBuilderService(db).build_team_features(
        sport=sport,
        team_id=away_team_id,
        last_n=5
    )
    
    # 2. Get standings (opponent strength)
    standings = await repo.get_standings(sport, league_id=39)  # EPL
    
    # 3. Calculate model probability (using features)
    model_prob_home = calculate_model_prob(
        home_form=home_features["last_n_form_wins"] / 5,
        away_form=away_features["last_n_form_wins"] / 5,
        rest_days_home=home_features["rest_days"],
        rest_days_away=away_features["rest_days"],
        home_advantage=0.03
    )
    
    # 4. Get implied probability from odds
    implied_prob_home = 0.55  # From odds API
    
    # 5. Blend with confidence
    freshness = 1.0  # Assume fresh
    engine = get_confidence_engine()
    result = engine.blend(
        model_prob=model_prob_home,
        implied_prob=implied_prob_home,
        data_freshness_score=freshness,
        sample_size_score=1.0
    )
    
    return {
        "win_probability": result.final_prob,
        "confidence": result.confidence_meter,
        "explanation": result.explanation
    }
```

---

## Current Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Background Scheduler (every 60 min)                         │
│                                                              │
│  SportsRefreshService                                        │
│    ↓                                                         │
│  ApiSportsClient (quota-safe)                             │
│    ↓                                                         │
│  SportsDataRepository.upsert_*()                            │
│    ↓                                                         │
│  DB: apisports_fixtures, apisports_standings, etc.         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ User Request (e.g., GET /api/parlay/suggest)                │
│                                                              │
│  [NOT YET INTEGRATED]                                       │
│  SportsDataRepository.get_*()                               │
│    ↓                                                         │
│  FeatureBuilderService.build_team_features()                 │
│    ↓                                                         │
│  ConfidenceEngine.blend()                                   │
│    ↓                                                         │
│  Probability Engine / Parlay Builder                        │
└─────────────────────────────────────────────────────────────┘
```

---

## What Needs to Be Done (Integration Steps)

### Step 1: Team Name Mapping

Create a mapping from Parlay Gorilla team names → API-Sports team IDs:

```python
# backend/app/services/apisports/team_mapper.py

TEAM_NAME_TO_ID = {
    "football": {
        "Manchester United": 33,
        "Liverpool": 40,
        # ... etc
    }
}
```

### Step 2: Integrate into FeaturePipeline

Modify `app/services/feature_pipeline.py`:
- Add `SportsDataRepository` to fetch API-Sports data
- Use `FeatureBuilderService` to get form/rest days
- Use ESPN as fallback when API-Sports data is unavailable

### Step 3: Integrate into Probability Engine

Modify `app/services/probability_engine_impl/base_engine.py`:
- Add API-Sports form data to heuristics
- Use rest days from `apisports_features`
- Use opponent strength from standings

### Step 4: Use ConfidenceEngine

Modify `app/services/model_win_probability.py`:
- Replace simple confidence calculation with `ConfidenceEngine.blend()`
- Pass data freshness score from API-Sports cache
- Return confidence meter to frontend

---

## Benefits of Using API-Sports

1. **Multi-sport coverage** - Consistent API across NFL, NBA, NHL, MLB, Soccer
2. **Form data** - Last N games, home/away splits (better than season totals)
3. **Rest days** - Days since last game (important for fatigue)
4. **Opponent strength** - Standings-based strength proxy
5. **Freshness tracking** - Know when data is stale
6. **Confidence calibration** - Blend model + market with data quality awareness

---

## Current Usage (What's Active Now)

✅ **Background refresh** - Scheduler fetches and caches data every 60 min  
✅ **Quota management** - Tracks usage, prevents exceeding 100/day  
✅ **Admin endpoints** - `/admin/apisports/quota` and `/admin/apisports/refresh`  
✅ **Data storage** - All data cached in DB tables  

❌ **Not yet used in predictions** - Infrastructure ready, integration pending

---

## Next Steps to Activate

1. **Create team name → ID mapping** (one-time setup)
2. **Integrate `SportsDataRepository` into `FeaturePipeline`**
3. **Use `FeatureBuilderService` for form/rest days**
4. **Use `ConfidenceEngine` in probability calculations**
5. **Test with real games** and verify improvements

The infrastructure is **production-ready** - you just need to wire it into the prediction flow!
