# API-Sports Integration Status in Parlay Gorilla

## ✅ What's Built (Infrastructure Complete)

### 1. **Data Collection & Caching**
- **Background scheduler** refreshes API-Sports data every 60 minutes
- **Quota management** enforces 100 requests/day limit
- **DB-first architecture** - all data cached in PostgreSQL
- **Tables created:** `apisports_fixtures`, `apisports_results`, `apisports_team_stats`, `apisports_standings`, `apisports_features`, `api_quota_usage`

### 2. **Data Access Layer**
- **`SportsDataRepository`** - Read/write API-Sports cache (DB-only reads)
- **`FeatureBuilderService`** - Computes derived features (form, rest days, splits)
- **`ConfidenceEngine`** - Blends model + odds probabilities with freshness awareness

### 3. **Admin & Monitoring**
- **`GET /api/admin/apisports/quota`** - Check daily usage
- **`POST /api/admin/apisports/refresh`** - Manual refresh trigger
- **Logs** - Scheduler reports usage: `[SCHEDULER] API-Sports refresh: used=X remaining=Y`

---

## ❌ What's NOT Yet Integrated (Pending)

### API-Sports data is **NOT currently used** in:
- ❌ Probability calculations (`BaseProbabilityEngine`)
- ❌ Feature pipeline (`FeaturePipeline`)
- ❌ Model win probability (`ModelWinProbabilityCalculator`)
- ❌ Parlay generation (`ParlayBuilderService`)
- ❌ Analysis generation (`AnalysisGeneratorService`)

**Why?** The infrastructure is ready, but the integration points need to be wired up.

---

## Data Source Roles

| Purpose | Primary | Fallback |
|--------|---------|----------|
| **Odds** | The Odds API | — |
| **Scheduling (games list)** | The Odds API | API-Sports |
| **Sports data** (stats, results, form, standings) | API-Sports | ESPN |

## How API-Sports Would Improve Predictions

### Current System Uses:
- **The Odds API** - Odds and primary scheduling (games list)
- **API-Sports** - Sports data (stats, fixtures, results, standings); scheduling fallback
- **ESPN** - Backup stats, matchup context
- **Weather API** - Outdoor conditions

### API-Sports Would Add:
1. **Multi-sport consistency** - Same API format for all sports
2. **Form data** - Last 5 games win/loss (better than season totals)
3. **Rest days** - Days since last game (fatigue factor)
4. **Home/away splits** - Venue-specific performance
5. **Opponent strength** - Standings-based strength proxy
6. **Freshness tracking** - Know when data is stale

### Example Improvement:

**Before (current):**
```
Model uses: Season win % (50%), Recent form (30%), Home advantage (20%)
Confidence: Fixed calculation from model edge
```

**After (with API-Sports):**
```
Model uses: 
  - Season win % (40%)
  - Last 5 games form from API-Sports (25%)
  - Rest days from API-Sports (10%)
  - Home/away splits from API-Sports (10%)
  - Opponent strength from standings (10%)
  - Home advantage (5%)

Confidence: 
  - Blends model (60%) + market odds (40%)
  - Weight adjusts by data freshness (stale → lower model weight)
  - Returns confidence meter: "70-80" with explanation
```

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Background Scheduler (every 60 min)                         │
│                                                              │
│  SportsRefreshService                                        │
│    ↓ (quota-safe, 100/day)                                 │
│  ApiSportsClient → API-Sports API                           │
│    ↓                                                         │
│  SportsDataRepository.upsert_*()                           │
│    ↓                                                         │
│  DB: apisports_fixtures, apisports_standings, etc.        │
└─────────────────────────────────────────────────────────────┘
                              ↓ (data cached)
┌─────────────────────────────────────────────────────────────┐
│ User Request: GET /api/parlay/suggest                      │
│                                                              │
│  [INTEGRATION POINT - NOT YET WIRED]                       │
│                                                              │
│  FeaturePipeline                                            │
│    ├─ SportsDataRepository.get_team_stats()  ← ADD THIS    │
│    ├─ FeatureBuilderService.build_team_features() ← ADD     │
│    └─ ESPN fallback when API-Sports unavailable            │
│         ↓                                                   │
│  BaseProbabilityEngine                                      │
│    ├─ Use form from apisports_features ← ADD THIS         │
│    ├─ Use rest days from apisports_features ← ADD          │
│    └─ Use opponent strength from standings ← ADD           │
│         ↓                                                   │
│  ModelWinProbabilityCalculator                              │
│    └─ ConfidenceEngine.blend() ← REPLACE current calc      │
│         ↓                                                   │
│  Return: {prob, confidence_meter, explanation}             │
└─────────────────────────────────────────────────────────────┘
```

---

## What Needs to Be Done

### 1. Team Name Mapping (One-time Setup)
Create mapping: Parlay Gorilla team names → API-Sports team IDs

**File:** `backend/app/services/apisports/team_mapper.py`

```python
TEAM_NAME_TO_ID = {
    "football": {
        "Manchester United": 33,
        "Liverpool": 40,
        # ... etc
    },
    "basketball_nba": {
        "Los Angeles Lakers": 14,
        # ... etc
    }
}
```

### 2. Integrate into FeaturePipeline
**File:** `backend/app/services/feature_pipeline.py`

API-Sports is primary; ESPN is fallback when API-Sports data is unavailable.

### 3. Integrate into Probability Engine
**File:** `backend/app/services/probability_engine_impl/base_engine.py`

Use API-Sports form, rest days, and opponent strength in heuristics.

### 4. Use ConfidenceEngine
**File:** `backend/app/services/model_win_probability.py`

Replace simple confidence with `ConfidenceEngine.blend()`.

---

## Current State Summary

| Component | Status | Notes |
|-----------|--------|-------|
| **Data Collection** | ✅ Active | Scheduler runs every 60 min, quota enforced |
| **Data Storage** | ✅ Active | All data cached in DB tables |
| **Feature Building** | ✅ Ready | `FeatureBuilderService` can compute features |
| **Confidence Engine** | ✅ Ready | `ConfidenceEngine` can blend probabilities |
| **Team Name Mapping** | ❌ Missing | Need to map team names → API-Sports IDs |
| **FeaturePipeline Integration** | ❌ Pending | Not yet reading from API-Sports |
| **Probability Engine Integration** | ❌ Pending | Not yet using API-Sports features |
| **Confidence Integration** | ❌ Pending | Not yet using ConfidenceEngine |

---

## Bottom Line

**API-Sports is infrastructure-ready but not yet used in predictions.**

The system:
- ✅ Collects and caches API-Sports data
- ✅ Manages quota safely (100/day)
- ✅ Provides feature building and confidence blending tools
- ❌ Does NOT yet use this data in actual predictions

**To activate:** Wire `SportsDataRepository` and `FeatureBuilderService` into `FeaturePipeline` and `BaseProbabilityEngine`.

See [docs/API_SPORTS_USAGE_GUIDE.md](docs/API_SPORTS_USAGE_GUIDE.md) for detailed integration steps.
