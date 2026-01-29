# Parlay Gorilla — Weather Intelligence Engine

## Objective

Integrate weather as a first-class analytical modifier for NFL, MLB, and Soccer game analysis. Weather must influence:

- Efficiency metrics (passing, shooting, ball carry).
- Game script stability (volatility, late-game variance).
- Totals confidence (Over/Under).
- Overall model confidence.

Weather is **not** a standalone silo; it is a modifier layer that feeds into existing UGIE pillars (see [PARLAY_GORILLA_GAME_ANALYSIS_V2.md](PARLAY_GORILLA_GAME_ANALYSIS_V2.md)).

**Related code:** [backend/app/services/data_fetchers/weather.py](backend/app/services/data_fetchers/weather.py), [backend/app/services/stats_scraper.py](backend/app/services/stats_scraper.py) (weather fetch + impact assessment), [backend/app/services/analysis/core_analysis_generator.py](backend/app/services/analysis/core_analysis_generator.py) (`_build_weather_considerations`, `weather_data` in matchup_data). Frontend contract: [frontend/lib/api/types/analysis.ts](frontend/lib/api/types/analysis.ts) (`WeatherData`, `weather_considerations`, `weather_data`).

---

## Where Weather Lives in the System

Weather is a **modifier layer** that feeds into three existing pillars:

| Pillar | Weather modifier | Effect |
|--------|------------------|--------|
| **Efficiency Delta** | `weather_efficiency_modifier` | Adjusts passing/shooting/run efficiency (e.g. wind > 15 mph → passing downgrade). |
| **Game Script Stability** | `weather_volatility_modifier` | Increases or decreases late-game variance (e.g. bad weather → higher variance). |
| **Market Edge Strength** | `weather_confidence_modifier` | Reduces confidence when weather uncertainty is high. |

Formula (conceptual):

- `adjusted_efficiency = base_efficiency * weather_efficiency_modifier`
- `script_stability *= weather_volatility_modifier`
- `confidence *= weather_confidence_modifier`

Bad weather generally: lower confidence, higher variance, lower totals, higher upset risk.

---

## Weather Inputs (Canonical)

Aligned with current payload and fetchers.

| Variable | Type | Why it matters |
|----------|------|----------------|
| **temperature** | number (°F) | Fatigue, pace, late-game efficiency; cold/heat extremes. |
| **wind_speed** | number (mph) | Passing, kicking, shooting accuracy. |
| **wind_direction** | number (deg) | Directional impact (e.g. wind out to RF in MLB). |
| **precipitation** | number / condition | Ball control, scoring suppression, run rate (NFL). |
| **humidity** | number (%) | Endurance, ball flight (MLB). |
| **condition** / **description** | string | Rain, snow, clear, etc. |
| **is_outdoor** | boolean | Dome/indoor → weather neutralized. |
| **affects_game** | boolean | Whether to apply modifiers at all. |

**Current payload shape** ([frontend/lib/api/types/analysis.ts](frontend/lib/api/types/analysis.ts)):

```ts
interface WeatherData {
  temperature?: number
  feels_like?: number
  condition?: string
  description?: string
  wind_speed?: number
  wind_direction?: number
  humidity?: number
  precipitation?: number
  is_outdoor?: boolean
  affects_game?: boolean
}
```

**Current fetchers:** [backend/app/services/data_fetchers/weather.py](backend/app/services/data_fetchers/weather.py) (OpenWeatherMap forecast by stadium coords, NFL stadium list, indoor/dome set); [backend/app/services/stats_scraper.py](backend/app/services/stats_scraper.py) (`get_weather_data`, `_assess_weather_impact`, `_assess_weather_impact_from_data`).

---

## Weather Impact Engine (Target Design)

A single module **WeatherImpactEngine** that:

1. Consumes normalized weather data (same shape as `WeatherData`).
2. Applies sport-specific impact weights and rules.
3. Outputs three modifiers used by the core model:
   - **weather_efficiency_modifier** (e.g. 0.85–1.0; &lt; 1 = efficiency downgrade).
   - **weather_volatility_modifier** (e.g. 1.0–1.3; &gt; 1 = higher script variance).
   - **weather_confidence_modifier** (e.g. 0.7–1.0; &lt; 1 = reduce confidence).

