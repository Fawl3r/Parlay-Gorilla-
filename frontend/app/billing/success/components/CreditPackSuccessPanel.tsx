"use client"

import { useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { ArrowRight, Coins, Loader2, RefreshCw } from "lucide-react"

import { api } from "@/lib/api"
import { StripeReconcileService } from "@/lib/billing/StripeReconcileService"

import { ProviderLabel } from "./ProviderLabel"

interface AccessStatusResponse {
  credits: {
    balance: number
  }
}

export function CreditPackSuccessPanel({
  provider,
  sessionId,
  packId,
  beforeBalance,
  expectedCredits,
}: {
  provider: string | null
  sessionId: string | null
  packId: string | null
  beforeBalance: number | null
  expectedCredits: number | null
}) {
  const router = useRouter()
  const [polling, setPolling] = useState(true)
  const [currentBalance, setCurrentBalance] = useState<number | null>(null)
  const [creditsAdded, setCreditsAdded] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [manualSyncing, setManualSyncing] = useState(false)

  const isStripe = (provider || "").toLowerCase() === "stripe"
  const reconciler = useMemo(() => new StripeReconcileService(), [])

  const reconcileOnce = async () => {
    if (!isStripe) return

    // Prefer reconciling the exact session; fall back to latest if it fails.
    if (sessionId) {
      try {
        await reconciler.reconcileSession(sessionId)
        return
      } catch (err) {
        console.warn("Stripe reconcile failed (session, credits):", err)
      }
    }

    try {
      await reconciler.reconcileLatest()
    } catch (err) {
      console.warn("Stripe reconcile failed (latest, credits):", err)
    }
  }

  const handleManualSync = async () => {
    if (!isStripe) return

    setManualSyncing(true)
    setError(null)
    try {
      await reconcileOnce()

      const res = await api.get("/api/billing/access-status")
      const data = res.data as AccessStatusResponse
      const balance = data?.credits?.balance ?? 0
      setCurrentBalance(balance)

      const targetBalance =
        beforeBalance !== null && expectedCredits !== null ? beforeBalance + expectedCredits : null

      if (targetBalance !== null && beforeBalance !== null) {
        if (balance >= targetBalance) {
          setCreditsAdded(balance - beforeBalance)
          return
        }
      } else if (currentBalance !== null && balance > currentBalance) {
        setCreditsAdded(balance - currentBalance)
      }

      setError((prev) => prev || "Still waiting for confirmation. If you just completed a purchase, try again in a moment.")
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      setError(detail || "Unable to sync credits yet. Please check Billing in a moment.")
    } finally {
      setManualSyncing(false)
    }
  }

  useEffect(() => {
    let cancelled = false
    let initial: number | null = null
    let confirmed = false
    let attempts = 0
    const maxAttempts = 20
    const intervalMs = 1500
    const targetBalance =
      beforeBalance !== null && expectedCredits !== null ? beforeBalance + expectedCredits : null

    const poll = async () => {
      attempts += 1
      try {
        // Best-effort reconcile early + periodically while we wait for Stripe/webhooks.
        if (attempts === 1 || attempts % 5 === 1) {
          await reconcileOnce()
        }

        const res = await api.get("/api/billing/access-status")
        const data = res.data as AccessStatusResponse
        const balance = data?.credits?.balance ?? 0

        if (cancelled) return

        setCurrentBalance(balance)

        if (targetBalance !== null && beforeBalance !== null) {
          if (balance >= targetBalance) {
            confirmed = true
            setCreditsAdded(balance - beforeBalance)
            setPolling(false)
            return
          }
        } else {
          if (initial === null) {
            initial = balance
          } else if (balance > initial) {
            confirmed = true
            setCreditsAdded(balance - initial)
            setPolling(false)
            return
          }
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
        if (!confirmed) {
          setError((prev) => prev || "We couldn't confirm your updated credit balance yet. Please check Billing in a moment.")
        }
      }
    }

    // Wait a moment for webhook/reconcile to process, then start polling.
    setTimeout(poll, 800)

    return () => {
      cancelled = true
    }
  }, [beforeBalance, expectedCredits, isStripe, reconciler, sessionId])

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
        Your purchase was successful.
      </motion.p>

      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.45 }}
        className="text-gray-400 text-base mb-8"
      >
        {packId ? (
          <>
            Purchase complete for <span className="text-gray-200">{packId}</span>. We&apos;re confirming your updated
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
              {creditsAdded !== null && creditsAdded > 0 ? `+${creditsAdded} credits added` : "Still confirming credits"}
            </div>
            <div className="text-sm text-gray-300">
              Current balance: <span className="font-bold text-white">{currentBalance ?? "—"}</span>
            </div>
            {error && <div className="text-xs text-gray-400 mt-2">{error}</div>}
          </div>
        </motion.div>
      )}

      {!polling && isStripe && (creditsAdded === null || creditsAdded <= 0) && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-6">
          <button
            onClick={handleManualSync}
            disabled={manualSyncing}
            className="mx-auto inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-white/10 hover:bg-white/15 border border-white/10 text-white font-semibold transition-all disabled:opacity-50"
          >
            {manualSyncing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            Sync Credits Now
          </button>
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


