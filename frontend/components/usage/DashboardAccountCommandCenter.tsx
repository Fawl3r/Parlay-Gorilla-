"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { BarChart3, Target, Zap } from "lucide-react"

import { useAuth } from "@/lib/auth-context"
import { useSubscription } from "@/lib/subscription-context"
import { CREDITS_COST_AI_PARLAY } from "@/lib/pricingConfig"
import { UsageCoachInsightManager } from "@/lib/usage/UsageCoachInsightManager"
import { UserStatsRepository, type UserStatsResponse } from "@/lib/usage/UserStatsRepository"
import { cn } from "@/lib/utils"

import { AiCoachInsight } from "./AiCoachInsight"
import { MiniUsageBar } from "./MiniUsageBar"
import { UsageGauge } from "./UsageGauge"

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

export function DashboardAccountCommandCenter({ className }: { className?: string }) {
  const { user } = useAuth()
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

  const [stats, setStats] = useState<UserStatsResponse | null>(null)

  useEffect(() => {
    if (!user) return

    let alive = true
    const repo = new UserStatsRepository()
    repo
      .getMyStats()
      .then((data) => {
        if (!alive) return
        setStats(data)
      })
      .catch(() => {
        if (!alive) return
        setStats(null)
      })

    return () => {
      alive = false
    }
  }, [user])

  const coachInsight = useMemo(() => {
    const manager = new UsageCoachInsightManager()
    return manager.getSingleInsight({
      ai: {
        used: aiParlaysUsed,
        limit: aiParlaysLimit,
        remaining: aiParlaysRemaining,
        periodStartIso: stats?.ai_parlays?.period_start ?? null,
        periodEndIso: stats?.ai_parlays?.period_end ?? null,
      },
      custom: {
        used: customAiParlaysUsed,
        limit: customAiParlaysLimit,
        remaining: customAiParlaysRemaining,
      },
      credits: {
        balance: creditsRemaining,
        costPerAiParlay: CREDITS_COST_AI_PARLAY,
      },
    })
  }, [
    aiParlaysUsed,
    aiParlaysLimit,
    aiParlaysRemaining,
    customAiParlaysUsed,
    customAiParlaysLimit,
    customAiParlaysRemaining,
    creditsRemaining,
    stats,
  ])

  const creditsEstimate = useMemo(() => {
    const manager = new UsageCoachInsightManager()
    return manager.estimateAiRunsFromCredits(creditsRemaining, CREDITS_COST_AI_PARLAY)
  }, [creditsRemaining])

  if (!user) return null

  const aiPct = percentUsed(aiParlaysUsed, aiParlaysLimit)
  const customPct = percentUsed(customAiParlaysUsed, customAiParlaysLimit)

  const aiHelper = computeHelperFromPercent(aiPct)
  const customHelper = isPremium
    ? customAiParlaysLimit > 0
      ? "Automatically verified"
      : "Not included on your current plan"
    : customAiParlaysLimit > 0
      ? "5 free per week (no verification)"
      : "Weekly limit reached"

  return (
    <section className={cn("space-y-4 sm:space-y-6", className)}>
      <div className="rounded-2xl border border-white/10 bg-black/25 backdrop-blur p-5 sm:p-6">
        <h1 className="text-xl sm:text-2xl font-black text-white">Your Parlay Gorilla Dashboard</h1>
        <p className="mt-1 text-sm text-gray-200/70">Everything you need to track usage, performance, and next moves.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <UsageGauge
          label={isPremium ? "Gorilla Parlays (Monthly)" : "Gorilla Parlays (Weekly)"}
          used={aiParlaysUsed}
          limit={aiParlaysLimit}
          helperText={aiHelper}
        />

        <UsageGauge
          label={isPremium ? "Custom AI Parlays (Monthly)" : "Custom AI Parlays (Weekly)"}
          used={customAiParlaysUsed}
          limit={customAiParlaysLimit}
          helperText={customHelper}
          tooltip={isPremium ? "Custom AI lets you pick the games. Every parlay is automatically verified with a permanent, time-stamped record." : "Custom AI lets you pick the games. Free users get 5 per week (no verification). Premium users get unlimited with automatic verification."}
        />

        <UsageGauge
          label="Credits Balance"
          valueText={`${creditsRemaining} credits`}
          limit={null}
          helperText={`Good for ~${creditsEstimate} Gorilla Parlay generations`}
        />
      </div>

      <AiCoachInsight insight={coachInsight} />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <Link
          href="/app?tab=ai-builder"
          className={cn(
            "rounded-2xl border border-white/10 bg-white/[0.03] hover:bg-white/[0.06] transition-colors",
            "p-5 flex items-start justify-between gap-4"
          )}
        >
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-white font-black">
              <Zap className="h-4 w-4 text-emerald-300" />
              Generate Gorilla Parlay ({Math.max(0, aiParlaysRemaining)} remaining)
            </div>
            <div className="mt-2">
              <MiniUsageBar remaining={aiParlaysRemaining} limit={aiParlaysLimit} />
            </div>
          </div>
        </Link>

        <Link
          href="/app?tab=custom-builder"
          className={cn(
            "rounded-2xl border border-white/10 bg-white/[0.03] hover:bg-white/[0.06] transition-colors",
            "p-5 flex items-start justify-between gap-4"
          )}
        >
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-white font-black">
              <Target className="h-4 w-4 text-cyan-300" />
              Gorilla Builder Parlays ({Math.max(0, customAiParlaysRemaining)} remaining)
            </div>
            <div className="mt-2">
              <MiniUsageBar remaining={customAiParlaysRemaining} limit={customAiParlaysLimit} />
            </div>
          </div>
        </Link>

        <Link
          href="/usage"
          className={cn(
            "rounded-2xl border border-white/10 bg-white/[0.03] hover:bg-white/[0.06] transition-colors",
            "p-5 flex items-start justify-between gap-4"
          )}
        >
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-white font-black">
              <BarChart3 className="h-4 w-4 text-amber-300" />
              View Usage &amp; Performance
            </div>
            <div className="mt-2 text-sm text-gray-200/70">See cycle totals, weekly activity, and smart tips.</div>
          </div>
        </Link>
      </div>
    </section>
  )
}

export default DashboardAccountCommandCenter


