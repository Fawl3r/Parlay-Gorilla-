# Parlay Gorilla — Universal Game Intelligence Engine (UGIE)

## Objective

Define a single sport-agnostic game analysis engine that powers advanced analytics for all supported sports. The system must:

- Use API-Sports where available; fall back to ESPN or internal/odds-only when data is thinner.
- Normalize sport-specific data into universal metrics.
- Produce consistent, explainable analysis across sports.
- Scale as new sports are added without rewriting core logic.

**Related code:** [backend/app/services/analysis/analysis_orchestrator.py](backend/app/services/analysis/analysis_orchestrator.py), [backend/app/services/analysis/core_analysis_generator.py](backend/app/services/analysis/core_analysis_generator.py), [backend/app/services/model_win_probability.py](backend/app/services/model_win_probability.py), [frontend/lib/api/types/analysis.ts](frontend/lib/api/types/analysis.ts). See also [GAME_ANALYSIS_SYSTEM_DOCUMENTATION.md](GAME_ANALYSIS_SYSTEM_DOCUMENTATION.md).

---

## Core Principle

Stop thinking in terms of "NFL logic" or "NBA logic." Instead:

**Universal Game Intelligence Engine (UGIE)**  
Sport-specific data → normalized → sport-agnostic reasoning → sport-specific output.

Every sport feeds into the same analytical pillars; only the data mapping and copy are sport-specific.

---

## Canonical UGIE Output Schema

