"use client"

import { Award, BarChart3, Sparkles } from "lucide-react"

import { useSubscription } from "@/lib/subscription-context"
import { cn } from "@/lib/utils"
import type { UserStatsResponse } from "@/lib/usage/UserStatsRepository"

type PerformanceInsightsSectionProps = {
  stats: UserStatsResponse | null
  coachInsight: string
  className?: string
}

function InsightCard({
  title,
  icon: Icon,
  value,
  description,
  highlight,
  className,
}: {
  title: string
  icon: React.ComponentType<{ className?: string }>
  value: string
  description?: string
  highlight?: boolean
  className?: string
}) {
  return (
    <div
      className={cn(
        "rounded-2xl border backdrop-blur p-5 lg:p-6 transition-all",
        highlight
          ? "border-emerald-500/30 bg-gradient-to-br from-emerald-900/20 to-black/30"
          : "border-white/10 bg-black/25",
        className
      )}
    >
      <div className="flex items-center gap-2 mb-3">
        <Icon className={cn("w-5 h-5", highlight ? "text-emerald-400" : "text-cyan-400")} />
        <div className="text-xs font-black text-white uppercase tracking-wide">{title}</div>
      </div>
      <div className={cn("text-base font-black mb-2", highlight ? "text-emerald-300" : "text-white")}>
        {value}
      </div>
      {description && <div className="text-sm text-gray-200/70 mt-2">{description}</div>}
    </div>
  )
}

export function PerformanceInsightsSection({
  stats,
  coachInsight,
  className,
}: PerformanceInsightsSectionProps) {
  const { aiParlaysUsed, aiParlaysLimit } = useSubscription()

  const weeklyActivity = stats?.usage_breakdown?.weekly_activity
  const customAiBehavior = stats?.usage_breakdown?.custom_ai_behavior
  const mostActiveDay = weeklyActivity?.most_active_day
  const customAiShare = customAiBehavior?.custom_ai_share_percent ?? 0

  const usagePace = (() => {
    if (!aiParlaysLimit || aiParlaysLimit <= 0) return "No limit"
    const percent = (aiParlaysUsed / aiParlaysLimit) * 100
    if (percent <= 50) return "Steady pace"
    if (percent <= 75) return "Moderate usage"
    if (percent <= 90) return "High usage"
    return "Near limit"
  })()

  const rhythmPattern = mostActiveDay
    ? `Most active on ${mostActiveDay}`
    : "Consistent usage pattern"

  const customAiContext =
    customAiShare <= 25 && (stats?.custom_ai_parlays?.period_used ?? 0) > 0
      ? "Used selectively this cycle"
      : customAiShare > 50
        ? "Heavy Custom AI usage"
        : "Balanced usage this cycle"

  return (
    <section className={cn("space-y-4", className)}>
      <div className="flex items-center gap-2">
        <BarChart3 className="w-5 h-5 text-amber-400" />
        <h2 className="text-lg font-black text-white">Performance Insights</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 lg:gap-6">
        <InsightCard
          title="Pacing"
          icon={Sparkles}
          value={usagePace}
          description={coachInsight}
          highlight={true}
        />

        <InsightCard
          title="Rhythm"
          icon={BarChart3}
          value={rhythmPattern}
          description={
            mostActiveDay
              ? `Your activity peaks on ${mostActiveDay}s`
              : "You maintain consistent usage throughout the week"
          }
        />

        <InsightCard
          title="Custom AI Strategy"
          icon={Award}
          value={customAiContext}
          description={
            customAiShare > 50
              ? "You're maximizing Custom AI for targeted plays"
              : "You're using Custom AI strategically"
          }
        />
      </div>

      {/* Additional Performance Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-4">
        <div className="rounded-xl border border-white/10 bg-black/20 backdrop-blur p-4">
          <div className="text-xs uppercase tracking-wide text-gray-200/60 mb-1">Verified Wins</div>
          <div className="text-lg font-black text-emerald-300">{stats?.verified_wins?.lifetime ?? 0}</div>
          <div className="text-xs text-gray-200/60 mt-1">Lifetime total</div>
        </div>

        <div className="rounded-xl border border-white/10 bg-black/20 backdrop-blur p-4">
          <div className="text-xs uppercase tracking-wide text-gray-200/60 mb-1">30-Day Wins</div>
          <div className="text-lg font-black text-emerald-300">{stats?.verified_wins?.last_30_days ?? 0}</div>
          <div className="text-xs text-gray-200/60 mt-1">Recent activity</div>
        </div>

        <div className="rounded-xl border border-white/10 bg-black/20 backdrop-blur p-4">
          <div className="text-xs uppercase tracking-wide text-gray-200/60 mb-1">Leaderboard</div>
          <div className="text-lg font-black text-cyan-300">
            #{stats?.leaderboards?.verified_winners?.rank ?? "—"}
          </div>
          <div className="text-xs text-gray-200/60 mt-1">Verified winners rank</div>
        </div>

        <div className="rounded-xl border border-white/10 bg-black/20 backdrop-blur p-4">
          <div className="text-xs uppercase tracking-wide text-gray-200/60 mb-1">Usage Rank</div>
          <div className="text-lg font-black text-amber-300">
            #{stats?.leaderboards?.ai_usage_30d?.rank ?? "—"}
          </div>
          <div className="text-xs text-gray-200/60 mt-1">30-day usage rank</div>
        </div>
      </div>
    </section>
  )
}

