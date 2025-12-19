export interface AffiliateAccount {
  id: string
  referral_code: string
  referral_url: string
  tier: string
  commission_rates: {
    subscription_first: number
    subscription_recurring: number
    credits: number
  }
  stats: {
    total_clicks: number
    total_referrals: number
    total_referred_revenue: number
    total_commission_earned: number
    total_commission_paid: number
    pending_commission: number
  }
  payout_email: string | null
  payout_method: string | null
  created_at: string
}

export interface AffiliateStats {
  total_clicks: number
  total_referrals: number
  total_revenue: number
  total_commission_earned: number
  total_commission_paid: number
  pending_commission: number
  conversion_rate: number
  settlement_breakdown?: {
    internal?: { earned: number; paid: number; pending: number }
    lemonsqueezy?: { earned: number; paid: number; pending: number }
  }
  last_30_days: {
    clicks: number
    referrals: number
    revenue: number
  }
}

export interface Referral {
  id: string
  username: string | null
  email: string
  created_at: string
  has_subscription: boolean
}

export interface Commission {
  id: string
  sale_type: string
  base_amount: number
  amount: number
  status: string
  days_until_ready: number
  created_at: string
  subscription_plan: string | null
  credit_pack_id: string | null
  settlement_provider?: string
}

export type DashboardTabId = "overview" | "referrals" | "commissions"


