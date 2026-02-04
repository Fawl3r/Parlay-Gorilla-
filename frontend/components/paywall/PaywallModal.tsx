"use client"

import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Crown, Shield, Sparkles, Coins, DollarSign } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useSubscription, PaywallError } from '@/lib/subscription-context'
import { cn } from '@/lib/utils'
import { redirectToCheckout, PARLAY_PRICING, formatPrice, ParlayType } from '@/lib/parlay-purchase'
import { ClientPortal } from "@/components/ui/ClientPortal"
import {
  CREDITS_COST_CUSTOM_BUILDER_ACTION,
} from '@/lib/pricingConfig'
import { PAYWALL_PREMIUM_BENEFITS, PAYWALL_REASON_CONTENT, type PaywallReason } from './paywallContent'
import { trackPremiumUpsellShown, trackPremiumUpgradeClicked } from '@/lib/track-event'
import type { PremiumUpsellTrigger, PremiumUpsellVariant } from '@/lib/track-event'

export type { PaywallReason } from "./paywallContent"

interface PaywallModalProps {
  isOpen: boolean
  onClose: () => void
  reason: PaywallReason
  featureName?: string
  error?: PaywallError | null
  parlayType?: 'single' | 'multi'  // For pay-per-use context
  singlePrice?: number
  multiPrice?: number
  premiumUpsellTrigger?: PremiumUpsellTrigger
  premiumUpsellVariant?: PremiumUpsellVariant
}

