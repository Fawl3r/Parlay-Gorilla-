"use client"

import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react'
import { useAuth } from './auth-context'
import { api } from './api'
import { LemonSqueezyAffiliateUrlBuilder } from '@/lib/lemonsqueezy/LemonSqueezyAffiliateUrlBuilder'

/**
 * Subscription status returned from backend
 */
export interface SubscriptionStatus {
  tier: 'free' | 'premium'
  plan_code: string | null
  can_use_custom_builder: boolean
  can_use_upset_finder: boolean
  can_use_multi_sport: boolean
  can_save_parlays: boolean
  max_ai_parlays_per_day: number
  remaining_ai_parlays_today: number
  unlimited_ai_parlays: boolean
  credit_balance: number
  is_lifetime: boolean
  subscription_end: string | null
  balances?: {
    credit_balance: number
    free_parlays_total: number
    free_parlays_used: number
    free_parlays_remaining: number
    daily_ai_limit: number
    daily_ai_used: number
    daily_ai_remaining: number
    premium_ai_parlays_used: number
    premium_ai_period_start: string | null

    premium_custom_builder_used: number
    premium_custom_builder_limit: number
    premium_custom_builder_remaining: number
    premium_custom_builder_period_start: string | null

    premium_inscriptions_used: number
    premium_inscriptions_limit: number
    premium_inscriptions_remaining: number
    premium_inscriptions_period_start: string | null

    ai_parlays?: {
      monthly_limit: number
      used: number
      remaining: number
    }
    custom_ai_parlays?: {
      monthly_limit: number
      used: number
      remaining: number
      inscription_cost_usd: number
      requires_manual_opt_in: boolean
    }
  }
}

/**
 * Plan information for pricing page
 */
export interface SubscriptionPlan {
  id: string
  code: string
  name: string
  description: string | null
  price_cents: number
  price_dollars: number
  currency: string
  billing_cycle: 'monthly' | 'annual' | 'lifetime'
  provider: 'lemonsqueezy' | 'coinbase'
  is_active: boolean
  is_featured: boolean
  is_free: boolean
  is_lifetime: boolean
  features: {
    max_ai_parlays_per_day: number
    unlimited_ai_parlays: boolean
    custom_builder: boolean
    upset_finder: boolean
    multi_sport: boolean
    save_parlays: boolean
    ad_free: boolean
  }
}

/**
 * Paywall error from backend
 */
export interface PaywallError {
  error_code: 'PREMIUM_REQUIRED' | 'FREE_LIMIT_REACHED' | 'PAY_PER_USE_REQUIRED' | 'LOGIN_REQUIRED'
  message: string
  remaining_today: number
  feature: string | null
  upgrade_url: string
  // Pay-per-use fields
  parlay_type?: 'single' | 'multi'
  single_price?: number
  multi_price?: number
}

interface SubscriptionContextType {
  // Status
  status: SubscriptionStatus | null
  loading: boolean
  error: string | null
  
  // Computed helpers
  isPremium: boolean
  isCreditUser: boolean
  canUseCustomBuilder: boolean
  canUseUpsetFinder: boolean
  canUseMultiSport: boolean

  creditsRemaining: number
  freeRemaining: number
  todayLimit: number
  todayUsed: number
  todayRemaining: number
  aiParlaysLimit: number
  aiParlaysUsed: number
  aiParlaysRemaining: number
  customAiParlaysLimit: number
  customAiParlaysUsed: number
  customAiParlaysRemaining: number
  inscriptionCostUsd: number
  requiresManualOptIn: boolean
  premiumInscriptionsLimit: number

  freeParlaysTotal: number
  freeParlaysUsed: number
  freeParlaysRemaining: number
  dailyAiLimit: number
  dailyAiUsed: number
  dailyAiRemaining: number
  premiumAiUsed: number
  premiumAiPeriodStart: string | null
  creditBalance: number
  
  // Actions
  refreshStatus: () => Promise<void>
  
  // Checkout
  createCheckout: (provider: 'lemonsqueezy' | 'coinbase', planCode: string) => Promise<string>
  
  // Plans
  plans: SubscriptionPlan[]
  loadPlans: () => Promise<void>
}

