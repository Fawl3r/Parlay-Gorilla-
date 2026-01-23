export interface SystemStatusResponse {
  scraper_last_beat_at: string | null
  settlement_last_beat_at: string | null
  games_updated_last_run: number
  parlays_settled_today: number
  last_score_sync_at: string | null
}
