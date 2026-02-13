export interface SystemStatusResponse {
  scraper_last_beat_at: string | null
  settlement_last_beat_at: string | null
  games_updated_last_run: number
  parlays_settled_today: number
  last_score_sync_at: string | null
}

/** GET /ops/safety — Safety Mode snapshot (state, reasons, telemetry, events). */
export interface SafetySnapshotResponse {
  state: 'GREEN' | 'YELLOW' | 'RED'
  reasons: string[]
  telemetry: Record<string, unknown>
  safety_mode_enabled: boolean
  /** Last N safety state transitions (v1.1). */
  events?: Array<{ ts: number; from_state: string; to_state: string; reasons: string[] }>
}
