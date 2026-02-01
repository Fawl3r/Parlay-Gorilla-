export interface HeatmapProbabilityResponse {
  game_id: string
  home_win_prob: number
  away_win_prob: number
  spread_confidence: number | null
  total_confidence: number | null
  has_cached_analysis: boolean
}

export interface UpsetCandidateTools {
  game_id: string
  start_time: string
  league: string
  home_team: string
  away_team: string
  underdog_side: string
  underdog_team: string
  underdog_ml: number
  implied_prob: number
  model_prob: number
  edge: number
  confidence: number

  // ROI trust boosters (optional for staggered deploys)
  books_count?: number
  best_underdog_ml?: number | null
  median_underdog_ml?: number | null
  price_spread?: number | null
  worst_underdog_ml?: number | null
  flags?: string[]
  odds_quality?: "good" | "thin" | "bad"

  market_disagreement?: string | null
  reasons: string[]
}

export interface UpsetFinderToolsMeta {
  games_scanned: number
  games_with_odds: number
  missing_odds: number
  games_scanned_capped?: boolean | null
}

export interface UpsetFinderToolsAccess {
  can_view_candidates: boolean
  reason: 'login_required' | 'premium_required' | null
}

export interface UpsetFinderToolsResponse {
  sport: string
  window_days: number
  min_edge: number
  max_results: number
  min_underdog_odds: number
  generated_at: string
  access: UpsetFinderToolsAccess
  candidates: UpsetCandidateTools[]
  meta: UpsetFinderToolsMeta
  error?: string | null
}