Dome/indoor or `is_outdoor === false` → all modifiers neutral (1.0, 1.0, 1.0). Missing data → `weather_confidence_modifier` &lt; 1.

---

## Sport-Specific Logic

### NFL

- **Wind &gt; 15 mph** → Passing efficiency reduced; kicking variance up.
- **Rain / snow** → Run rate increases; passing downgrade.
- **Cold + wind** → Under bias; late-game fatigue variance.
- **Dome / indoor** → Weather neutralized (no modifiers).

Example output (narrative): "Wind 18 mph → Passing efficiency reduced. Temp 29°F → Slower pace, fatigue risk. Field: outdoor grass. Net: Under favored; spread volatility increased."

### MLB

- **Warm air + wind out** → HR boost (ball carry).
- **Cold air + wind in** → Suppressed offense.
- **Rain** → Bullpen volatility; possible delay risk.
- **Humidity** → Ball flight variance.

Example output: "Temp 82°F → Increased ball carry. Wind 12 mph out to RF → Home run boost. Humidity high. Net: Over favored; power hitters benefit; bullpen exposure risk elevated."

### Soccer (EPL, MLS, etc.)

- **Heavy rain** → Slower buildup, fewer shots; passing accuracy down.
- **Heat** → Reduced press, more subs; late goals less likely.
- **Wind** → Set-piece variance.
- **Poor pitch** → Long-ball bias.

Example output: "Rain: heavy → Reduced passing precision. Pitch: wet. Temp 88°F → Fatigue risk. Net: Under favored; high-press teams downgraded; late goals less likely."

### NBA / NHL

- Indoor; weather does **not** apply. Engine returns neutral modifiers and no narrative.

---

## Model Integration

Weather modifiers are applied **after** base pillar computation:

- **Efficiency pillar:** Multiply efficiency delta (or equivalent) by `weather_efficiency_modifier`.
- **Script stability pillar:** Multiply script stability score by `weather_volatility_modifier` (inverse so higher volatility = lower stability).
- **Confidence:** Multiply overall confidence by `weather_confidence_modifier`.

If weather data is missing or uncertain (e.g. forecast &gt; 24 h out), set `weather_confidence_modifier` &lt; 1 so that overall confidence is reduced and risk level can be elevated.

---

## Current vs Target Integration

| Current | Target |
|--------|--------|
| [backend/app/services/data_fetchers/weather.py](backend/app/services/data_fetchers/weather.py): Fetches by home_team + game_time; NFL stadium coords + indoor set. | WeatherImpactEngine consumes same `WeatherData` shape; no change to fetch contract. |
| [backend/app/services/stats_scraper.py](backend/app/services/stats_scraper.py): `get_weather_data` (city/state), `_assess_weather_impact` (narrative). | Engine produces modifiers + optional narrative; narrative can replace or supplement `_assess_weather_impact`. |
| [backend/app/services/analysis/core_analysis_generator.py](backend/app/services/analysis/core_analysis_generator.py): `_build_weather_considerations(matchup_data)` → string; `weather_data` in draft. | Core generator calls WeatherImpactEngine with `matchup_data.weather`; injects modifiers into model/pillar pipeline and keeps `weather_considerations` / `weather_data` for UI. |

Existing payload keys **unchanged**: `weather_considerations` (string), `weather_data` (WeatherData). New keys (optional): `weather_modifiers`: `{ efficiency_modifier, volatility_modifier, confidence_modifier }` for debugging or UI.

---

## Frontend Display Requirements

Weather should appear in three places:

1. **Quick Take (auto-adjusted)**  
   One sentence, e.g. "Weather favors lower scoring and increases spread volatility."

2. **Dedicated Weather Impact module**  
   - Title: "Weather Impact"
   - Fields: wind, temperature, precipitation (and optionally humidity, condition).
   - Impact: 2–3 bullets (e.g. "Passing efficiency reduced", "Under conditions favored", "Increased variance late").

3. **Confidence explanation**  
   If `weather_confidence_modifier` &lt; 1: "Model confidence reduced slightly due to weather volatility."

Weather must never be decorative; it must affect efficiency, script, or confidence in the model and in the copy.
