"use client"

import { Activity, Target, TrendingUp } from "lucide-react"

import { useSubscription } from "@/lib/subscription-context"
import { cn } from "@/lib/utils"
import type { UserStatsResponse } from "@/lib/usage/UserStatsRepository"

type UsageBreakdownSectionProps = {
  stats: UserStatsResponse | null
  className?: string
}

function StatCard({
  title,
  icon: Icon,
  lines,
  className,
}: {
  title: string
  icon: React.ComponentType<{ className?: string }>
  lines: Array<{ label: string; value: string; highlight?: boolean }>
  className?: string
}) {
  return (
    <div className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur p-5 lg:p-6", className)}>
      <div className="flex items-center gap-2 mb-4">
        <Icon className="w-5 h-5 text-emerald-400" />
        <div className="text-sm font-black text-white uppercase tracking-wide">{title}</div>
      </div>
      <div className="space-y-3">
        {lines.map((line) => (
          <div key={line.label} className="flex items-center justify-between gap-4">
            <span className="text-sm text-gray-200/70">{line.label}</span>
            <span
              className={cn(
                "text-sm font-black",
                line.highlight ? "text-emerald-300" : "text-white"
              )}
            >
              {line.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export function UsageBreakdownSection({ stats, className }: UsageBreakdownSectionProps) {
  const { customAiParlaysUsed } = useSubscription()

  const weeklyActivity = stats?.usage_breakdown?.weekly_activity
  const customAiBehavior = stats?.usage_breakdown?.custom_ai_behavior

  const mostActiveDay = weeklyActivity?.most_active_day ?? null
  const aiParlaysThisWeek = weeklyActivity?.ai_parlays_this_week ?? 0
  const customAiShare = customAiBehavior?.custom_ai_share_percent ?? 0
  const verifiedOnChain = customAiBehavior?.verified_on_chain_this_period ?? 0

  return (
    <section className={cn("space-y-4", className)}>
      <div className="flex items-center gap-2">
        <Activity className="w-5 h-5 text-cyan-400" />
        <h2 className="text-lg font-black text-white">Usage Breakdown</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 lg:gap-6">
        <StatCard
          title="Weekly Activity"
          icon={TrendingUp}
          lines={[
            {
              label: "This week",
              value: `${aiParlaysThisWeek} Gorilla Parlays`,
              highlight: aiParlaysThisWeek > 0,
            },
            {
              label: "Most active day",
              value: mostActiveDay ? mostActiveDay : "—",
              highlight: !!mostActiveDay,
            },
            {
              label: "Last 30 days",
              value: `${stats?.ai_parlays?.last_30_days ?? 0} total`,
            },
          ]}
        />

        <StatCard
          title="Gorilla Parlay Builder"
          icon={Target}
          lines={[
            {
              label: "Share (this cycle)",
              value: `${customAiShare}%`,
              highlight: customAiShare > 0,
            },
            {
              label: "Verified on-chain",
              value: `${verifiedOnChain} times`,
              highlight: verifiedOnChain > 0,
            },
            {
              label: "Lifetime saved",
              value: `${stats?.custom_ai_parlays?.saved_lifetime ?? 0} parlays`,
            },
          ]}
        />
      </div>
    </section>
  )
}


