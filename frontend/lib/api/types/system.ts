export interface SystemStatusResponse {
  scraper_last_beat_at: string | null
  settlement_last_beat_at: string | null
  games_updated_last_run: number
  parlays_settled_today: number
  last_score_sync_at: string | null
}

/** GET /ops/safety or GET /api/admin/safety — Safety Mode snapshot. */
export interface SafetySnapshotResponse {
  state: 'GREEN' | 'YELLOW' | 'RED'
  reasons: string[]
  telemetry: Record<string, unknown>
  safety_mode_enabled: boolean
  /** Last N safety state transitions (v1.1). */
  events?: Array<{ ts: number; from_state: string; to_state: string; reasons: string[] }>
  /** v1.2: 0–100 deterministic health score for dashboard. */
  health_score?: number
  /** v1.2: Human-readable recommended action. */
  recommended_action?: string
}
