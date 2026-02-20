"use client"

import { motion } from "framer-motion"
import { CheckCircle, Crown, Loader2, Sparkles, Zap } from "lucide-react"
import { formatPlanName } from "@/lib/utils/planNameFormatter"
import { SubscriptionPlanCtaResolver } from "./SubscriptionPlanCtaResolver"
import { cn } from "@/lib/utils"
import type { AccessStatus, SubscriptionPlan } from "./types"
import { PREMIUM_AI_PARLAYS_PER_PERIOD, PREMIUM_AI_PARLAYS_PERIOD_DAYS } from "@/lib/pricingConfig"

interface PlanComparisonSmartProps {
  subscriptionPlans: SubscriptionPlan[]
  accessStatus: AccessStatus | null
  purchaseLoading: string | null
  onSubscribe: (planId: string) => void
  onManagePlan: () => void
  isEmailVerified: boolean
  className?: string
}

function deriveRecommendedPlan(
  plans: SubscriptionPlan[],
  accessStatus: AccessStatus | null
): SubscriptionPlan | null {
  if (!plans.length) return null
  const lifetime = plans.find((p) => p.period === "lifetime")
  const featured = plans.find((p) => p.is_featured)
  if (accessStatus?.subscription.active && accessStatus.subscription.is_lifetime)
    return null
  if (accessStatus?.subscription.remaining_today <= 3 && accessStatus?.subscription.active && lifetime)
    return lifetime
  return featured ?? lifetime ?? plans[0] ?? null
}

export function PlanComparisonSmart({
  subscriptionPlans,
  accessStatus,
  purchaseLoading,
  onSubscribe,
  onManagePlan,
  isEmailVerified,
  className,
}: PlanComparisonSmartProps) {
  const ctaResolver = new SubscriptionPlanCtaResolver(accessStatus?.subscription ?? null)
  const recommended = deriveRecommendedPlan(subscriptionPlans, accessStatus)
  const currentPlanName = accessStatus?.subscription.active && accessStatus.subscription.plan
    ? formatPlanName(accessStatus.subscription.plan)
    : "Free"

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className={cn("rounded-2xl border border-white/10 bg-black/20 backdrop-blur p-6", className)}
    >
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <h2 className="text-lg font-black text-white flex items-center gap-2">
          <Crown className="h-5 w-5 text-emerald-400" />
          Plan Comparison
        </h2>
        {recommended && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#00FF5E]/10 border border-[#00FF5E]/20">
            <Sparkles className="h-4 w-4 text-[#00FF5E]" />
            <span className="text-xs font-bold text-[#00FF5E]">
              Gorilla AI recommends {formatPlanName(recommended.name)} based on usage.
            </span>
          </div>
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
          <p className="text-xs uppercase tracking-widest text-white/70 mb-2">Current Plan</p>
          <p className="text-xl font-bold text-white">{currentPlanName}</p>
          {accessStatus?.subscription.active && (
            <p className="text-sm text-emerald-400 mt-1">Active</p>
          )}
        </div>
        <div className="rounded-xl border border-[#00FF5E]/20 bg-[#00FF5E]/5 p-4">
          <p className="text-xs uppercase tracking-widest text-[#00FF5E]/80 mb-2">Recommended</p>
          <p className="text-xl font-bold text-white">
            {recommended ? formatPlanName(recommended.name) : "—"}
          </p>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
          <p className="text-xs uppercase tracking-widest text-white/70 mb-2">Pro Upgrade</p>
          <p className="text-sm text-white/92">Unlock full AI parlays & builder</p>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {subscriptionPlans.map((plan, index) => {
          const cta = ctaResolver.resolve(plan, purchaseLoading !== null)
          const busy = purchaseLoading === plan.id || purchaseLoading === "portal"
          const isRec = recommended?.id === plan.id

          const handleClick = () => {
            if (cta.action === "none") return
            if (cta.action === "portal") {
              onManagePlan()
              return
            }
            if (!isEmailVerified && cta.action === "checkout") return
            onSubscribe(plan.id)
          }

          const disabled = cta.disabled || (!isEmailVerified && cta.action === "checkout")

          return (
            <motion.div
              key={plan.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 * index }}
              className={cn(
                "relative rounded-xl border p-6",
                plan.is_featured || isRec
                  ? "bg-gradient-to-br from-emerald-900/20 to-green-900/10 border-emerald-500/30"
                  : "bg-white/5 border-white/10"
              )}
            >
              {(plan.is_featured || isRec) && (
                <div className="absolute -top-2.5 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-bold uppercase">
                  {isRec ? "AI Recommended" : "Popular"}
                </div>
              )}
              <h3 className="text-xl font-bold text-white">{formatPlanName(plan.name)}</h3>
              <p className="text-sm text-white/78 mt-1">{plan.description}</p>
              <div className="mt-4 flex items-baseline gap-1">
                <span className="text-3xl font-black text-white">${plan.price}</span>
                <span className="text-white/70">
                  {plan.period === "lifetime" ? " one-time" : `/${plan.period === "yearly" ? "yr" : "mo"}`}
                </span>
              </div>
              <div className="mt-4 flex items-center gap-2 text-sm text-white/85">
                <Zap className="h-4 w-4 text-amber-400" />
                {plan.daily_parlay_limit > 0
                  ? `${plan.daily_parlay_limit} parlays/day`
                  : `${PREMIUM_AI_PARLAYS_PER_PERIOD} AI / ${PREMIUM_AI_PARLAYS_PERIOD_DAYS} days`}
              </div>
              <ul className="mt-4 space-y-2">
                {plan.features.slice(0, 4).map((f, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-white/92">
                    <CheckCircle className="h-4 w-4 text-emerald-400 shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>
              <button
                onClick={handleClick}
                disabled={disabled}
                className={cn(
                  "mt-6 w-full py-3 rounded-lg font-bold transition-all",
                  plan.is_featured || isRec
                    ? "bg-emerald-500 text-black hover:bg-emerald-400"
                    : "bg-white/10 text-white hover:bg-white/20"
                )}
              >
                {busy ? <Loader2 className="h-4 w-4 animate-spin mx-auto" /> : cta.label}
              </button>
              {!isEmailVerified && cta.action === "checkout" && (
                <p className="mt-2 text-xs text-amber-400 text-center">Verify email to purchase</p>
              )}
            </motion.div>
          )
        })}
      </div>
    </motion.section>
  )
}
