import type { CustomParlayLeg, LegResponse } from "./parlay"

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

export type SavedParlayType = 'custom' | 'ai_generated'
export type InscriptionStatus = 'none' | 'queued' | 'confirmed' | 'failed'
export type VerificationStatus = 'queued' | 'confirmed' | 'failed'

export interface VerificationRecordResponse {
  id: string
  saved_parlay_id: string | null
  status: VerificationStatus
  data_hash: string
  created_at: string
  confirmed_at?: string | null
  receipt_id?: string | null
  record_object_id?: string | null
  viewer_url: string
  error?: string | null
}

export interface SavedParlayResponse {
  id: string
  user_id: string
  parlay_type: SavedParlayType
  title: string
  legs: Array<CustomParlayLeg | LegResponse>
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