const defaultStatus: SubscriptionStatus = {
  tier: 'free',
  plan_code: null,
  can_use_custom_builder: false,
  can_use_upset_finder: false,
  can_use_multi_sport: false,
  can_save_parlays: false,
  max_ai_parlays_per_day: 1,
  remaining_ai_parlays_today: 1,
  unlimited_ai_parlays: false,
  credit_balance: 0,
  is_lifetime: false,
  subscription_end: null,
  balances: {
    credit_balance: 0,
    free_parlays_total: 2,
    free_parlays_used: 0,
    free_parlays_remaining: 2,
    daily_ai_limit: 1,
    daily_ai_used: 0,
    daily_ai_remaining: 1,
    premium_ai_parlays_used: 0,
    premium_ai_period_start: null,
    premium_custom_builder_used: 0,
    premium_custom_builder_limit: 0,
    premium_custom_builder_remaining: 0,
    premium_custom_builder_period_start: null,
    premium_inscriptions_used: 0,
    premium_inscriptions_limit: 0,
    premium_inscriptions_remaining: 0,
    premium_inscriptions_period_start: null,
    ai_parlays: {
      monthly_limit: 1,
      used: 0,
      remaining: 1,
    },
    custom_ai_parlays: {
      monthly_limit: 0,
      used: 0,
      remaining: 0,
      inscription_cost_usd: 0.37,
      requires_manual_opt_in: true,
    },
  },
}

const SubscriptionContext = createContext<SubscriptionContextType | undefined>(undefined)

