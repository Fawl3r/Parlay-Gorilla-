"use client"

import { useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { CheckCircle, ArrowRight, Crown, Loader2 } from 'lucide-react'
import { Header } from '@/components/Header'
import { useSubscription } from '@/lib/subscription-context'
import { useAuth } from '@/lib/auth-context'
import confetti from 'canvas-confetti'

export default function BillingSuccessPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const provider = searchParams.get('provider')
  const { refreshStatus, status } = useSubscription()
  const { user } = useAuth()
  const [refreshing, setRefreshing] = useState(true)

  useEffect(() => {
    // Trigger confetti on mount
    const duration = 3000
    const end = Date.now() + duration

    const frame = () => {
      confetti({
        particleCount: 3,
        angle: 60,
        spread: 55,
        origin: { x: 0 },
        colors: ['#10b981', '#34d399', '#6ee7b7'],
      })
      confetti({
        particleCount: 3,
        angle: 120,
        spread: 55,
        origin: { x: 1 },
        colors: ['#10b981', '#34d399', '#6ee7b7'],
      })

      if (Date.now() < end) {
        requestAnimationFrame(frame)
      }
    }
    frame()

    // Refresh subscription status
    const refreshSub = async () => {
      try {
        await refreshStatus()
      } catch (err) {
        console.error('Failed to refresh subscription:', err)
      } finally {
        setRefreshing(false)
      }
    }

    // Wait a moment for webhook to process, then refresh
    setTimeout(refreshSub, 2000)
  }, [refreshStatus])

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950">
      <Header />

      <main className="flex-1 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-lg text-center"
        >
          {/* Success Icon */}
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', delay: 0.2 }}
            className="mx-auto w-24 h-24 rounded-full bg-gradient-to-br from-emerald-500/20 to-green-500/20 flex items-center justify-center mb-8 border-2 border-emerald-500/50"
          >
            <CheckCircle className="h-12 w-12 text-emerald-400" />
          </motion.div>

          {/* Title */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-3xl md:text-4xl font-black text-white mb-4"
          >
            Welcome to{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-green-400">
              Gorilla Premium!
            </span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="text-gray-400 text-lg mb-8"
          >
            Your payment was successful. You now have full access to all premium features.
          </motion.p>

          {/* Status */}
          {refreshing ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="flex items-center justify-center gap-2 text-gray-400 mb-8"
            >
              <Loader2 className="h-5 w-5 animate-spin" />
              Activating your subscription...
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 mb-8"
            >
              <div className="flex items-center justify-center gap-2 text-emerald-400">
                <Crown className="h-5 w-5" />
                <span className="font-semibold">
                  {status?.plan_code?.includes('LIFETIME') 
                    ? 'Lifetime Premium Active' 
                    : 'Premium Subscription Active'}
                </span>
              </div>
            </motion.div>
          )}

          {/* Features unlocked */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="grid grid-cols-2 gap-4 mb-8"
          >
            {[
              'Unlimited AI Parlays',
              'Custom Builder',
              'Upset Finder',
              'Multi-Sport Mixing',
            ].map((feature, i) => (
              <div
                key={feature}
                className="p-3 rounded-lg bg-white/5 border border-white/10 text-gray-300 text-sm"
              >
                <CheckCircle className="h-4 w-4 text-emerald-400 inline mr-2" />
                {feature}
              </div>
            ))}
          </motion.div>

          {/* CTA */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
          >
            <button
              onClick={() => router.push('/app')}
              className="w-full py-4 px-6 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-xl hover:shadow-lg hover:shadow-emerald-500/30 transition-all flex items-center justify-center gap-2"
            >
              Start Building Parlays
              <ArrowRight className="h-5 w-5" />
            </button>
          </motion.div>

          {/* Provider info */}
          {provider && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8 }}
              className="mt-6 text-gray-500 text-sm"
            >
              Payment processed via {provider === 'coinbase' ? 'Coinbase Commerce' : 'LemonSqueezy'}
            </motion.p>
          )}
        </motion.div>
      </main>
    </div>
  )
}

