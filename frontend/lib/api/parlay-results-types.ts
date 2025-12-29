export type ParlayLegStatus = 'hit' | 'missed' | 'push' | 'pending'

export interface ParlayLegOutcome {
  market_id?: string | null
  game_id?: string | null
  market_type?: string | null
  outcome?: string | null
  game?: string | null
  home_team?: string | null
  away_team?: string | null
  sport?: string | null
  odds?: string | null
  probability?: number | null
  confidence?: number | null

  status: ParlayLegStatus
  hit?: boolean | null
  notes?: string | null
  home_score?: number | null
  away_score?: number | null
  line?: number | null
  selection?: string | null
}

export interface ParlayHistoryItem {
  id: string
  created_at?: string | null
  num_legs: number
  risk_profile: string
  parlay_hit_prob: number
  status: ParlayLegStatus
  legs: ParlayLegOutcome[]
}

export interface ParlayDetail {
  id: string
  created_at?: string | null
  num_legs: number
  risk_profile: string
  parlay_hit_prob: number
  ai_summary?: string | null
  ai_risk_notes?: string | null
  status: ParlayLegStatus
  legs: ParlayLegOutcome[]
}


