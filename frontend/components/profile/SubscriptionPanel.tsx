"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { 
  Crown, 
  Calendar, 
  CreditCard, 
  AlertCircle, 
  Check, 
  Loader2,
  ExternalLink,
  Infinity
} from "lucide-react"
import Link from "next/link"
import { api, SubscriptionMeResponse } from "@/lib/api"
import { PREMIUM_AI_PARLAYS_PER_PERIOD, PREMIUM_AI_PARLAYS_PERIOD_DAYS, PREMIUM_CUSTOM_PARLAYS_PER_PERIOD, PREMIUM_CUSTOM_PARLAYS_PERIOD_DAYS } from "@/lib/pricingConfig"
import { GlassPanel } from "@/components/ui/glass-panel"

interface SubscriptionPanelProps {
  className?: string
}

export function SubscriptionPanel({ className }: SubscriptionPanelProps) {
  const [subscription, setSubscription] = useState<SubscriptionMeResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [canceling, setCanceling] = useState(false)
  const [showCancelConfirm, setShowCancelConfirm] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  useEffect(() => {
    loadSubscription()
  }, [])

  const loadSubscription = async () => {
    try {
      setError(null)
      setSuccessMessage(null)
      const data = await api.getMySubscription()
      setSubscription(data)
    } catch (err: any) {
      console.error("Subscription load error:", err)
      const errorMessage = err.response?.data?.detail || err.message || "Failed to load subscription"
      setError(errorMessage)
      // Still set a default subscription state so UI doesn't break
      setSubscription({
        has_subscription: false,
        plan_name: "Free",
        status: "free",
        is_lifetime: false,
        is_on_trial: false,
        cancel_at_period_end: false,
      } as SubscriptionMeResponse)
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = async () => {
    setCanceling(true)
    try {
      setError(null)
      await api.cancelSubscription()
      await loadSubscription()
      setShowCancelConfirm(false)
      setSuccessMessage("Cancellation scheduled. You'll keep access until the end of your billing period.")
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to cancel subscription")
    } finally {
      setCanceling(false)
    }
  }

  if (loading) {
    return (
      <GlassPanel className={className}>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-gray-500" />
        </div>
      </GlassPanel>
    )
  }

  if (error) {
    return (
      <GlassPanel className={className}>
        <div className="flex items-center gap-2 text-red-400">
          <AlertCircle className="h-5 w-5" />
          <span>{error}</span>
        </div>
      </GlassPanel>
    )
  }

  if (!subscription) return null

  const provider = (subscription.provider || "").toLowerCase()
  const isAutoRenewProvider = provider === "stripe" || provider === "lemonsqueezy"

  const providerLabel = (() => {
    if (provider === "stripe") return "Card (Stripe)"
    if (provider === "lemonsqueezy") return "Card (LemonSqueezy)"
    return subscription.provider || "Unknown"
  })()

  const getStatusBadge = () => {
    switch (subscription.status) {
      case "active":
        return { label: "Active", color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" }
      case "trialing":
        return { label: "Trial", color: "bg-blue-500/20 text-blue-400 border-blue-500/30" }
      case "canceled":
        return { label: "Canceled", color: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" }
      case "past_due":
        return { label: "Past Due", color: "bg-red-500/20 text-red-400 border-red-500/30" }
      case "expired":
        return { label: "Expired", color: "bg-gray-500/20 text-gray-400 border-gray-500/30" }
      default:
        return { label: "Free", color: "bg-gray-500/20 text-gray-400 border-gray-500/30" }
    }
  }

  const statusBadge = getStatusBadge()

  return (
    <GlassPanel className={className}>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <CreditCard className="h-5 w-5 text-gray-500" />
          Subscription
        </h2>
        <span className={`px-3 py-1 rounded-full text-xs font-medium border ${statusBadge.color}`}>
          {statusBadge.label}
        </span>
      </div>

      {/* Current Plan */}
      <div className="space-y-4">
        {successMessage && (
          <div className="flex items-center gap-2 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-sm text-emerald-300">
            <Check className="h-4 w-4 text-emerald-400" />
            <span>{successMessage}</span>
          </div>
        )}

        <div className="flex items-center gap-4 p-4 bg-white/[0.05] rounded-lg border border-white/10">
          <div className="h-12 w-12 rounded-lg bg-gradient-to-br from-emerald-500/20 to-green-500/10 flex items-center justify-center">
            {subscription.is_lifetime ? (
              <Infinity className="h-6 w-6 text-emerald-400" />
            ) : (
              <Crown className="h-6 w-6 text-emerald-400" />
            )}
          </div>
          <div className="flex-1">
            <p className="font-semibold text-white">{subscription.plan_name || "Free Plan"}</p>
            <p className="text-sm text-gray-400">
              {subscription.is_lifetime 
                ? "Lifetime access" 
                : subscription.has_subscription 
                  ? `via ${providerLabel}` 
                  : "Upgrade for full access"
              }
            </p>
          </div>
        </div>

        {/* Renewal/Cancellation Info */}
        {subscription.has_subscription && subscription.current_period_end && !subscription.is_lifetime && (
          <div className="flex items-center gap-2 text-sm">
            <Calendar className="h-4 w-4 text-gray-500" />
            {subscription.cancel_at_period_end ? (
              <span className="text-yellow-400">
                Access ends on {new Date(subscription.current_period_end).toLocaleDateString()}
              </span>
            ) : isAutoRenewProvider ? (
              <span className="text-gray-400">
                Renews on {new Date(subscription.current_period_end).toLocaleDateString()}
              </span>
            ) : (
              <span className="text-gray-400">
                Access ends on {new Date(subscription.current_period_end).toLocaleDateString()}
              </span>
            )}
          </div>
        )}


        {/* Trial Info */}
        {subscription.is_on_trial && (
          <div className="flex items-center gap-2 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg text-sm text-blue-400">
            <AlertCircle className="h-4 w-4" />
            <span>You&apos;re on a free trial</span>
          </div>
        )}

        {/* Plan Features */}
        {subscription.has_subscription && (
          <div className="space-y-2 pt-2">
            <p className="text-xs text-gray-500 uppercase tracking-wider">Included Features</p>
            <div className="grid grid-cols-2 gap-2">
              {[
                `${PREMIUM_AI_PARLAYS_PER_PERIOD} Gorilla Parlays / ${PREMIUM_AI_PARLAYS_PERIOD_DAYS} days`,
                "Multi-Sport Mixing",
                `🦍 Gorilla Parlay Builder 🦍 (${PREMIUM_CUSTOM_PARLAYS_PER_PERIOD}/${PREMIUM_CUSTOM_PARLAYS_PERIOD_DAYS} days)`,
                "Win Probability",
              ].map((feature) => (
                <div key={feature} className="flex items-center gap-2 text-sm text-gray-300">
                  <Check className="h-3 w-3 text-emerald-400" />
                  {feature}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 pt-4 border-t border-white/5">
          {!subscription.has_subscription ? (
            <Link
              href="/pricing"
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-lg hover:from-emerald-400 hover:to-green-400 transition-all"
            >
              <Crown className="h-4 w-4" />
              Upgrade Now
            </Link>
          ) : (
            <>
              {isAutoRenewProvider && !subscription.is_lifetime && !subscription.cancel_at_period_end && (
                <button
                  onClick={() => setShowCancelConfirm(true)}
                  disabled={canceling}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-white/5 border border-white/10 text-gray-300 rounded-lg hover:bg-white/10 transition-all disabled:opacity-50"
                >
                  {canceling ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    "Cancel Subscription"
                  )}
                </button>
              )}
              <Link
                href="/pricing"
                className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 text-gray-300 rounded-lg hover:bg-white/10 transition-all"
              >
                <ExternalLink className="h-4 w-4" />
                View Plans
              </Link>
            </>
          )}
        </div>

        {/* Cancel confirmation */}
        {showCancelConfirm && isAutoRenewProvider && subscription.has_subscription && !subscription.is_lifetime && !subscription.cancel_at_period_end && (
          <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20">
            <p className="text-sm text-red-200 mb-3">
              Confirm cancellation? You&apos;ll keep access until the end of your current billing period.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowCancelConfirm(false)}
                disabled={canceling}
                className="flex-1 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-gray-300 hover:bg-white/10 transition-all disabled:opacity-50"
              >
                Keep Subscription
              </button>
              <button
                onClick={handleCancel}
                disabled={canceling}
                className="flex-1 px-4 py-2 rounded-lg bg-red-500 text-white font-semibold hover:bg-red-400 transition-all disabled:opacity-50"
              >
                {canceling ? <Loader2 className="h-4 w-4 animate-spin mx-auto" /> : "Confirm Cancel"}
              </button>
            </div>
          </div>
        )}
      </div>
    </GlassPanel>
  )
}

