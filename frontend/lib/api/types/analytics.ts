export interface AnalyticsGameResponse {
  game_id: string
  matchup: string
  home_team: string
  away_team: string
  sport: string
  start_time: string
  slug: string | null
  home_win_prob: number | null
  away_win_prob: number | null
  spread_confidence: number | null
  total_confidence: number | null
  has_cached_analysis: boolean
  is_trending: boolean
  traffic_score: number
  confidence_threshold?: number
}

export interface AnalyticsSnapshotResponse {
  games_tracked_today: number
  model_accuracy_last_100: number | null
  high_confidence_games: number
  trending_matchup: string | null
}

export interface AnalyticsResponse {
  snapshot: AnalyticsSnapshotResponse
  games: AnalyticsGameResponse[]
  total_games: number
}
