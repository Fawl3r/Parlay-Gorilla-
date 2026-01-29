import type { UiBetOption, UiKeyDrivers, UiMatchupCard, UiQuickTake } from "../analysisUiTypes"
import type { LegResponse } from "./parlay"

export interface SpreadPick {
  pick: string
  confidence: number
  rationale: string
}

export interface TotalPick {
  pick: string
  confidence: number
  rationale: string
}

export interface BestBet {
  bet_type: string
  pick: string
  confidence: number
  rationale: string
}

export interface ModelWinProbability {
  home_win_prob: number
  away_win_prob: number
  explanation: string
  ai_confidence?: number
  calculation_method?: string
  score_projection?: string
}

export interface MatchupEdges {
  home_advantage: string
  away_advantage: string
  key_matchup: string
}

export interface TrendAnalysis {
  home_team_trend: string
  away_team_trend: string
  analysis: string
}

export interface SameGameParlay {
  legs: LegResponse[]
  hit_probability: number
  confidence: number
}

export interface SameGameParlays {
  safe_3_leg: SameGameParlay
  balanced_6_leg: SameGameParlay
  degen_10_20_leg: SameGameParlay
}

export interface WeatherData {
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

export interface OutcomePath {
  probability: number
  description: string
  recommended_angles: string[]
}

export interface OutcomePaths {
  home_control_script: OutcomePath
  shootout_script: OutcomePath
  variance_upset_script: OutcomePath
  explanation?: string
}

export interface ConfidenceBreakdown {
  market_agreement: number
  statistical_edge: number
  situational_edge: number
  data_quality: number
  confidence_total: number
  explanation?: string
  trend?: {
    direction: "up" | "down"
    change: number
    previous: number
  }
}

export interface MarketDisagreement {
  spread_variance: "low" | "med" | "high"
  total_variance: "low" | "med" | "high"
  books_split_summary: string
  flag: "consensus" | "volatile" | "sharp_vs_public"
  explanation?: string
  sharp_indicator?: {
    has_sharp_signals: boolean
    signals?: string[]
    confidence: string
    summary: string
  }
}

export interface PortfolioGuidance {
  low_risk: string[]
  medium_risk: string[]
  high_risk: string[]
  exposure_note: string
}

export interface PropRecommendation {
  market: string
  player: string
  pick: string
  confidence: number
  why: string
  best_odds: {
    book: string
    price: string
  }
  ev_score?: number
}

export interface PropRecommendations {
  top_props: PropRecommendation[]
  notes: string
}

export interface GenerationMetadata {
  run_mode: string
  data_sources_used: {
    odds: boolean
    stats: boolean
    injuries: boolean
    weather: boolean
    form: boolean
  }
  metrics: {
    core_ms: number
    external_calls_count: number
    cache_hit: boolean
  }
}

/** UGIE v2: pillar signals (optional at runtime for older cached content). */
export interface UgieSignal {
  key: string
  value: unknown
  weight?: number
  direction?: string
  explain?: string
}

export interface UgiePillar {
  score: number
  confidence: number
  signals?: UgieSignal[]
  why_summary?: string
  top_edges?: string[]
}

export interface UgieDataQuality {
  status: "Good" | "Partial" | "Poor"
  missing?: string[]
  stale?: string[]
  provider?: string
}

export interface UgieWeatherBlock {
  weather_efficiency_modifier: number
  weather_volatility_modifier: number
  weather_confidence_modifier: number
  why?: string
  rules_fired?: string[]
}

export interface UgieV2 {
  pillars: {
    availability?: UgiePillar
    efficiency?: UgiePillar
    matchup_fit?: UgiePillar
    script_stability?: UgiePillar
    market_alignment?: UgiePillar
  }
  confidence_score: number
  risk_level: "Low" | "Medium" | "High"
  data_quality: UgieDataQuality
  recommended_action?: string
  market_snapshot?: Record<string, unknown>
  weather?: UgieWeatherBlock
}

export interface GameAnalysisContent {
  headline?: string
  subheadline?: string
  opening_summary: string
  offensive_matchup_edges: MatchupEdges
  defensive_matchup_edges: MatchupEdges
  key_stats: string[]
  ats_trends: TrendAnalysis
  totals_trends: TrendAnalysis
  weather_considerations: string
  weather_data?: WeatherData
  model_win_probability: ModelWinProbability
  ai_spread_pick: SpreadPick
  ai_total_pick: TotalPick
  best_bets: BestBet[]
  same_game_parlays: SameGameParlays
  ui_quick_take?: UiQuickTake
  ui_key_drivers?: UiKeyDrivers
  ui_bet_options?: UiBetOption[]
  ui_matchup_cards?: UiMatchupCard[]
  ui_trends?: string[]
  full_article: string
  // FREE-mode enhancements
  outcome_paths?: OutcomePaths
  confidence_breakdown?: ConfidenceBreakdown
  market_disagreement?: MarketDisagreement
  portfolio_guidance?: PortfolioGuidance
  prop_recommendations?: PropRecommendations
  delta_summary?: {
    has_changes: boolean
    line_changes?: {
      spread?: { old: number; new: number; direction: "up" | "down" }
      total?: { old: number; new: number; direction: "up" | "down" }
      moneyline?: { home_old: string; home_new: string }
    }
    injury_changes?: string[]
    pick_changes?: string[]
    summary: string
    updated_at?: string
  }
  seo_structured_data?: any
  generation?: GenerationMetadata
  ugie_v2?: UgieV2
}

export interface GameAnalysisResponse {
  id: string
  slug: string
  league: string
  matchup: string
  game_id: string
  game_time: string
  analysis_content: GameAnalysisContent
  seo_metadata?: {
    title?: string
    description?: string
    keywords?: string
  }
  generated_at: string
  expires_at?: string | null
  version: number
}

export interface GameAnalysisListItem {
  id: string
  slug: string
  league: string
  matchup: string
  game_time: string
  generated_at: string
}
