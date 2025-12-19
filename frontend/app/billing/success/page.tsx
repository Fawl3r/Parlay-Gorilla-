"use client"

import { Suspense, useEffect, useMemo, useState } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { ArrowRight, CheckCircle, Coins, Crown, Loader2 } from "lucide-react"
import confetti from "canvas-confetti"

import { Header } from "@/components/Header"
import { api } from "@/lib/api"
import { useSubscription } from "@/lib/subscription-context"
import { PREMIUM_AI_PARLAYS_PER_PERIOD, PREMIUM_AI_PARLAYS_PERIOD_DAYS, PREMIUM_CUSTOM_PARLAYS_PER_DAY } from "@/lib/pricingConfig"

type SuccessType = "sub" | "credits" | "parlay_purchase"

interface AccessStatusResponse {
  credits: {
    balance: number
  }
}

function ProviderLabel({ provider }: { provider: string | null }) {
  if (!provider) return null
  const label = provider === "coinbase" ? "Coinbase Commerce" : "LemonSqueezy"
  return (
    <motion.p
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.8 }}
      className="mt-6 text-gray-500 text-sm"
    >
      Payment processed via {label}
    </motion.p>
  )
}

function CreditPackSuccessPanel({ provider, packId }: { provider: string | null; packId: string | null }) {
  const router = useRouter()
  const [polling, setPolling] = useState(true)
  const [currentBalance, setCurrentBalance] = useState<number | null>(null)
  const [creditsAdded, setCreditsAdded] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    let initial: number | null = null
    let attempts = 0
    const maxAttempts = 20
    const intervalMs = 1500

    const poll = async () => {
      attempts += 1
      try {
        const res = await api.get("/api/billing/access-status")
        const data = res.data as AccessStatusResponse
        const balance = data?.credits?.balance ?? 0

        if (cancelled) return

        setCurrentBalance(balance)

        if (initial === null) {
          initial = balance
        } else if (balance > initial) {
          setCreditsAdded(balance - initial)
          setPolling(false)
          return
        }
      } catch (err: any) {
        const detail = err?.response?.data?.detail
        if (!cancelled) {
          setError(detail || "Unable to confirm credits yet. Please check your Billing page.")
        }
      }

      if (!cancelled && attempts < maxAttempts) {
        setTimeout(poll, intervalMs)
      } else if (!cancelled) {
        setPolling(false)
      }
    }

    // Wait a moment for webhook to process, then start polling.
    setTimeout(poll, 800)

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <>
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: "spring", delay: 0.2 }}
        className="mx-auto w-24 h-24 rounded-full bg-gradient-to-br from-amber-500/20 to-yellow-500/20 flex items-center justify-center mb-8 border-2 border-amber-500/50"
      >
        <Coins className="h-12 w-12 text-amber-400" />
      </motion.div>

      <motion.h1
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="text-3xl md:text-4xl font-black text-white mb-4"
      >
        Thank You for{" "}
        <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-yellow-300">
          Your Purchase!
        </span>
      </motion.h1>

      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="text-gray-300 text-lg mb-2"
      >
        Your credits have been successfully added to your account.
      </motion.p>

      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.45 }}
        className="text-gray-400 text-base mb-8"
      >
        {packId ? (
          <>
            Purchase complete for <span className="text-gray-200">{packId}</span>. We're confirming your updated
            balance…
          </>
        ) : (
          "We're confirming your updated balance…"
        )}
      </motion.p>

      {polling ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="flex items-center justify-center gap-2 text-gray-400 mb-8"
        >
          <Loader2 className="h-5 w-5 animate-spin" />
          Confirming your credits...
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 mb-8"
        >
          <div className="text-amber-200">
            <div className="font-semibold mb-1">
              {creditsAdded !== null && creditsAdded > 0 ? `+${creditsAdded} credits added` : "Credits confirmed"}
            </div>
            <div className="text-sm text-gray-300">
              Current balance: <span className="font-bold text-white">{currentBalance ?? "—"}</span>
            </div>
            {error && <div className="text-xs text-gray-400 mt-2">{error}</div>}
          </div>
        </motion.div>
      )}

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
        className="grid grid-cols-1 sm:grid-cols-2 gap-3"
      >
        <button
          onClick={() => router.push("/billing#credits")}
          className="w-full py-4 px-6 bg-white/10 text-white font-bold rounded-xl hover:bg-white/20 transition-all"
        >
          View Billing
        </button>
        <button
          onClick={() => router.push("/app")}
          className="w-full py-4 px-6 bg-gradient-to-r from-amber-500 to-yellow-400 text-black font-bold rounded-xl hover:shadow-lg hover:shadow-amber-500/30 transition-all flex items-center justify-center gap-2"
        >
          Access Your Content
          <ArrowRight className="h-5 w-5" />
        </button>
      </motion.div>

      <ProviderLabel provider={provider} />
    </>
  )
}