export function SubscriptionProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const [status, setStatus] = useState<SubscriptionStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [plans, setPlans] = useState<SubscriptionPlan[]>([])

  // Fetch subscription status when user changes
  const refreshStatus = useCallback(async () => {
    if (!user) {
      setStatus(null)
      return
    }

    try {
      setLoading(true)
      setError(null)
      
      // Add cache-busting timestamp to ensure fresh data
      const response = await api.get(`/api/billing/status?t=${Date.now()}`)
      setStatus(response.data)
    } catch (err: any) {
      console.error('Failed to fetch subscription status:', err)
      // Default to free tier on error
      setStatus(defaultStatus)
      setError(err.message || 'Failed to load subscription status')
    } finally {
      setLoading(false)
    }
  }, [user])

  // Load subscription status on user change
  useEffect(() => {
    if (user) {
      refreshStatus()
    } else {
      setStatus(null)
    }
  }, [user, refreshStatus])

  // Also refresh subscription status periodically (every 5 minutes) to catch updates
  useEffect(() => {
    if (!user) return
    
    const interval = setInterval(() => {
      refreshStatus()
    }, 5 * 60 * 1000) // 5 minutes
    
    return () => clearInterval(interval)
  }, [user, refreshStatus])

  // Load available plans
  const loadPlans = useCallback(async () => {
    try {
      const response = await api.get('/api/billing/plans')
      setPlans(response.data)
    } catch (err: any) {
      console.error('Failed to fetch plans:', err)
    }
  }, [])

  // Create checkout session
  const createCheckout = useCallback(async (
    provider: 'lemonsqueezy' | 'coinbase',
    planCode: string
  ): Promise<string> => {
    const endpoint = provider === 'lemonsqueezy'
      ? '/api/billing/lemonsqueezy/checkout'
      : '/api/billing/coinbase/checkout'
    
    const response = await api.post(endpoint, { plan_code: planCode })
    const checkoutUrl = response.data.checkout_url as string
    if (provider !== 'lemonsqueezy') return checkoutUrl
    return await new LemonSqueezyAffiliateUrlBuilder().build(checkoutUrl)
  }, [])

  // Computed values
  const isPremium = status?.tier === 'premium'
  const creditBalance = status?.balances?.credit_balance ?? status?.credit_balance ?? 0
  const isCreditUser = !isPremium && creditBalance > 0
  const canUseCustomBuilder = status?.can_use_custom_builder ?? false
  const canUseUpsetFinder = status?.can_use_upset_finder ?? false
  const canUseMultiSport = status?.can_use_multi_sport ?? false

  // New balances (with backwards-compatible fallbacks)
  const freeParlaysTotal = status?.balances?.free_parlays_total ?? 2
  const freeParlaysUsed = status?.balances?.free_parlays_used ?? 0
  const freeParlaysRemaining = status?.balances?.free_parlays_remaining ?? Math.max(0, freeParlaysTotal - freeParlaysUsed)

  const dailyAiLimit = status?.balances?.daily_ai_limit ?? status?.max_ai_parlays_per_day ?? 1
  const dailyAiRemaining = status?.balances?.daily_ai_remaining ?? status?.remaining_ai_parlays_today ?? 1
  const dailyAiUsed = status?.balances?.daily_ai_used ?? (dailyAiLimit >= 0 ? Math.max(0, dailyAiLimit - dailyAiRemaining) : 0)

  const premiumAiUsed = status?.balances?.premium_ai_parlays_used ?? 0
  const premiumAiPeriodStart = status?.balances?.premium_ai_period_start ?? null

  const aiParlaysLimit = status?.balances?.ai_parlays?.monthly_limit ?? dailyAiLimit
  const aiParlaysUsed = status?.balances?.ai_parlays?.used ?? (isPremium ? premiumAiUsed : dailyAiUsed)
  const aiParlaysRemaining = status?.balances?.ai_parlays?.remaining ?? dailyAiRemaining

  const customAiParlaysLimit = status?.balances?.custom_ai_parlays?.monthly_limit ?? 0
  const customAiParlaysUsed = status?.balances?.custom_ai_parlays?.used ?? 0
  const customAiParlaysRemaining = status?.balances?.custom_ai_parlays?.remaining ?? 0
  const inscriptionCostUsd = status?.balances?.custom_ai_parlays?.inscription_cost_usd ?? 0.37
  const requiresManualOptIn = status?.balances?.custom_ai_parlays?.requires_manual_opt_in ?? true
  const premiumInscriptionsLimit = status?.balances?.premium_inscriptions_limit ?? 0

  const creditsRemaining = creditBalance
  const freeRemaining = freeParlaysRemaining
  const todayLimit = isPremium ? 0 : dailyAiLimit
  const todayUsed = isPremium ? 0 : dailyAiUsed
  const todayRemaining = isPremium ? 0 : dailyAiRemaining

  return (
    <SubscriptionContext.Provider
      value={{
        status,
        loading,
        error,
        isPremium,
        isCreditUser,
        canUseCustomBuilder,
        canUseUpsetFinder,
        canUseMultiSport,
        creditsRemaining,
        freeRemaining,
        todayLimit,
        todayUsed,
        todayRemaining,
        aiParlaysLimit,
        aiParlaysUsed,
        aiParlaysRemaining,
        customAiParlaysLimit,
        customAiParlaysUsed,
        customAiParlaysRemaining,
        inscriptionCostUsd,
        requiresManualOptIn,
        premiumInscriptionsLimit,
        freeParlaysTotal,
        freeParlaysUsed,
        freeParlaysRemaining,
        dailyAiLimit,
        dailyAiUsed,
        dailyAiRemaining,
        premiumAiUsed,
        premiumAiPeriodStart,
        creditBalance,
        refreshStatus,
        createCheckout,
        plans,
        loadPlans,
      }}
    >
      {children}
    </SubscriptionContext.Provider>
  )
}

export function useSubscription() {
  const context = useContext(SubscriptionContext)
  if (context === undefined) {
    throw new Error('useSubscription must be used within a SubscriptionProvider')
  }
  return context
}

/**
 * Helper to check if an error is a paywall error
 */
export function isPaywallError(error: any): error is { response: { data: PaywallError } } {
  return (
    error?.response?.status === 402 &&
    error?.response?.data?.error_code &&
    ['PREMIUM_REQUIRED', 'FREE_LIMIT_REACHED', 'PAY_PER_USE_REQUIRED', 'LOGIN_REQUIRED'].includes(
      error.response.data.error_code
    )
  )
}

/**
 * Extract paywall error details from API error
 */
export function getPaywallError(error: any): PaywallError | null {
  if (isPaywallError(error)) {
    return error.response.data
  }
  return null
}

