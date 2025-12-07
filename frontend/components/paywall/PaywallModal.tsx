"use client"

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Crown, Zap, Target, TrendingUp, Shield, Sparkles } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useSubscription, PaywallError } from '@/lib/subscription-context'
import { cn } from '@/lib/utils'

export type PaywallReason = 
  | 'ai_parlay_limit_reached' 
  | 'feature_premium_only' 
  | 'custom_builder_locked'
  | 'upset_finder_locked'
  | 'login_required'

interface PaywallModalProps {
  isOpen: boolean
  onClose: () => void
  reason: PaywallReason
  featureName?: string
  error?: PaywallError | null
}

const REASON_CONTENT: Record<PaywallReason, { title: string; subtitle: string; icon: typeof Crown }> = {
  ai_parlay_limit_reached: {
    title: "You've Hit Your Daily Limit",
    subtitle: "Upgrade to Gorilla Premium for unlimited AI parlays every day.",
    icon: Zap,
  },
  feature_premium_only: {
    title: "Premium Feature",
    subtitle: "This feature requires a Gorilla Premium subscription.",
    icon: Crown,
  },
  custom_builder_locked: {
    title: "Custom Builder is Premium",
    subtitle: "Build your own custom parlays with AI validation – Premium only.",
    icon: Target,
  },
  upset_finder_locked: {
    title: "Unlock the Upset Finder",
    subtitle: "Find plus-money underdogs with positive expected value.",
    icon: TrendingUp,
  },
  login_required: {
    title: "Login Required",
    subtitle: "Create a free account to use this feature.",
    icon: Shield,
  },
}

const PREMIUM_BENEFITS = [
  {
    icon: Zap,
    title: "Unlimited AI Parlays",
    description: "Generate as many 1-20 leg parlays as you want",
  },
  {
    icon: Target,
    title: "Custom Parlay Builder",
    description: "Build your own parlays with AI-powered analysis",
  },
  {
    icon: TrendingUp,
    title: "Gorilla Upset Finder",
    description: "Discover +EV underdogs the market is undervaluing",
  },
  {
    icon: Sparkles,
    title: "Multi-Sport Mixing",
    description: "Cross-sport parlays with smart correlation handling",
  },
]

export function PaywallModal({ isOpen, onClose, reason, featureName, error }: PaywallModalProps) {
  const router = useRouter()
  const { createCheckout, loadPlans, plans, freeParlaysRemaining } = useSubscription()
  const [loading, setLoading] = useState<string | null>(null)

  const content = REASON_CONTENT[reason] || REASON_CONTENT.feature_premium_only
  const Icon = content.icon

  useEffect(() => {
    if (isOpen && plans.length === 0) {
      loadPlans()
    }
  }, [isOpen, plans.length, loadPlans])

  const handleUpgrade = () => {
    onClose()
    router.push('/pricing')
  }

  const handleQuickCheckout = async (provider: 'lemonsqueezy' | 'coinbase') => {
    try {
      setLoading(provider)
      const planCode = provider === 'coinbase' ? 'PG_LIFETIME' : 'PG_PREMIUM_MONTHLY'
      const checkoutUrl = await createCheckout(provider, planCode)
      window.location.href = checkoutUrl
    } catch (err) {
      console.error('Checkout error:', err)
      // Fallback to pricing page
      router.push('/pricing')
    } finally {
      setLoading(null)
    }
  }

  if (reason === 'login_required') {
    return (
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
    )
  }

  return (
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
                    Free parlays remaining today: {freeParlaysRemaining}
                  </p>
                )}
              </div>

              {/* Benefits */}
              <div className="grid grid-cols-2 gap-3 mb-8">
                {PREMIUM_BENEFITS.map((benefit) => (
                  <div
                    key={benefit.title}
                    className="p-3 rounded-xl bg-white/5 border border-white/10"
                  >
                    <benefit.icon className="h-5 w-5 text-emerald-400 mb-2" />
                    <p className="text-sm font-medium text-white">{benefit.title}</p>
                    <p className="text-xs text-gray-500">{benefit.description}</p>
                  </div>
                ))}
              </div>

              {/* CTAs */}
              <div className="space-y-3">
                <button
                  onClick={handleUpgrade}
                  className="w-full py-4 px-6 bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-400 hover:to-green-400 text-black font-bold rounded-xl transition-all shadow-lg shadow-emerald-500/30 flex items-center justify-center gap-2"
                >
                  <Crown className="h-5 w-5" />
                  Unlock Gorilla Premium
                </button>

                <div className="flex gap-3">
                  <button
                    onClick={() => handleQuickCheckout('lemonsqueezy')}
                    disabled={loading !== null}
                    className={cn(
                      "flex-1 py-3 px-4 bg-white/10 hover:bg-white/20 text-white font-medium rounded-xl transition-all text-sm",
                      loading === 'lemonsqueezy' && "opacity-50 cursor-wait"
                    )}
                  >
                    {loading === 'lemonsqueezy' ? 'Loading...' : 'Pay with Card'}
                  </button>
                  <button
                    onClick={() => handleQuickCheckout('coinbase')}
                    disabled={loading !== null}
                    className={cn(
                      "flex-1 py-3 px-4 bg-white/10 hover:bg-white/20 text-white font-medium rounded-xl transition-all text-sm",
                      loading === 'coinbase' && "opacity-50 cursor-wait"
                    )}
                  >
                    {loading === 'coinbase' ? 'Loading...' : 'Pay with Crypto'}
                  </button>
                </div>

                <button
                  onClick={onClose}
                  className="w-full py-2 text-gray-500 hover:text-gray-300 text-sm transition-colors"
                >
                  Maybe later
                </button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default PaywallModal

