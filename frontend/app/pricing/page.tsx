"use client"

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Crown, Zap, Target, TrendingUp, Sparkles, Check, X, 
  CreditCard, Bitcoin, Shield, Clock, Infinity
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import { Header } from '@/components/Header'
import { Footer } from '@/components/Footer'
import { useSubscription, SubscriptionPlan } from '@/lib/subscription-context'
import { useAuth } from '@/lib/auth-context'
import { cn } from '@/lib/utils'

const FEATURE_LIST = [
  { key: 'game_analysis', label: 'Full Game Analysis Pages', free: true, premium: true },
  { key: 'ai_parlays', label: 'AI-Generated Parlays (1-20 legs)', free: '1/day', premium: 'Unlimited' },
  { key: 'custom_builder', label: 'Custom Parlay Builder', free: false, premium: true },
  { key: 'upset_finder', label: 'Gorilla Upset Finder (+EV picks)', free: false, premium: true },
  { key: 'multi_sport', label: 'Multi-Sport Parlay Mixing', free: false, premium: true },
  { key: 'saved_parlays', label: 'Save & Track Parlays', free: false, premium: true },
  { key: 'confidence', label: 'Advanced Confidence Meters', free: 'Basic', premium: 'Full' },
  { key: 'ev_estimates', label: 'Expected Value Estimates', free: false, premium: true },
  { key: 'ad_free', label: 'Ad-Free Experience', free: false, premium: true },
  { key: 'early_access', label: 'Early Access to New Features', free: false, premium: true },
]

