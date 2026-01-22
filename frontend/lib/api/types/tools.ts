export interface HeatmapProbabilityResponse {
  game_id: string
  home_win_prob: number
  away_win_prob: number
  spread_confidence: number | null
  total_confidence: number | null
  has_cached_analysis: boolean
}