export function PaywallModal({ isOpen, onClose, reason, featureName, error, parlayType, singlePrice, multiPrice, premiumUpsellTrigger, premiumUpsellVariant = 'A' }: PaywallModalProps) {
  const router = useRouter()
  const upsellShownFiredRef = useRef(false)
  const {
    createCheckout,
    loadPlans,
    plans,
    isPremium,
    creditsRemaining,
    freeRemaining,
    todayRemaining,
    todayLimit,
    aiParlaysRemaining,
    aiParlaysLimit,
    customAiParlaysRemaining,
    customAiParlaysLimit,
    inscriptionCostUsd,
  } = useSubscription()
  const [loading, setLoading] = useState<string | null>(null)

  const content = PAYWALL_REASON_CONTENT[reason] || PAYWALL_REASON_CONTENT.feature_premium_only
  const Icon = content.icon
  const canUpgrade = !isPremium

  const aiLimitLabel = aiParlaysLimit < 0 ? "∞" : String(aiParlaysLimit)
  const aiRemainingLabel = aiParlaysLimit < 0 ? "∞" : String(Math.max(0, aiParlaysRemaining))
  const todayLimitLabel = todayLimit < 0 ? "∞" : String(todayLimit)
  const todayRemainingLabel = todayLimit < 0 ? "∞" : String(Math.max(0, todayRemaining))
  const customLimitLabel = customAiParlaysLimit < 0 ? "∞" : String(customAiParlaysLimit)
  const customRemainingLabel =
    customAiParlaysLimit < 0 ? "∞" : String(Math.max(0, customAiParlaysRemaining))
  
  // Determine if we should show pay-per-use options
  // Note: custom_builder_locked does NOT show pay-per-use purchases (credits/subscription only)
  const showPayPerUse = reason === 'ai_parlay_limit_reached' || reason === 'pay_per_use_required'
  const showBuyCreditsOnly = reason === 'custom_builder_locked' || reason === 'inscriptions_overage'
  const showUpgrade = canUpgrade
  
  // Use provided prices or defaults
  const effectiveSinglePrice = singlePrice ?? PARLAY_PRICING.single.price
  const effectiveMultiPrice = multiPrice ?? PARLAY_PRICING.multi.price

  const buyCreditsButtonLabel =
    reason === 'custom_builder_locked'
      ? `Buy Credits (${CREDITS_COST_CUSTOM_BUILDER_ACTION} per AI action)`
      : 'Buy Credits'

  useEffect(() => {
    if (isOpen && plans.length === 0) {
      loadPlans()
    }
  }, [isOpen, plans.length, loadPlans])

  useEffect(() => {
    if (isOpen && reason === 'feature_premium_only' && premiumUpsellTrigger && !upsellShownFiredRef.current) {
      upsellShownFiredRef.current = true
      trackPremiumUpsellShown({ trigger: premiumUpsellTrigger, variant: premiumUpsellVariant })
    }
    if (!isOpen) upsellShownFiredRef.current = false
  }, [isOpen, reason, premiumUpsellTrigger, premiumUpsellVariant])

  const handleUpgrade = () => {
    if (reason === 'feature_premium_only' && premiumUpsellTrigger) {
      trackPremiumUpgradeClicked({ trigger: premiumUpsellTrigger, variant: premiumUpsellVariant })
    }
    onClose()
    router.push('/pricing')
  }

  const handleBuyCredits = () => {
    onClose()
    router.push('/pricing#credits')
  }

  const handleQuickCheckout = async () => {
    try {
      setLoading('stripe')
      const checkoutUrl = await createCheckout('PG_PRO_MONTHLY')
      window.location.href = checkoutUrl
    } catch (err) {
      console.error('Checkout error:', err)
      // Fallback to pricing page
      router.push('/pricing')
    } finally {
      setLoading(null)
    }
  }
  
  const handleParlayPurchase = async (type: ParlayType, provider: 'stripe' = 'stripe') => {
    try {
      setLoading(`parlay-${type}-${provider}`)
      await redirectToCheckout(type, provider)
    } catch (err) {
      console.error('Parlay purchase error:', err)
      alert('Failed to create checkout. Please try again.')
    } finally {
      setLoading(null)
    }
  }

  if (reason === 'login_required') {
    return (
      <ClientPortal>
        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
              onClick={onClose}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="relative w-full max-w-md bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-2xl border border-emerald-500/20 shadow-2xl overflow-hidden"
                onClick={(e) => e.stopPropagation()}
              >
                <button
                  onClick={onClose}
                  className="absolute top-4 right-4 p-2 text-gray-400 hover:text-white transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>

                <div className="p-8 text-center">
                  <div className="mx-auto w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center mb-6">
                    <Shield className="h-8 w-8 text-emerald-400" />
                  </div>

                  <h2 className="text-2xl font-bold text-white mb-2">
                    {content.title}
                  </h2>
                  <p className="text-gray-400 mb-8">
                    {content.subtitle}
                  </p>

                  <div className="flex flex-col gap-3">
                    <button
                      onClick={() => router.push('/auth/login')}
                      className="w-full py-3 px-6 bg-emerald-500 hover:bg-emerald-400 text-black font-bold rounded-xl transition-all"
                    >
                      Log In
                    </button>
                    <button
                      onClick={() => router.push('/auth/signup')}
                      className="w-full py-3 px-6 bg-white/10 hover:bg-white/20 text-white font-medium rounded-xl transition-all"
                    >
                      Create Free Account
                    </button>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </ClientPortal>
    )
  }

  return (
    <ClientPortal>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            data-testid="pg-paywall"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
            onClick={onClose}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              className="relative w-full max-w-lg bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-2xl border border-emerald-500/30 shadow-2xl shadow-emerald-500/10 overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
            {/* Decorative gradient */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 via-green-400 to-emerald-500" />

            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-2 text-gray-400 hover:text-white transition-colors z-10"
            >
              <X className="h-5 w-5" />
            </button>

            <div className="p-8">
              {/* Header */}
              <div className="text-center mb-8">
                <div className="mx-auto w-20 h-20 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-green-500/20 flex items-center justify-center mb-6 border border-emerald-500/30">
                  <Icon className="h-10 w-10 text-emerald-400" />
                </div>

                <h2 className="text-2xl font-bold text-white mb-2">
                  {content.title}
                </h2>
                <p className="text-gray-400">
                  {error?.message || content.subtitle}
                </p>

                {reason === 'ai_parlay_limit_reached' && (
                  <p className="mt-2 text-sm text-emerald-400">
                    {isPremium
                      ? `This period remaining: ${aiRemainingLabel}/${aiLimitLabel}`
                      : `Today remaining: ${todayRemainingLabel}/${todayLimitLabel}`}
                  </p>
                )}

                {/* Balance context */}
                <div className="mt-4 grid grid-cols-3 gap-2">
                  <div className="rounded-xl bg-white/5 border border-white/10 p-3 text-center">
                    <p className="text-[10px] uppercase tracking-wide text-gray-500">Credits</p>
                    <p className="text-sm font-bold text-white">{creditsRemaining}</p>
                  </div>
                  {isPremium ? (
                    <>
                      <div className="rounded-xl bg-white/5 border border-white/10 p-3 text-center">
                        <p className="text-[10px] uppercase tracking-wide text-gray-500">AI Picks (this period)</p>
                        <p className="text-sm font-bold text-white">{`${aiRemainingLabel}/${aiLimitLabel}`}</p>
                      </div>
                      <div className="rounded-xl bg-white/5 border border-white/10 p-3 text-center">
                        <p className="text-[10px] uppercase tracking-wide text-gray-500">Gorilla Builder Parlays</p>
                        <p className="text-sm font-bold text-white">{`${customRemainingLabel}/${customLimitLabel}`}</p>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="rounded-xl bg-white/5 border border-white/10 p-3 text-center">
                        <p className="text-[10px] uppercase tracking-wide text-gray-500">Free (lifetime)</p>
                        <p className="text-sm font-bold text-white">{freeRemaining}</p>
                      </div>
                      <div className="rounded-xl bg-white/5 border border-white/10 p-3 text-center">
                        <p className="text-[10px] uppercase tracking-wide text-gray-500">Today</p>
                        <p className="text-sm font-bold text-white">{`${todayRemainingLabel}/${todayLimitLabel}`}</p>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Pay-Per-Use Options */}
              {showPayPerUse && (
                <div className="mb-6">
                  <p className="text-sm text-gray-400 text-center mb-4">Buy a single parlay:</p>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      onClick={() => handleParlayPurchase('single')}
                      disabled={loading !== null}
                      className={cn(
                        "p-4 rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-500/20 border border-blue-500/30 hover:border-blue-400/50 transition-all text-center group",
                        loading?.startsWith('parlay-single') && "opacity-50 cursor-wait"
                      )}
                    >
                      <DollarSign className="h-6 w-6 text-blue-400 mx-auto mb-2 group-hover:scale-110 transition-transform" />
                      <p className="text-lg font-bold text-white">{formatPrice(effectiveSinglePrice)}</p>
                      <p className="text-xs text-gray-400">Single Sport</p>
                      {loading?.startsWith('parlay-single') && <p className="text-xs text-blue-400 mt-1">Loading...</p>}
                    </button>
                    <button
                      onClick={() => handleParlayPurchase('multi')}
                      disabled={loading !== null}
                      className={cn(
                        "p-4 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30 hover:border-purple-400/50 transition-all text-center group",
                        loading?.startsWith('parlay-multi') && "opacity-50 cursor-wait"
                      )}
                    >
                      <Sparkles className="h-6 w-6 text-purple-400 mx-auto mb-2 group-hover:scale-110 transition-transform" />
                      <p className="text-lg font-bold text-white">{formatPrice(effectiveMultiPrice)}</p>
                      <p className="text-xs text-gray-400">Multi-Sport</p>
                      {loading?.startsWith('parlay-multi') && <p className="text-xs text-purple-400 mt-1">Loading...</p>}
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 text-center mt-2">Valid for 24 hours after purchase</p>

                  <div className="mt-4 flex flex-col items-center gap-2">
                    <p className="text-xs text-gray-500 text-center">
                      Want pay-per-use without a 24h window? Buy a credit pack.
                    </p>
                    <button
                      onClick={handleBuyCredits}
                      disabled={loading !== null}
                      className={cn(
                        "w-full py-3 px-4 bg-amber-500 hover:bg-amber-400 text-black font-bold rounded-xl transition-all text-sm flex items-center justify-center gap-2",
                        loading !== null && "opacity-50 cursor-wait"
                      )}
                    >
                      <Coins className="h-4 w-4" />
                      Buy Credits
                    </button>
                  </div>
                </div>
              )}

              {/* Divider for pay-per-use */}
              {showPayPerUse && showUpgrade && (
                <div className="flex items-center gap-4 mb-6">
                  <div className="flex-1 h-px bg-white/10" />
                  <span className="text-xs text-gray-500 uppercase tracking-wide">Or go Premium</span>
                  <div className="flex-1 h-px bg-white/10" />
                </div>
              )}

              {/* Benefits - show fewer when pay-per-use */}
              <div className={cn("grid gap-3 mb-6", showPayPerUse ? "grid-cols-4" : "grid-cols-2 mb-8")}>
                {(showPayPerUse ? PAYWALL_PREMIUM_BENEFITS.slice(0, 4) : PAYWALL_PREMIUM_BENEFITS).map((benefit) => (
                  <div
                    key={benefit.title}
                    className={cn("p-3 rounded-xl bg-white/5 border border-white/10", showPayPerUse && "p-2")}
                  >
                    <benefit.icon className={cn("text-emerald-400 mb-2", showPayPerUse ? "h-4 w-4" : "h-5 w-5")} />
                    <p className={cn("font-medium text-white", showPayPerUse ? "text-xs" : "text-sm")}>{benefit.title}</p>
                    {!showPayPerUse && <p className="text-xs text-gray-500">{benefit.description}</p>}
                  </div>
                ))}
              </div>

              {/* CTAs */}
              <div className="space-y-3">
                {showBuyCreditsOnly && (
                  <button
                    onClick={handleBuyCredits}
                    disabled={loading !== null}
                    className={cn(
                      "w-full py-3 px-6 bg-amber-500 hover:bg-amber-400 text-black font-bold rounded-xl transition-all flex items-center justify-center gap-2",
                      loading !== null && "opacity-50 cursor-wait"
                    )}
                  >
                    <Coins className="h-5 w-5" />
                    {buyCreditsButtonLabel}
                  </button>
                )}
                {showUpgrade ? (
                  <button
                    onClick={handleUpgrade}
                    className="w-full py-4 px-6 bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-400 hover:to-green-400 text-black font-bold rounded-xl transition-all shadow-lg shadow-emerald-500/30 flex items-center justify-center gap-2"
                  >
                    <Crown className="h-5 w-5" />
                    {showPayPerUse ? "View Premium Plans" : "Unlock Gorilla Premium"}
                  </button>
                ) : null}

                {!showPayPerUse && showUpgrade && (
                  <div className="flex gap-3">
                    <button
                      onClick={handleQuickCheckout}
                      disabled={loading !== null}
                      className={cn(
                        "flex-1 py-3 px-4 bg-white/10 hover:bg-white/20 text-white font-medium rounded-xl transition-all text-sm",
                        loading === 'stripe' && "opacity-50 cursor-wait"
                      )}
                    >
                      {loading === 'stripe' ? 'Loading...' : 'Pay with Card'}
                    </button>
                  </div>
                )}

                <button
                  onClick={onClose}
                  className="w-full py-2 text-gray-500 hover:text-gray-300 text-sm transition-colors"
                >
                  Continue Free
                </button>
              </div>
            </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </ClientPortal>
  )
}

export default PaywallModal