export default function PricingPage() {
  const router = useRouter()
  const { user } = useAuth()
  const { plans, loadPlans, createCheckout, isPremium, status } = useSubscription()
  const [loading, setLoading] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadPlans()
  }, [loadPlans])

  const handleCheckout = async (provider: 'lemonsqueezy' | 'coinbase', planCode: string) => {
    if (!user) {
      // Store intent and redirect to login
      sessionStorage.setItem('redirectAfterLogin', '/pricing')
      router.push('/auth/login')
      return
    }

    try {
      setLoading(`${provider}-${planCode}`)
      setError(null)
      const checkoutUrl = await createCheckout(provider, planCode)
      window.location.href = checkoutUrl
    } catch (err: any) {
      console.error('Checkout error:', err)
      setError(err.response?.data?.detail || 'Failed to create checkout. Please try again.')
    } finally {
      setLoading(null)
    }
  }

  // Get premium plans
  const monthlyPlan = plans.find(p => p.code === 'PG_PREMIUM_MONTHLY')
  const annualPlan = plans.find(p => p.code === 'PG_PREMIUM_ANNUAL')
  const lifetimePlan = plans.find(p => p.code === 'PG_LIFETIME')

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950">
      <Header />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative py-20 overflow-hidden">
          {/* Background decoration */}
          <div className="absolute inset-0 overflow-hidden">
            <div className="absolute top-20 left-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl" />
            <div className="absolute bottom-20 right-1/4 w-96 h-96 bg-green-500/10 rounded-full blur-3xl" />
          </div>

          <div className="container mx-auto px-4 relative z-10">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center max-w-3xl mx-auto"
            >
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-medium mb-6">
                <Crown className="h-4 w-4" />
                Gorilla Premium
              </div>

              <h1 className="text-4xl md:text-5xl lg:text-6xl font-black text-white mb-6">
                Unlock Your{' '}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-green-400">
                  Betting Edge
                </span>
              </h1>

              <p className="text-xl text-gray-400 mb-8">
                Stop guessing. Let Parlay Gorilla stack model-backed edges into every ticket.
                Unlimited AI parlays, custom builders, and the Upset Finder await.
              </p>

              {isPremium && (
                <div className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-emerald-500/20 border border-emerald-500/30 text-emerald-400">
                  <Check className="h-5 w-5" />
                  You're already a Premium member!
                </div>
              )}
            </motion.div>
          </div>
        </section>

        {/* Pricing Cards */}
        <section className="py-16">
          <div className="container mx-auto px-4">
            {error && (
              <div className="max-w-2xl mx-auto mb-8 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-center">
                {error}
              </div>
            )}

            <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
              {/* Free Plan */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="relative p-8 rounded-2xl bg-gray-900/50 border border-gray-800"
              >
                <h3 className="text-xl font-bold text-white mb-2">Free</h3>
                <p className="text-gray-400 text-sm mb-6">Get started with Parlay Gorilla</p>

                <div className="mb-6">
                  <span className="text-4xl font-black text-white">$0</span>
                  <span className="text-gray-500">/forever</span>
                </div>

                <ul className="space-y-3 mb-8">
                  <li className="flex items-center gap-3 text-gray-300">
                    <Check className="h-5 w-5 text-emerald-400" />
                    Full game analysis access
                  </li>
                  <li className="flex items-center gap-3 text-gray-300">
                    <Check className="h-5 w-5 text-emerald-400" />
                    1 AI parlay per day
                  </li>
                  <li className="flex items-center gap-3 text-gray-500">
                    <X className="h-5 w-5" />
                    Custom parlay builder
                  </li>
                  <li className="flex items-center gap-3 text-gray-500">
                    <X className="h-5 w-5" />
                    Upset finder
                  </li>
                </ul>

                <button
                  onClick={() => router.push(user ? '/app' : '/auth/signup')}
                  className="w-full py-3 px-6 rounded-xl border border-gray-700 text-gray-300 font-medium hover:bg-gray-800 transition-colors"
                >
                  {user ? 'Go to App' : 'Start Free'}
                </button>
              </motion.div>

              {/* Monthly Premium Plan */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="relative p-8 rounded-2xl bg-gradient-to-br from-emerald-900/30 to-green-900/30 border-2 border-emerald-500/50 shadow-xl shadow-emerald-500/10"
              >
                {/* Featured badge */}
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-emerald-500 text-black text-sm font-bold">
                  Most Popular
                </div>

                <h3 className="text-xl font-bold text-white mb-2">Premium Monthly</h3>
                <p className="text-gray-400 text-sm mb-6">Full access to all features</p>

                <div className="mb-6">
                  <span className="text-4xl font-black text-white">
                    ${monthlyPlan?.price_dollars || 9.99}
                  </span>
                  <span className="text-gray-500">/month</span>
                </div>

                <ul className="space-y-3 mb-8">
                  <li className="flex items-center gap-3 text-gray-300">
                    <Infinity className="h-5 w-5 text-emerald-400" />
                    Unlimited AI parlays
                  </li>
                  <li className="flex items-center gap-3 text-gray-300">
                    <Target className="h-5 w-5 text-emerald-400" />
                    Custom parlay builder
                  </li>
                  <li className="flex items-center gap-3 text-gray-300">
                    <TrendingUp className="h-5 w-5 text-emerald-400" />
                    Gorilla Upset Finder
                  </li>
                  <li className="flex items-center gap-3 text-gray-300">
                    <Sparkles className="h-5 w-5 text-emerald-400" />
                    Multi-sport mixing
                  </li>
                </ul>

                <div className="space-y-3">
                  <button
                    onClick={() => handleCheckout('lemonsqueezy', 'PG_PREMIUM_MONTHLY')}
                    disabled={loading !== null || isPremium}
                    className={cn(
                      "w-full py-3 px-6 rounded-xl font-bold transition-all flex items-center justify-center gap-2",
                      isPremium
                        ? "bg-gray-700 text-gray-400 cursor-not-allowed"
                        : "bg-gradient-to-r from-emerald-500 to-green-500 text-black hover:shadow-lg hover:shadow-emerald-500/30"
                    )}
                  >
                    {loading === 'lemonsqueezy-PG_PREMIUM_MONTHLY' ? (
                      'Loading...'
                    ) : isPremium ? (
                      'Already Premium'
                    ) : (
                      <>
                        <CreditCard className="h-5 w-5" />
                        Pay with Card
                      </>
                    )}
                  </button>
                </div>
              </motion.div>

              {/* Lifetime Plan - Crypto Only */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="relative p-8 rounded-2xl bg-gradient-to-br from-amber-900/20 to-orange-900/20 border border-amber-500/30"
              >
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 text-black text-sm font-bold">
                  🦍 Crypto Exclusive
                </div>

                <h3 className="text-xl font-bold text-white mb-2">Lifetime Access</h3>
                <p className="text-gray-400 text-sm mb-6">Pay once with crypto, access forever</p>

                <div className="mb-2">
                  <span className="text-4xl font-black text-white">
                    ${lifetimePlan?.price_dollars || 500}
                  </span>
                  <span className="text-gray-500">/one-time</span>
                </div>
                
                {/* Crypto payment options */}
                <div className="flex items-center gap-2 mb-6 text-sm">
                  <span className="px-2 py-1 rounded bg-orange-500/20 text-orange-400 font-medium flex items-center gap-1">
                    <Bitcoin className="h-3.5 w-3.5" />
                    BTC
                  </span>
                  <span className="px-2 py-1 rounded bg-blue-500/20 text-blue-400 font-medium">
                    USDC
                  </span>
                  <span className="text-gray-500">+ more</span>
                </div>

                <ul className="space-y-3 mb-8">
                  <li className="flex items-center gap-3 text-gray-300">
                    <Infinity className="h-5 w-5 text-amber-400" />
                    Everything in Premium
                  </li>
                  <li className="flex items-center gap-3 text-gray-300">
                    <Clock className="h-5 w-5 text-amber-400" />
                    Never pay again - ever
                  </li>
                  <li className="flex items-center gap-3 text-gray-300">
                    <Shield className="h-5 w-5 text-amber-400" />
                    Founding member perks
                  </li>
                  <li className="flex items-center gap-3 text-gray-300">
                    <Zap className="h-5 w-5 text-amber-400" />
                    Priority support
                  </li>
                </ul>

                <button
                  onClick={() => handleCheckout('coinbase', 'PG_LIFETIME')}
                  disabled={loading !== null || isPremium}
                  className={cn(
                    "w-full py-3 px-6 rounded-xl font-bold transition-all flex items-center justify-center gap-2",
                    isPremium
                      ? "bg-gray-700 text-gray-400 cursor-not-allowed"
                      : "bg-gradient-to-r from-amber-500 to-orange-500 text-black hover:shadow-lg hover:shadow-amber-500/30"
                  )}
                >
                  {loading === 'coinbase-PG_LIFETIME' ? (
                    'Loading...'
                  ) : isPremium ? (
                    'Already Premium'
                  ) : (
                    <>
                      <Bitcoin className="h-5 w-5" />
                      Pay $500 with Crypto
                    </>
                  )}
                </button>
                
                <p className="text-xs text-gray-500 mt-3 text-center">
                  Powered by Coinbase Commerce • BTC, USDC, ETH accepted
                </p>
              </motion.div>
            </div>

            {/* Annual option */}
            {annualPlan && !isPremium && (
              <div className="mt-8 text-center">
                <p className="text-gray-400 mb-4">
                  Want to save? Get{' '}
                  <span className="text-emerald-400 font-semibold">2 months free</span>{' '}
                  with annual billing.
                </p>
                <button
                  onClick={() => handleCheckout('lemonsqueezy', 'PG_PREMIUM_ANNUAL')}
                  disabled={loading !== null}
                  className="px-6 py-2 rounded-lg bg-white/10 text-white hover:bg-white/20 transition-colors"
                >
                  {loading === 'lemonsqueezy-PG_PREMIUM_ANNUAL' 
                    ? 'Loading...' 
                    : `Annual Plan - $${annualPlan.price_dollars}/year`
                  }
                </button>
              </div>
            )}
          </div>
        </section>

        {/* Feature Comparison */}
        <section className="py-16 border-t border-gray-800">
          <div className="container mx-auto px-4">
            <h2 className="text-3xl font-bold text-white text-center mb-12">
              Compare Plans
            </h2>

            <div className="max-w-4xl mx-auto overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="py-4 px-4 text-left text-gray-400 font-medium">Feature</th>
                    <th className="py-4 px-4 text-center text-gray-400 font-medium">Free</th>
                    <th className="py-4 px-4 text-center text-emerald-400 font-medium">Premium</th>
                  </tr>
                </thead>
                <tbody>
                  {FEATURE_LIST.map((feature, i) => (
                    <tr key={feature.key} className={i % 2 === 0 ? 'bg-gray-900/30' : ''}>
                      <td className="py-4 px-4 text-gray-300">{feature.label}</td>
                      <td className="py-4 px-4 text-center">
                        {feature.free === true ? (
                          <Check className="h-5 w-5 text-emerald-400 mx-auto" />
                        ) : feature.free === false ? (
                          <X className="h-5 w-5 text-gray-600 mx-auto" />
                        ) : (
                          <span className="text-gray-400">{feature.free}</span>
                        )}
                      </td>
                      <td className="py-4 px-4 text-center">
                        {feature.premium === true ? (
                          <Check className="h-5 w-5 text-emerald-400 mx-auto" />
                        ) : feature.premium === false ? (
                          <X className="h-5 w-5 text-gray-600 mx-auto" />
                        ) : (
                          <span className="text-emerald-400">{feature.premium}</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* FAQ or CTA */}
        <section className="py-16">
          <div className="container mx-auto px-4 text-center">
            <h2 className="text-2xl font-bold text-white mb-4">
              Questions? We've got answers.
            </h2>
            <p className="text-gray-400 mb-8">
              Email us at{' '}
              <a href="mailto:support@parlaygorilla.com" className="text-emerald-400 hover:underline">
                support@parlaygorilla.com
              </a>
            </p>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  )
}

