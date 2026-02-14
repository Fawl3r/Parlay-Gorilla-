import type { GameResponse } from './core'

/** Sport state from backend (no hardcoded dates). */
export type SportState =
  | 'OFFSEASON'
  | 'PRESEASON'
  | 'IN_SEASON'
  | 'IN_BREAK'
  | 'POSTSEASON'

export interface SportListItem {
  slug: string
  code: string
  display_name: string
  default_markets: string[]
  in_season?: boolean
  status_label?: string
  upcoming_games?: number
  sport_state?: SportState
  next_game_at?: string | null
  last_game_at?: string | null
  state_reason?: string
  /** If false, hide or disable sport tab and parlay builder for this sport. */
  is_enabled?: boolean
  /** Days until next game (for badge e.g. "Unlocks in X days"). */
  days_to_next?: number | null
  /** Preseason enable window in days (backend policy). */
  preseason_enable_days?: number | null
}

/** Response from GET /api/sports/{sport}/games (and /games/quick). */
export interface GamesListResponse {
  games: GameResponse[]
  sport_state?: string | null
  next_game_at?: string | null
  status_label?: string | null
  days_to_next?: number | null
  preseason_enable_days?: number | null
}

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