The engine outputs a normalized structure that the frontend can render consistently. (Today's payload lives in `analysis_content`; UGIE can extend it with a `pillars` block.)

### Pillars (each 0–1 score, confidence, signals, why)

| Pillar | Description | Example outputs |
|--------|-------------|-----------------|
| **availability** | Injuries, absences, key personnel | Availability Impact Score |
| **efficiency** | Normalized efficiency metrics (not raw PPG) | Efficiency Delta |
| **matchup_fit** | Style vs style, key matchup edges | Matchup Advantage Score |
| **script_stability** | Blowout risk, close-game volatility, garbage time | Script Stability Score |
| **market_alignment** | Model vs sportsbook implied prob, line movement | Edge Strength |

Per-pillar shape (JSON-ish):

```json
{
  "pillars": {
    "availability": {
      "score_0_to_1": 0.72,
      "confidence_0_to_1": 0.85,
      "signals": ["home_injuries_light", "away_key_out"],
      "why_summary": "Home at full strength; away missing starter."
    },
    "efficiency": { "score_0_to_1": 0.58, "confidence_0_to_1": 0.9, "signals": [], "why_summary": "..." },
    "matchup_fit": { "..." },
    "script_stability": { "..." },
    "market_alignment": { "..." }
  },
  "overall": {
    "confidence_score": 0.65,
    "risk_level": "medium",
    "data_quality": "high"
  }
}
```

- **score_0_to_1**: Direction and magnitude of the factor (e.g. favor home, favor under).
- **confidence_0_to_1**: How much we trust this pillar given data availability.
- **signals**: Short machine-readable tags used to generate copy.
- **why_summary**: One or two sentences for the UI.

**Existing payload keys** that already align with pillars (see [frontend/lib/api/types/analysis.ts](frontend/lib/api/types/analysis.ts)): `model_win_probability`, `opening_summary`, `offensive_matchup_edges`, `defensive_matchup_edges`, `ats_trends`, `totals_trends`, `weather_considerations`, `weather_data`, `confidence_breakdown`, `market_disagreement`, `best_bets`, `ai_spread_pick`, `ai_total_pick`.

---

## Where Each Pillar Plugs Into Today's Pipeline

No code changes in this doc—only mapping of current responsibilities to pillars.

| Pillar | Current source | Notes |
|--------|----------------|-------|
| **availability** | [backend/app/services/stats_scraper.py](backend/app/services/stats_scraper.py) (injuries), matchup_data `home_injuries` / `away_injuries` | Data quality flags in `matchup_data`: `home_data_quality`, `away_data_quality`. |
| **efficiency** | Team stats from StatsScraperService / feature pipeline; normalized in probability engine | Avoid raw PPG in user-facing copy; use efficiency deltas. |
| **matchup_fit** | [backend/app/services/analysis/core_analysis_edges.py](backend/app/services/analysis/core_analysis_edges.py) (`offensive_matchup_edges`, `defensive_matchup_edges`) | Style vs style; key matchup bullets. |
| **script_stability** | [backend/app/services/analysis/builders/outcome_paths_builder.py](backend/app/services/analysis/builders/outcome_paths_builder.py), model win prob spread | Blowout / close / variance scripts. |
| **market_alignment** | [backend/app/services/model_win_probability.py](backend/app/services/model_win_probability.py), [backend/app/services/analysis/builders/confidence_breakdown_builder.py](backend/app/services/analysis/builders/confidence_breakdown_builder.py), [backend/app/services/analysis/builders/market_disagreement_builder.py](backend/app/services/analysis/builders/market_disagreement_builder.py) | Model vs market, line movement, sharp signals. |

`compute_game_win_probability` already consumes `matchup_data` (stats, injuries, weather) and odds; its `ai_confidence` and `calculation_method` feed overall confidence and risk level.

---

## Sport Adapter Contract

Adapters **translate only**; they do **not** contain betting logic.

- **Inputs (per sport):** Raw stats, injuries, odds, weather (and optionally form/standings) from API-Sports, ESPN, or internal DB.
- **Outputs:** Normalized features for the core engine, e.g.:
  - Availability: list of key absences, severity, unit affected.
  - Efficiency: normalized rates (e.g. points per possession, goals per shot) for home/away.
  - Matchup: tags for style (e.g. pace, pass/run, press intensity).
  - Script: volatility tag, blowout risk tag.
  - Market: implied probs, line movement summary.

Adapters must degrade gracefully: missing data → lower confidence for that pillar, not invented numbers.

---

## Per-Sport Mapping (Data Sources & Thin-Data Mode)

Supported sports are defined in [backend/app/services/sports_config.py](backend/app/services/sports_config.py) and [backend/app/services/sports/sport_registry.py](backend/app/services/sports/sport_registry.py).

| Sport | Primary data | Fallback | Notes |
|-------|--------------|----------|--------|
| **NFL** | API-Sports (americanfootball_nfl), ESPN | Odds-only | Injuries, yards/play, pressure, red zone, weather (outdoor). |
| **NBA / WNBA** | API-Sports (basketball_nba), ESPN | Odds-only | Pace, O/D rating, on/off, rest, minutes. |
| **NHL** | API-Sports (icehockey_nhl), ESPN | Odds-only | Goalie, Corsi/Fenwick, special teams. |
| **MLB** | API-Sports (baseball_mlb), ESPN | Odds-only | SP, bullpen, OPS vs handedness, park, weather. |
| **NCAAF** | ESPN, odds | Odds-only | Same pillars as NFL; fewer injury/weather sources. |
| **NCAAB** | ESPN, odds | Odds-only | Same pillars as NBA; thinner team stats. |
| **EPL / MLS / LaLiga / UCL / soccer** | API-Sports (football), ESPN | Odds-only | xG/xGA, possession, press, injuries/suspensions. |

**Thin-data mode (UFC, Boxing):**

- **availability**: Usually N/A (no pre-fight injury feed); set confidence to 0 or omit.
- **efficiency**: Use historical finish rates / rounds if available; else odds-only.
- **matchup_fit**: Style (striker vs grappler, etc.) if available; else omit.
- **script_stability**: Round/finish variance from odds.
- **market_alignment**: Model vs market from odds only.

For UFC/Boxing, overall confidence should be reduced and risk_level elevated when pillars are missing; never fabricate stats.

---

## Quality Rules

1. **Missing data → reduce confidence.** If a pillar has no inputs, set `confidence_0_to_1` low or omit the pillar; do not guess.
2. **No raw-PPG language in user-facing copy.** Explain edges via normalized efficiency, matchup fit, and market alignment (e.g. "points per possession advantage" not "averages 28 PPG").
3. **Always emit "why" for each pillar.** At least one sentence tying signals to conclusion (e.g. "Pass-heavy offense vs low pressure → efficiency edge").
4. **Never duplicate offense/defense language.** One clear edge per side per pillar where applicable.
5. **Data quality flags.** Use existing `data_sources_used` (stats, injuries, weather, form) in generation metadata so the UI can show "Limited data" when appropriate (see [frontend/lib/analysis/detail/AnalysisDetailViewModelBuilder.ts](frontend/lib/analysis/detail/AnalysisDetailViewModelBuilder.ts) `limitedDataNote`).

---

## UI Mapping (Analysis Detail Page)

The analysis detail page is built from `GameAnalysisResponse.analysis_content` and view model from [frontend/lib/analysis/detail/AnalysisDetailViewModelBuilder.ts](frontend/lib/analysis/detail/AnalysisDetailViewModelBuilder.ts). Components live under [frontend/app/analysis/[...slug]](frontend/app/analysis/[...slug]) and [frontend/components/analysis/detail](frontend/components/analysis/detail).

| Page section | Content source | UGIE pillar(s) |
|--------------|----------------|-----------------|
| Header / matchup | `matchup`, `analysis_content.headline` | — |
| Quick Take | `ui_quick_take` or derived from `model_win_probability`, picks | overall confidence, risk_level; market_alignment |
| Key drivers | `ui_key_drivers` or `key_stats`, `opening_summary` | availability, efficiency, matchup_fit |
| Matchup cards | `offensive_matchup_edges`, `defensive_matchup_edges`, `ui_matchup_cards` | matchup_fit |
| Trends | `ats_trends`, `totals_trends`, `weather_considerations`, `ui_trends` | efficiency, script_stability, weather (if present) |
| Bet options | `ai_spread_pick`, `ai_total_pick`, `ui_bet_options` | market_alignment, script_stability |
| Outcome paths | `outcome_paths` | script_stability |
| Confidence breakdown | `confidence_breakdown` | overall confidence, market_alignment |
| Weather | `weather_considerations`, `weather_data` | availability / efficiency modifier (see Weather doc) |
| Best bets | `best_bets` | All pillars summarized |

The page should feel like: "An AI analyst broke this game down end-to-end." Consistency across sports means same sections, sport-specific language and metrics.

---

## Frontend Requirements (From Spec)

Each game detail page must include:

- Injury/availability impact summary (pillar: availability).
- Key matchup mismatches (pillar: matchup_fit).
- Game script explanation (pillar: script_stability).
- Confidence score with explanation (overall + per-pillar confidence).
- Best bet reasoning tied to data (signals → why_summary).

Remove generic PPG-based language in favor of normalized efficiency and matchup explanations.
