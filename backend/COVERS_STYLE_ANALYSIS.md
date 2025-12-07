# Covers-Style AI Predictions - Implementation Guide

## ✅ What's Implemented

### 1. **Full Game Analysis Generation**
- ✅ Opening summary (2-3 paragraphs)
- ✅ Offensive/defensive matchup edges
- ✅ Key stats with context
- ✅ ATS (Against The Spread) trends
- ✅ Totals (Over/Under) trends
- ✅ Weather considerations
- ✅ Model win probability (calculated from probability engine)
- ✅ AI spread pick with confidence
- ✅ AI total pick with confidence
- ✅ Best bets (top 3)
- ✅ Same-game parlays (3-leg safe, 6-leg balanced, 15-leg degen)
- ✅ Full 1200-2000 word article with SEO structure

### 2. **Data Sources**
- ✅ Real odds from The Odds API (spread, total, moneyline)
- ✅ Team stats from scrapers (ESPN/Covers/Rotowire)
- ✅ Injury reports
- ✅ Weather data (for outdoor games)
- ✅ ATS/O/U trends from team stats
- ✅ Model probabilities from probability engine

### 3. **AI Generation**
- ✅ OpenAI GPT-4o-mini for analysis
- ✅ Structured JSON output
- ✅ Covers.com-style writing tone
- ✅ Data-driven analysis
- ✅ SEO-optimized HTML article

### 4. **Same-Game Parlays**
- ✅ **Safe 3-Leg**: High-probability legs from same game
- ✅ **Balanced 6-Leg**: Mix of safe and value picks
- ✅ **Degen 15-Leg**: Maximum risk/reward

## 🔧 How It Works

### Analysis Generation Flow

```
1. Fetch Game Data
   ├── Game info (teams, time, league)
   ├── Markets (spread, total, moneyline)
   └── Odds (prices, implied probabilities)

2. Gather Context
   ├── Team stats (offense, defense, ATS, O/U)
   ├── Injury reports
   ├── Weather conditions
   └── Model probabilities

3. Build AI Prompt
   ├── Matchup context
   ├── Stats and trends
   ├── Betting lines
   └── Model projections

4. Generate Analysis
   ├── OpenAI GPT-4o-mini
   ├── Structured JSON output
   └── Full article HTML

5. Generate Same-Game Parlays
   ├── Extract legs from game markets
   ├── Build 3-leg safe parlay
   ├── Build 6-leg balanced parlay
   └── Build 15-leg degen parlay
```

## 📊 Analysis Structure

### JSON Output Format

```json
{
  "opening_summary": "...",
  "offensive_defensive_edges": "...",
  "key_stats": ["...", "...", "..."],
  "ats_trends": {
    "home_team_trend": "...",
    "away_team_trend": "...",
    "analysis": "..."
  },
  "totals_trends": {
    "home_team_trend": "...",
    "away_team_trend": "...",
    "analysis": "..."
  },
  "weather_considerations": "...",
  "model_win_probability": {
    "home_win_prob": 0.55,
    "away_win_prob": 0.45,
    "ai_score_projection": "24-21"
  },
  "ai_spread_pick": {
    "pick": "Home Team -3.5",
    "confidence": 72,
    "rationale": "..."
  },
  "ai_total_pick": {
    "pick": "Over 44.5",
    "confidence": 68,
    "rationale": "..."
  },
  "best_bets": [
    {
      "bet_type": "Spread",
      "pick": "Home Team -3.5",
      "confidence": 72,
      "rationale": "..."
    }
  ],
  "same_game_parlays": [
    {
      "type": "safe",
      "title": "3-Leg Same-Game Parlay (Safe)",
      "legs": [...],
      "total_odds": "+600",
      "confidence": 70.0,
      "rationale": "..."
    }
  ],
  "full_breakdown_html": "<h2>...</h2>..."
}
```

## 🚀 Usage

### Generate Analysis for a Game

```python
from app.services.analysis_generator import AnalysisGeneratorService

generator = AnalysisGeneratorService(db)
analysis = await generator.generate_game_analysis(
    game_id="uuid-here",
    sport="nfl"
)
```

### API Endpoint

```bash
POST /api/analysis/generate
{
  "game_id": "uuid-here",
  "sport": "nfl",
  "force_regenerate": false
}
```

### Scheduled Generation

Analyses are automatically generated daily at 6 AM for all upcoming games via the scheduler.

## 🎯 Key Features

### 1. **Real Odds Integration**
- Fetches actual spread, total, and moneyline from The Odds API
- Uses real odds in predictions and parlays
- Updates as odds change

### 2. **Model Probabilities**
- Calculated using probability engine
- Based on team stats, trends, and historical data
- Provides win probabilities and score projections

### 3. **Same-Game Parlays**
- All legs from the same game
- Safe (3-leg), Balanced (6-leg), Degen (15-leg)
- Real odds and confidence scores

### 4. **SEO Optimization**
- 1200-2000 word articles
- Proper H2/H3 structure
- Meta tags and descriptions
- JSON-LD structured data

## 📝 Example Output

### Opening Summary
> "The Kansas City Chiefs host the Buffalo Bills in a crucial AFC matchup. Both teams enter with strong records, but the Chiefs' home-field advantage and recent ATS success make them slight favorites. The Bills' road struggles against the spread this season could be the difference."

### AI Spread Pick
```json
{
  "pick": "Kansas City Chiefs -3.5",
  "confidence": 72,
  "rationale": "The Chiefs are 7-2 ATS at home this season and have covered in 4 of their last 5 games. The Bills are 3-5 ATS on the road and have struggled against top-tier defenses."
}
```

### Same-Game Parlay (Safe)
```json
{
  "type": "safe",
  "title": "3-Leg Same-Game Parlay (Safe)",
  "legs": [
    {
      "matchup": "Buffalo Bills @ Kansas City Chiefs",
      "pick": "Kansas City Chiefs ML",
      "odds": "-150",
      "rationale": "Chiefs are favored to win",
      "confidence": 65.0
    },
    {
      "matchup": "Buffalo Bills @ Kansas City Chiefs",
      "pick": "Kansas City Chiefs -3.5",
      "odds": "-110",
      "rationale": "Home team covers the spread",
      "confidence": 60.0
    },
    {
      "matchup": "Buffalo Bills @ Kansas City Chiefs",
      "pick": "Over 52.5",
      "odds": "-110",
      "rationale": "Game goes over the total",
      "confidence": 55.0
    }
  ],
  "total_odds": "+600",
  "confidence": 70.0
}
```

## 🔄 Continuous Improvement

### Model Training
- AI model trainer analyzes parlay performance
- Adjusts confidence scores based on results
- Improves predictions over time

### Data Updates
- Odds sync every 5 minutes
- Stats scraper every 30 minutes
- Analysis regeneration daily

## 📈 Performance Metrics

The system tracks:
- Prediction accuracy
- Calibration error
- ATS pick success rate
- Total pick success rate
- Same-game parlay hit rate

---

**Status**: ✅ **Fully Implemented and Production-Ready**

The Covers-style AI prediction system is complete with:
- Real odds integration
- Model-based probabilities
- Same-game parlays
- SEO-optimized content
- Automated generation

