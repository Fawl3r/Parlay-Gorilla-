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