function ParlayPurchaseSuccessPanel({ provider }: { provider: string | null }) {
  const router = useRouter()

  return (
    <>
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: "spring", delay: 0.2 }}
        className="mx-auto w-24 h-24 rounded-full bg-gradient-to-br from-blue-500/20 to-cyan-500/20 flex items-center justify-center mb-8 border-2 border-blue-500/50"
      >
        <CheckCircle className="h-12 w-12 text-blue-300" />
      </motion.div>

      <motion.h1
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="text-3xl md:text-4xl font-black text-white mb-4"
      >
        Thank You for{" "}
        <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-300 to-cyan-300">
          Your Purchase!
        </span>
      </motion.h1>

      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="text-gray-300 text-lg mb-2"
      >
        Your one-time parlay purchase is ready to use. Start building winning parlays now!
      </motion.p>

      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.45 }}
        className="text-gray-400 text-base mb-8"
      >
        Access your content below to get started.
      </motion.p>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7 }}>
        <button
          onClick={() => router.push("/app")}
          className="w-full py-4 px-6 bg-gradient-to-r from-blue-500 to-cyan-400 text-black font-bold rounded-xl hover:shadow-lg hover:shadow-blue-500/20 transition-all flex items-center justify-center gap-2"
        >
          Access Your Content
          <ArrowRight className="h-5 w-5" />
        </button>
      </motion.div>

      <ProviderLabel provider={provider} />
    </>
  )
}

function SubscriptionSuccessPanel({ provider }: { provider: string | null }) {
  const router = useRouter()
  const { refreshStatus, status } = useSubscription()
  const [refreshing, setRefreshing] = useState(true)

  useEffect(() => {
    const refreshSub = async () => {
      try {
        await refreshStatus()
      } catch (err) {
        console.error("Failed to refresh subscription:", err)
      } finally {
        setRefreshing(false)
      }
    }

    // Wait a moment for webhook to process, then refresh
    setTimeout(refreshSub, 2000)
  }, [refreshStatus])

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
              {status?.plan_code?.includes("LIFETIME") ? "Lifetime Premium Active" : "Premium Subscription Active"}
            </span>
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
          `${PREMIUM_AI_PARLAYS_PER_PERIOD} AI Parlays / ${PREMIUM_AI_PARLAYS_PERIOD_DAYS} days`,
          `Custom Builder (${PREMIUM_CUSTOM_PARLAYS_PER_DAY}/day)`,
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

function BillingSuccessContent() {
  const searchParams = useSearchParams()

  const provider = searchParams.get("provider")
  const typeParam = (searchParams.get("type") || "").toLowerCase()
  const packId = searchParams.get("pack")

  const successType: SuccessType = useMemo(() => {
    if (typeParam === "credits") return "credits"
    if (typeParam === "parlay_purchase") return "parlay_purchase"
    return "sub"
  }, [typeParam])

  useEffect(() => {
    // Trigger confetti on mount
    const duration = 2500
    const end = Date.now() + duration

    const frame = () => {
      confetti({
        particleCount: 3,
        angle: 60,
        spread: 55,
        origin: { x: 0 },
        colors: successType === "credits" ? ["#f59e0b", "#fbbf24", "#fde68a"] : ["#10b981", "#34d399", "#6ee7b7"],
      })
      confetti({
        particleCount: 3,
        angle: 120,
        spread: 55,
        origin: { x: 1 },
        colors: successType === "credits" ? ["#f59e0b", "#fbbf24", "#fde68a"] : ["#10b981", "#34d399", "#6ee7b7"],
      })

      if (Date.now() < end) {
        requestAnimationFrame(frame)
      }
    }
    frame()
  }, [successType])

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950">
      <Header />

      <main className="flex-1 flex items-center justify-center p-4">
        <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="w-full max-w-lg text-center">
          {successType === "credits" ? (
            <CreditPackSuccessPanel provider={provider} packId={packId} />
          ) : successType === "parlay_purchase" ? (
            <ParlayPurchaseSuccessPanel provider={provider} />
          ) : (
            <SubscriptionSuccessPanel provider={provider} />
          )}
        </motion.div>
      </main>
    </div>
  )
}

export default function BillingSuccessPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex flex-col bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950">
          <Header />
          <main className="flex-1 flex items-center justify-center p-4">
            <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
          </main>
        </div>
      }
    >
      <BillingSuccessContent />
    </Suspense>
  )
}

