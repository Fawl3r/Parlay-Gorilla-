"use client"

import { useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { ArrowRight, CheckCircle, Crown, Loader2 } from "lucide-react"

import { useSubscription } from "@/lib/subscription-context"
import { api } from "@/lib/api"
import {
  PREMIUM_AI_PARLAYS_PER_PERIOD,
  PREMIUM_AI_PARLAYS_PERIOD_DAYS,
  PREMIUM_CUSTOM_PARLAYS_PER_PERIOD,
  PREMIUM_CUSTOM_PARLAYS_PERIOD_DAYS,
} from "@/lib/pricingConfig"

import { ProviderLabel } from "./ProviderLabel"
import { StripeReconcileService } from "@/lib/billing/StripeReconcileService"

export function SubscriptionSuccessPanel({
  provider,
  sessionId,
}: {
  provider: string | null
  sessionId: string | null
}) {
  const router = useRouter()
  const { refreshStatus, status } = useSubscription()
  const [refreshing, setRefreshing] = useState(true)
  const [activationStatus, setActivationStatus] = useState<"checking" | "active" | "pending" | "error">("checking")
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const isStripe = (provider || "").toLowerCase() === "stripe"
  const reconciler = useMemo(() => new StripeReconcileService(), [])

  useEffect(() => {
    let pollCount = 0
    const maxPolls = 12 // ~24s
    let cancelled = false
    let reconciledOnce = false

    const attemptReconcile = async () => {
      if (!isStripe || reconciledOnce) return
      reconciledOnce = true
      try {
        if (sessionId) {
          await reconciler.reconcileSession(sessionId)
        } else {
          await reconciler.reconcileLatest()
        }
      } catch (err) {
        // Best-effort fallback; polling will still reflect webhook activation if it lands.
        console.warn("Stripe reconcile failed (subscription):", err)
      }
    }

    const checkActivation = async () => {
      if (cancelled) return

      try {
        await attemptReconcile()
        await refreshStatus()

        // Re-fetch status after refresh to avoid stale context reads.
        const response = await api.get(`/api/billing/status?t=${Date.now()}`)
        const latestStatus = response.data

        const isActive =
          latestStatus?.tier === "premium" ||
          (latestStatus?.plan_code !== null && latestStatus?.plan_code !== undefined)

        if (isActive) {
          setActivationStatus("active")
          setRefreshing(false)
          return
        }

        pollCount++
        if (pollCount >= maxPolls) {
          setActivationStatus("pending")
          setErrorMessage(
            "Your payment was successful, but activation is taking longer than expected. " +
              "Please check back in a few minutes or contact support if the issue persists."
          )
          setRefreshing(false)
        } else {
          setTimeout(checkActivation, 2000)
        }
      } catch (err) {
        console.error("Failed to check activation:", err)
        pollCount++
        if (pollCount >= maxPolls) {
          setActivationStatus("error")
          setErrorMessage("Unable to verify activation. Please check your subscription status.")
          setRefreshing(false)
        } else {
          setTimeout(checkActivation, 2000)
        }
      }
    }

    // Wait a moment for Stripe/webhooks then start polling.
    setTimeout(checkActivation, 1200)

    return () => {
      cancelled = true
    }
  }, [isStripe, reconciler, refreshStatus, sessionId])

  return (
    <>
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: "spring", delay: 0.2 }}
        className="mx-auto w-24 h-24 rounded-full bg-gradient-to-br from-emerald-500/20 to-green-500/20 flex items-center justify-center mb-8 border-2 border-emerald-500/50"
      >
        <CheckCircle className="h-12 w-12 text-emerald-400" />
      </motion.div>

      <motion.h1
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="text-3xl md:text-4xl font-black text-white mb-4"
      >
        Thank You for{" "}
        <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-green-400">
          Your Purchase!
        </span>
      </motion.h1>

      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="text-gray-300 text-lg mb-2"
      >
        Welcome to Gorilla Premium! Your payment was successful and you now have full access to all premium features.
      </motion.p>

      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.45 }}
        className="text-gray-400 text-base mb-8"
      >
        Access your content below to start building winning parlays.
      </motion.p>

      {refreshing || activationStatus === "checking" ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="flex flex-col items-center justify-center gap-2 text-gray-400 mb-8"
        >
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>Activating your subscription...</span>
          <span className="text-xs text-gray-500">This may take a few moments</span>
        </motion.div>
      ) : activationStatus === "active" ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 mb-8"
        >
          <div className="flex items-center justify-center gap-2 text-emerald-400">
            <Crown className="h-5 w-5" />
            <span className="font-semibold">
              {status?.plan_code?.includes("LIFETIME") ? "Lifetime Premium Active" : "Premium Subscription Active"}
            </span>
          </div>
        </motion.div>
      ) : activationStatus === "pending" ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/30 mb-8"
        >
          <div className="flex flex-col items-center justify-center gap-2 text-yellow-400">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="font-semibold text-center">Activation in Progress</span>
            {errorMessage && <span className="text-xs text-yellow-300 text-center mt-2">{errorMessage}</span>}
            <a href="/billing" className="mt-2 text-xs text-yellow-300 underline hover:text-yellow-200">
              Check subscription status
            </a>
          </div>
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 mb-8"
        >
          <div className="flex flex-col items-center justify-center gap-2 text-red-400">
            <span className="font-semibold text-center">Unable to Verify Activation</span>
            {errorMessage && <span className="text-xs text-red-300 text-center mt-2">{errorMessage}</span>}
          </div>
        </motion.div>
      )}

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="grid grid-cols-2 gap-4 mb-8"
      >
        {[
          `${PREMIUM_AI_PARLAYS_PER_PERIOD} Gorilla Parlays / ${PREMIUM_AI_PARLAYS_PERIOD_DAYS} days`,
          `🦍 Gorilla Parlay Builder 🦍 (${PREMIUM_CUSTOM_PARLAYS_PER_PERIOD}/${PREMIUM_CUSTOM_PARLAYS_PERIOD_DAYS} days)`,
          "Upset Finder",
          "Multi-Sport Mixing",
        ].map((feature) => (
          <div
            key={feature}
            className="p-3 rounded-lg bg-white/5 border border-white/10 text-gray-300 text-sm"
          >
            <CheckCircle className="h-4 w-4 text-emerald-400 inline mr-2" />
            {feature}
          </div>
        ))}
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7 }}>
        <button
          onClick={() => router.push("/app")}
          className="w-full py-4 px-6 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-xl hover:shadow-lg hover:shadow-emerald-500/30 transition-all flex items-center justify-center gap-2"
        >
          Access Your Content
          <ArrowRight className="h-5 w-5" />
        </button>
      </motion.div>

      <ProviderLabel provider={provider} />
    </>
  )
}


