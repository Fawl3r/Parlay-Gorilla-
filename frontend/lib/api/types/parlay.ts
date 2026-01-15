// Parlay types
export interface LegResponse {
  market_id: string
  outcome: string
  game: string
  home_team?: string
  away_team?: string
  market_type: string
  odds: string
  probability: number
  confidence: number
  sport?: string
}

export interface ParlayRequest {
  num_legs: number
  risk_profile: 'conservative' | 'balanced' | 'degen'
  sports?: string[]
  mix_sports?: boolean
  week?: number
}

export interface ParlayResponse {
  id: string
  legs: LegResponse[]
  num_legs: number
  parlay_hit_prob: number
  risk_profile: string
  confidence_scores: number[]
  overall_confidence: number
  ai_summary: string
  ai_risk_notes: string
  confidence_meter: {
    score: number
    color: string
  }
  parlay_ev?: number
  model_confidence?: number
  upset_count?: number
  model_version?: string
}

export interface TripleParlayRequest {
  sports?: string[]
  safe_legs?: number
  balanced_legs?: number
  degen_legs?: number
}

export interface TripleParlayMetadata {
  num_legs: number
  risk_profile: string
  sport: string
  confidence_floor: number
  leg_range: [number, number]
  highlight_leg?: string
}

export interface TripleParlayResponse {
  safe: ParlayResponse
  balanced: ParlayResponse
  degen: ParlayResponse
  metadata: Record<'safe' | 'balanced' | 'degen', TripleParlayMetadata>
}

export type UpsetRiskTier = 'low' | 'medium' | 'high'

export interface UpsetCandidateResponse {
  team: string
  opponent: string
  sport: string
  market_type: string
  model_prob: number
  implied_prob: number
  edge: number
  edge_percentage: number
  odds: number
  risk_tier: UpsetRiskTier
  confidence_score: number
  ev: number
  plus_money: boolean
  game_id?: string | null
  game_time?: string | null
  reasoning?: string
}

export interface UpsetFinderResponse {
  sport: string
  count: number
  upsets: UpsetCandidateResponse[]
}

// Custom Parlay Builder Types
export interface CustomParlayLeg {
  game_id: string
  pick: string
  market_type: 'h2h' | 'spreads' | 'totals'
  market_id?: string
  odds?: string
  point?: number
}

export interface CustomParlayRequest {
  legs: CustomParlayLeg[]
}

export interface CustomParlayLegAnalysis {
  game_id: string
  game: string
  home_team: string
  away_team: string
  sport: string
  market_type: string
  pick: string
  pick_display: string
  odds: string
  decimal_odds: number
  implied_probability: number
  ai_probability: number
  confidence: number
  edge: number
  recommendation: 'strong' | 'moderate' | 'weak' | 'avoid'
}

export interface VerificationRecordSummary {
  id: string
  status: string
  viewer_url: string
}

export interface CustomParlayAnalysisResponse {
  legs: CustomParlayLegAnalysis[]
  num_legs: number
  combined_implied_probability: number
  combined_ai_probability: number
  overall_confidence: number
  confidence_color: 'green' | 'yellow' | 'red'
  parlay_odds: string
  parlay_decimal_odds: number
  ai_summary: string
  ai_risk_notes: string
  ai_recommendation: 'strong_play' | 'solid_play' | 'risky_play' | 'avoid'
  weak_legs: string[]
  strong_legs: string[]
  verification?: VerificationRecordSummary | null
}

// Counter / Hedge Parlay Types
export type CounterParlayMode = 'best_edges' | 'flip_all'

export interface CounterParlayRequest {
  legs: CustomParlayLeg[]
  target_legs?: number
  mode?: CounterParlayMode
  min_edge?: number
}

export interface CounterLegCandidate {
  game_id: string
  market_type: string
  original_pick: string
  counter_pick: string
  counter_odds?: string | null
  counter_ai_probability: number
  counter_confidence: number
  counter_edge: number
  score: number
  included: boolean
}

export interface CounterParlayResponse {
  counter_legs: CustomParlayLeg[]
  counter_analysis: CustomParlayAnalysisResponse
  candidates: CounterLegCandidate[]
}

// Coverage Pack Types (upset possibilities + up to 20 tickets)
export interface CoverageTicket {
  legs: CustomParlayLeg[]
  num_upsets: number
  analysis: CustomParlayAnalysisResponse
}

export interface ParlayCoverageRequest {
  legs: CustomParlayLeg[]
  max_total_parlays?: number
  scenario_max?: number
  round_robin_max?: number
  round_robin_size?: number
}

export interface ParlayCoverageResponse {
  num_games: number
  total_scenarios: number
  by_upset_count: Record<string, number>
  scenario_tickets: CoverageTicket[]
  round_robin_tickets: CoverageTicket[]
}
