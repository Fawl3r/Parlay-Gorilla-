"use client"

import { motion } from "framer-motion"
import { Crown, Zap, Shield } from "lucide-react"
import { cn } from "@/lib/utils"
import type { AccessStatus } from "./types"

interface BillingStatusHeroProps {
  accessStatus: AccessStatus | null
  planName?: string
  isLifetime?: boolean
  className?: string
}

function deriveStatusBadge(accessStatus: AccessStatus | null): {
  label: string
  variant: "active" | "optimized" | "near_limit" | "free"
} {
  if (!accessStatus) return { label: "Free", variant: "free" }
  const { subscription, credits } = accessStatus
  if (subscription.active && subscription.is_lifetime)
    return { label: "Lifetime", variant: "active" }
  if (subscription.active) {
    const pct =
      subscription.daily_limit > 0
        ? (subscription.remaining_today / subscription.daily_limit) * 100
        : 100
    if (pct <= 15) return { label: "Near Limit", variant: "near_limit" }
    return { label: "Active", variant: "optimized" }
  }
  if (credits.balance > 20) return { label: "Credits", variant: "optimized" }
  return { label: "Free", variant: "free" }
}

function deriveAiInsightLine(accessStatus: AccessStatus | null): string {
  if (!accessStatus) return "Upgrade to unlock more AI parlays and builder usage."
  const { subscription, credits } = accessStatus
  const hasHeadroom =
    (subscription.active && subscription.remaining_today > 5) ||
    credits.balance > 10
  if (subscription.active && subscription.is_lifetime)
    return "Lifetime plan — no renewal. Your usage is well within limits."
  if (hasHeadroom)
    return "At current pace, your plan comfortably supports your usage."
  if (subscription.remaining_today <= 2 && subscription.active)
    return "Consider topping up credits or wait for your next period reset."
  return "Add credits or upgrade for more AI power when you need it."
}

export function BillingStatusHero({
  accessStatus,
  planName = "Free",
  isLifetime = false,
  className,
}: BillingStatusHeroProps) {
  const badge = deriveStatusBadge(accessStatus)
  const insight = deriveAiInsightLine(accessStatus)

  const remaining =
    accessStatus?.subscription.active && accessStatus.subscription.daily_limit > 0
      ? accessStatus.subscription.remaining_today
      : accessStatus?.free.remaining ?? 0
  const limit =
    accessStatus?.subscription.active && accessStatus.subscription.daily_limit > 0
      ? accessStatus.subscription.daily_limit
      : accessStatus?.free.total ?? 5

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        "relative rounded-2xl border overflow-hidden",
        "bg-gradient-to-br from-white/[0.08] to-white/[0.02] backdrop-blur-xl",
        "border-white/10",
        "shadow-[0_0_40px_-12px rgba(0,255,94,0.15)]",
        className
      )}
    >
      <div className="absolute inset-0 rounded-2xl border border-[#00FF5E]/20 pointer-events-none opacity-60" />
      <div className="relative p-6 md:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-widest text-white/70 mb-1">
              Gorilla AI Subscription Status
            </p>
            <h1 className="text-2xl md:text-3xl font-black text-white mb-2">
              {planName}
              {isLifetime && (
                <span className="ml-2 text-lg font-semibold text-emerald-400">
                  Lifetime
                </span>
              )}
            </h1>
            <div className="flex flex-wrap items-center gap-3 mt-2">
              <span className="inline-flex items-center gap-1.5 text-sm text-white/80">
                <Zap className="h-4 w-4 text-[#00FF5E]" />
                AI parlays: {remaining} / {limit} remaining
              </span>
              {accessStatus?.credits.balance != null && (
                <span className="text-sm text-white/78">
                  Credits: {accessStatus.credits.balance}
                </span>
              )}
            </div>
            <p className="mt-3 text-sm text-white/70 max-w-xl">{insight}</p>
          </div>
          <div className="flex items-center gap-2">
            <StatusBadge variant={badge.variant} label={badge.label} />
          </div>
        </div>
      </div>
    </motion.section>
  )
}

function StatusBadge({
  variant,
  label,
}: {
  variant: "active" | "optimized" | "near_limit" | "free"
  label: string
}) {
  const styles = {
    active:
      "bg-emerald-500/20 border-emerald-500/40 text-emerald-300",
    optimized:
      "bg-[#00FF5E]/10 border-[#00FF5E]/30 text-[#00FF5E]",
    near_limit:
      "bg-amber-500/20 border-amber-500/40 text-amber-300",
    free:
      "bg-white/10 border-white/20 text-white/92",
  }
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-bold uppercase tracking-wide",
        styles[variant]
      )}
    >
      <Shield className="h-3.5 w-3.5" />
      {label}
    </span>
  )
}
