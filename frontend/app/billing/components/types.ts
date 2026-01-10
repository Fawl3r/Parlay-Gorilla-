export interface AccessStatus {
  free: {
    total: number
    used: number
    remaining: number
  }
  subscription: {
    active: boolean
    plan: string | null
    daily_limit: number
    used_today: number
    remaining_today: number
    is_lifetime?: boolean
  }
  custom_builder?: {
    used: number
    limit: number
    remaining: number
    period_start: string | null
  }
  inscriptions?: {
    used: number
    limit: number
    remaining: number
    period_start: string | null
  }
  credits: {
    balance: number
    standard_cost: number
    elite_cost: number
  }
  can_generate: {
    standard: boolean
    elite: boolean
  }
}

export interface CreditPack {
  id: string
  name: string
  credits: number
  bonus_credits: number
  total_credits: number
  price: number
  price_cents: number
  price_per_credit: number
  is_featured: boolean
}

export interface SubscriptionPlan {
  id: string
  name: string
  description: string
  price: number
  period: string
  daily_parlay_limit: number
  features: string[]
  is_featured: boolean
}

export type CheckoutProvider = 'stripe' | 'lemonsqueezy'


