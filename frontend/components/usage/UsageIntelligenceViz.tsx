"use client"

import { motion } from "framer-motion"
import { Activity, Target } from "lucide-react"

import { useSubscription } from "@/lib/subscription-context"
import { cn } from "@/lib/utils"
import type { UserStatsResponse } from "@/lib/usage/UserStatsRepository"

export type UsageIntelligenceVizProps = {
  stats: UserStatsResponse | null
  className?: string
}

function MiniBarChart({
  thisWeek,
  last30,
  mostActiveDay,
}: {
  thisWeek: number
  last30: number
  mostActiveDay: string | null
}) {
  const max = Math.max(1, thisWeek, last30)
  const weekHeight = max > 0 ? (thisWeek / max) * 100 : 0
  const monthHeight = max > 0 ? (last30 / max) * 100 : 0

  return (
    <div className="space-y-3">
      <div className="flex items-end gap-4 h-20">
        <div className="flex-1 flex flex-col items-center gap-1">
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: `${weekHeight}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="w-full max-w-[48px] rounded-t bg-emerald-400/90"
            title={`This week: ${thisWeek} parlays`}
          />
          <span className="text-xs text-gray-100/95">This week</span>
        </div>
        <div className="flex-1 flex flex-col items-center gap-1">
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: `${monthHeight}%` }}
            transition={{ duration: 0.5, delay: 0.1, ease: "easeOut" }}
            className="w-full max-w-[48px] rounded-t bg-cyan-400/80"
            title={`Last 30 days: ${last30} parlays`}
          />
          <span className="text-xs text-gray-100/95">Last 30d</span>
        </div>
      </div>
      <div className="text-xs text-gray-200/90">
        {mostActiveDay ? (
          <span>Most active day: {mostActiveDay}</span>
        ) : (
          <span>Weekly activity</span>
        )}
      </div>
    </div>
  )
}

function ProgressBar({
  label,
  value,
  max,
  suffix,
  colorClass,
  delay = 0,
}: {
  label: string
  value: number
  max: number
  suffix: string
  colorClass: string
  delay?: number
}) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-xs">
        <span className="text-gray-100/95">{label}</span>
        <span className="text-white font-semibold">{value}{suffix}</span>
      </div>
      <div className="h-2 rounded-full bg-white/10 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, delay, ease: "easeOut" }}
          className={cn("h-full rounded-full", colorClass)}
        />
      </div>
    </div>
  )
}

export function UsageIntelligenceViz({ stats, className }: UsageIntelligenceVizProps) {
  const { customAiParlaysUsed, customAiParlaysLimit } = useSubscription()
  const weeklyActivity = stats?.usage_breakdown?.weekly_activity
  const customAiBehavior = stats?.usage_breakdown?.custom_ai_behavior

  const aiParlaysThisWeek = weeklyActivity?.ai_parlays_this_week ?? 0
  const last30 = stats?.ai_parlays?.last_30_days ?? 0
  const mostActiveDay = weeklyActivity?.most_active_day ?? null
  const customAiShare = customAiBehavior?.custom_ai_share_percent ?? 0
  const verifiedOnChain = customAiBehavior?.verified_on_chain_this_period ?? 0
  const builderUsed = stats?.custom_ai_parlays?.period_used ?? 0
  const builderLimit = customAiParlaysLimit > 0 ? customAiParlaysLimit : 1

  return (
    <motion.section
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.08 }}
      className={cn("space-y-4", className)}
    >
      <div className="flex items-center gap-2">
        <Activity className="w-5 h-5 text-cyan-400" />
        <h2 className="text-lg font-black text-white">Usage Intelligence</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 lg:gap-6">
        <div
          className={cn(
            "rounded-xl border border-white/10 backdrop-blur-xl p-5 lg:p-6",
            "bg-black/45 shadow-[0_4px_24px_-8px_rgba(0,0,0,0.5)]",
            "hover:shadow-[0_4px_28px_-8px_rgba(0,0,0,0.6)] transition-shadow duration-200"
          )}
        >
          <div className="flex items-center gap-2 mb-4">
            <Target className="w-5 h-5 text-emerald-400" />
            <span className="text-xs font-black text-white uppercase tracking-wide">
              Weekly Activity
            </span>
          </div>
          <MiniBarChart
            thisWeek={aiParlaysThisWeek}
            last30={last30}
            mostActiveDay={mostActiveDay}
          />
        </div>

        <div
          className={cn(
            "rounded-xl border border-white/10 backdrop-blur-xl p-5 lg:p-6",
            "bg-black/45 shadow-[0_4px_24px_-8px_rgba(0,0,0,0.5)]",
            "hover:shadow-[0_4px_28px_-8px_rgba(0,0,0,0.6)] transition-shadow duration-200"
          )}
        >
          <div className="flex items-center gap-2 mb-4">
            <Target className="w-5 h-5 text-cyan-400" />
            <span className="text-xs font-black text-white uppercase tracking-wide">
              Builder Usage
            </span>
          </div>
          <div className="space-y-5">
            <ProgressBar
              label="Builder share this cycle"
              value={customAiShare}
              max={100}
              suffix="%"
              colorClass="bg-cyan-400/90"
              delay={0.1}
            />
            <ProgressBar
              label="Builder parlays used"
              value={builderUsed}
              max={builderLimit}
              suffix=""
              colorClass="bg-emerald-400/90"
              delay={0.2}
            />
            <div className="text-xs text-gray-200/90 pt-1">
              Verified on-chain this period: <span className="font-semibold text-white">{verifiedOnChain}</span>
            </div>
          </div>
        </div>
      </div>
    </motion.section>
  )
}
