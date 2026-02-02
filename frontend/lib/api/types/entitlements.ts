/** GET /api/me/entitlements response (single source of truth for UI). */
export interface EntitlementsCredits {
  ai_picks_remaining: number
  gorilla_builder_remaining: number
}

export interface EntitlementsFeatures {
  mix_sports: boolean
  max_legs: number
  player_props: boolean
}

export interface EntitlementsResponse {
  is_authenticated: boolean
  plan: 'anon' | 'free' | 'premium'
  credits: EntitlementsCredits
  features: EntitlementsFeatures
}
