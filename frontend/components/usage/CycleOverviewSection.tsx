"use client"

import { useMemo } from "react"
import { motion } from "framer-motion"
import { Calendar, TrendingUp } from "lucide-react"

import { useSubscription } from "@/lib/subscription-context"
import { CREDITS_COST_AI_PARLAY } from "@/lib/pricingConfig"
import { UsageCoachInsightManager } from "@/lib/usage/UsageCoachInsightManager"
import { UsageGauge } from "./UsageGauge"
import { cn } from "@/lib/utils"
import type { UserStatsResponse } from "@/lib/usage/UserStatsRepository"

type CycleOverviewSectionProps = {
  stats: UserStatsResponse | null
  className?: string
}

function formatResetDate(iso?: string | null) {
  if (!iso) return "—"
  const d = new Date(iso)
  if (!Number.isFinite(d.getTime())) return "—"
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" })
}

function computeHelperFromPercent(percentUsed: number | null) {
  if (percentUsed === null) return "No limit this cycle"
  if (percentUsed <= 60) return "Plenty remaining this cycle"
  if (percentUsed <= 85) return "On pace — keep an eye on your usage"
  return "Almost at your cycle limit"
}

function percentUsed(used: number, limit: number) {
  if (!(limit > 0)) return null
  const pct = (Math.max(0, used) / limit) * 100
  return Math.max(0, Math.min(100, pct))
}

export function CycleOverviewSection({ stats, className }: CycleOverviewSectionProps) {
  const {
    isPremium,
    aiParlaysUsed,
    aiParlaysLimit,
    aiParlaysRemaining,
    customAiParlaysUsed,
    customAiParlaysLimit,
    customAiParlaysRemaining,
    creditsRemaining,
  } = useSubscription()

  const creditsEstimate = useMemo(() => {
    const mgr = new UsageCoachInsightManager()
    return mgr.estimateAiRunsFromCredits(creditsRemaining, CREDITS_COST_AI_PARLAY)
  }, [creditsRemaining])

  const aiPct = percentUsed(aiParlaysUsed, aiParlaysLimit)
  const customPct = percentUsed(customAiParlaysUsed, customAiParlaysLimit)

  const aiHelper = computeHelperFromPercent(aiPct)
  const customHelper =
    customAiParlaysLimit > 0 ? "Automatically verified on-chain" : "Not included on your current plan"

  return (
    <motion.section
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.05 }}
      className={cn("space-y-4", className)}
    >
      <div className="flex items-center gap-2">
        <Calendar className="w-5 h-5 text-emerald-400" />
        <h2 className="text-lg font-black text-white">This Cycle Overview</h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 lg:gap-6">
        {/* Primary: Cycle Progress — double width */}
        <div className="lg:col-span-6">
          <UsageGauge
            label={isPremium ? "Gorilla Parlays (Monthly)" : "Gorilla Parlays (Today)"}
            used={aiParlaysUsed}
            limit={aiParlaysLimit}
            helperText={aiHelper}
            tooltip={`Resets on ${formatResetDate(stats?.ai_parlays?.period_end ?? null)}`}
            className="h-full rounded-xl border border-white/10 backdrop-blur-xl bg-black/45 shadow-[0_4px_24px_-8px_rgba(0,0,0,0.5)] hover:shadow-[0_4px_28px_-8px_rgba(0,0,0,0.6)] transition-shadow duration-200"
          />
        </div>

        {/* Secondary cards */}
        <div className="lg:col-span-3">
          <UsageGauge
            label="Gorilla Builder Parlays (Monthly)"
            used={customAiParlaysUsed}
            limit={customAiParlaysLimit}
            helperText={customHelper}
            tooltip="Gorilla Parlay Builder lets you pick the games. Every parlay can be verified with a permanent, time-stamped record."
            className="h-full rounded-xl border border-white/10 backdrop-blur-xl bg-black/45 shadow-[0_4px_24px_-8px_rgba(0,0,0,0.5)] hover:shadow-[0_4px_28px_-8px_rgba(0,0,0,0.6)] transition-shadow duration-200"
          />
        </div>
        <div className="lg:col-span-3">
          <UsageGauge
            label="Credits Balance"
            valueText={`${creditsRemaining} credits`}
            limit={null}
            helperText={`Good for ~${creditsEstimate} Gorilla Parlay generations`}
            className="h-full rounded-xl border border-white/10 backdrop-blur-xl bg-black/45 shadow-[0_4px_24px_-8px_rgba(0,0,0,0.5)] hover:shadow-[0_4px_28px_-8px_rgba(0,0,0,0.6)] transition-shadow duration-200"
          />
        </div>
      </div>

      {/* Quick Stats Row — secondary hierarchy */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="rounded-xl border border-white/10 bg-black/40 backdrop-blur p-4 transition-shadow duration-200 hover:shadow-[0_2px_16px_-4px_rgba(0,0,0,0.4)]">
          <div className="text-xs uppercase tracking-wide text-gray-200/90 mb-1">Gorilla Parlays</div>
          <div className="flex items-center gap-2 mt-2">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            <div className="text-sm">
              <span className="font-black text-white">{aiParlaysRemaining}</span>
              <span className="text-gray-100/95 ml-1">remaining</span>
            </div>
          </div>
          <div className="text-xs text-gray-200/90 mt-1">
            Resets {formatResetDate(stats?.ai_parlays?.period_end ?? null)}
          </div>
        </div>

        <div className="rounded-xl border border-white/10 bg-black/40 backdrop-blur p-4 transition-shadow duration-200 hover:shadow-[0_2px_16px_-4px_rgba(0,0,0,0.4)]">
          <div className="text-xs uppercase tracking-wide text-gray-200/90 mb-1">Gorilla Parlay Builder</div>
          <div className="flex items-center gap-2 mt-2">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            <div className="text-sm">
              <span className="font-black text-white">{customAiParlaysRemaining}</span>
              <span className="text-gray-100/95 ml-1">remaining</span>
            </div>
          </div>
          <div className="text-xs text-gray-200/90 mt-1">
            Resets {formatResetDate(stats?.custom_ai_parlays?.period_end ?? null)}
          </div>
        </div>

        <div className="rounded-xl border border-white/10 bg-black/40 backdrop-blur p-4 transition-shadow duration-200 hover:shadow-[0_2px_16px_-4px_rgba(0,0,0,0.4)]">
          <div className="text-xs uppercase tracking-wide text-gray-200/90 mb-1">Lifetime Stats</div>
          <div className="text-sm mt-2">
            <span className="font-black text-white">{stats?.ai_parlays?.lifetime ?? 0}</span>
            <span className="text-gray-100/95 ml-1">total Gorilla Parlays</span>
          </div>
          <div className="text-xs text-gray-200/90 mt-1">
            {stats?.verified_wins?.lifetime ?? 0} verified wins
          </div>
        </div>
      </div>
    </motion.section>
  )
}


