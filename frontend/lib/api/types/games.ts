export interface GameFeedResponse {
  id: string
  sport: string
  home_team: string
  away_team: string
  start_time: string
  status: string
  home_score: number | null
  away_score: number | null
  period: string | null
  clock: string | null
  is_stale: boolean
}
