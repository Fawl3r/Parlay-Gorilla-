// Shared API response/request types

import type { UiBetOption, UiKeyDrivers, UiMatchupCard, UiQuickTake } from "./analysisUiTypes"

export interface OddsResponse {
  id: string
  outcome: string
  price: string
  decimal_price: number
  implied_prob: number
  created_at: string
}

export interface MarketResponse {
  id: string
  market_type: string
  book: string
  odds: OddsResponse[]
}

export interface GameResponse {
  id: string
  external_game_id: string
  sport: string
  home_team: string
  away_team: string
  start_time: string
  status: string
  week?: number | null // NFL week number (1-18 for regular season)
  markets: MarketResponse[]
}

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
  sport?: string // Sport for this leg (NFL, NBA, NHL, etc.)
}

export interface ParlayRequest {
  num_legs: number
  risk_profile: 'conservative' | 'balanced' | 'degen'
  sports?: string[] // List of sports to mix (e.g., ['NFL', 'NBA', 'NHL'])
  mix_sports?: boolean // Whether to mix legs from multiple sports
  week?: number // NFL week number (1-18) to build parlay from
}

export interface NFLWeekInfo {
  week: number
  label: string
  is_current: boolean
  is_available: boolean
  start_date?: string
  end_date?: string
}

export interface NFLWeeksResponse {
  current_week: number | null
  season_year: number
  weeks: NFLWeekInfo[]
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
  // Model metrics (new - for UI confidence display)
  parlay_ev?: number // Expected value of the parlay
  model_confidence?: number // Model confidence (0-1)
  upset_count?: number // Number of plus-money upset legs
  model_version?: string // Model version used
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

// Upset Finder (premium)
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
  pick: string // Team name for moneyline, 'home'/'away' for spreads, 'over'/'under' for totals
  market_type: 'h2h' | 'spreads' | 'totals'
  market_id?: string // Recommended: exact market ID (book + market instance) for precise odds resolution
  odds?: string // American odds if known
  point?: number // Spread or total line if applicable
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
}

// Counter / Hedge Parlay Types
export type CounterParlayMode = 'best_edges' | 'flip_all'

export interface CounterParlayRequest {
  legs: CustomParlayLeg[]
  target_legs?: number
  mode?: CounterParlayMode
  min_edge?: number // 0-1 (e.g. 0.02 = 2% edge)
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

// Analysis types
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
  ai_confidence?: number // Model confidence score (0-100)
  calculation_method?: string // How the probability was calculated
  score_projection?: string // Projected final score
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
  // UI-first blocks for the redesigned analysis detail page (optional)
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
  game_time: string // Actual game start time from Game table
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

// Profile & Badge types
export interface BadgeResponse {
  id: string
  name: string
  slug: string
  description?: string
  icon?: string
  requirement_type: string
  requirement_value: number
  display_order: number
  unlocked: boolean
  unlocked_at?: string
}

export interface ParlayStatsResponse {
  total_parlays: number
  by_sport: Record<string, number>
  by_risk_profile: Record<string, number>
}

export interface UserProfileData {
  id: string
  email: string
  username?: string
  display_name?: string
  leaderboard_visibility?: 'public' | 'anonymous' | 'hidden'
  avatar_url?: string
  bio?: string
  timezone?: string
  email_verified: boolean
  profile_completed: boolean
  default_risk_profile: string
  favorite_teams: string[]
  favorite_sports: string[]
  role: string
  plan: string
  created_at?: string
  last_login?: string
}

export interface ProfileResponse {
  user: UserProfileData
  stats: ParlayStatsResponse
  badges: BadgeResponse[]
}

// Subscription types
export interface SubscriptionMeResponse {
  has_subscription: boolean
  plan_id?: string
  plan_name?: string
  status: 'active' | 'trialing' | 'canceled' | 'expired' | 'free' | 'past_due'
  current_period_end?: string
  cancel_at_period_end: boolean
  provider?: string
  is_lifetime: boolean
  is_on_trial: boolean
}

export interface PaymentHistoryItem {
  id: string
  amount: number
  currency: string
  plan: string
  status: string
  provider: string
  created_at: string
  paid_at?: string
}

export interface PaymentHistoryResponse {
  payments: PaymentHistoryItem[]
  total_count: number
}

// ============================================================================
// Saved Parlays + On-chain Inscriptions
// ============================================================================

export type SavedParlayType = 'custom' | 'ai_generated'
export type InscriptionStatus = 'none' | 'queued' | 'confirmed' | 'failed'

export interface SavedParlayResponse {
  id: string
  user_id: string
  parlay_type: SavedParlayType
  title: string
  legs: any[]
  created_at: string
  updated_at: string
  version: number
  content_hash: string

  inscription_status: InscriptionStatus
  inscription_hash?: string | null
  inscription_tx?: string | null
  solscan_url?: string | null
  inscription_error?: string | null
  inscribed_at?: string | null
}

export interface SaveCustomParlayRequest {
  saved_parlay_id?: string
  title?: string
  legs: CustomParlayLeg[]
}

export interface SaveAiParlayRequest {
  saved_parlay_id?: string
  title?: string
  legs: LegResponse[]
}


// Web Push notifications
export interface WebPushVapidPublicKeyResponse {
  enabled: boolean
  public_key: string
}

export interface WebPushSubscribeRequest {
  endpoint: string
  keys: {
    p256dh: string
    auth: string
  }
  expirationTime?: number | null
}

export interface WebPushSubscribeResponse {
  success: boolean
  subscription_id: string
}

export interface WebPushUnsubscribeResponse {
  success: boolean
  deleted: number
}


