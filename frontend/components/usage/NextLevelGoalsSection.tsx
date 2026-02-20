"use client"

import { motion } from "framer-motion"
import { Check, Circle } from "lucide-react"

import { cn } from "@/lib/utils"
import type { UserStatsResponse } from "@/lib/usage/UserStatsRepository"

export type NextLevelGoalsSectionProps = {
  stats: UserStatsResponse | null
  aiPercentUsed: number | null
  className?: string
}

function GoalItem({
  done,
  label,
  delay = 0,
}: {
  done: boolean
  label: string
  delay?: number
}) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -4 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.25, delay }}
      className="flex items-center gap-3"
    >
      {done ? (
        <Check className="w-5 h-5 text-emerald-400 flex-shrink-0" aria-hidden />
      ) : (
        <Circle className="w-5 h-5 text-gray-200/90 flex-shrink-0" aria-hidden />
      )}
      <span
        className={cn(
          "text-sm",
          done ? "text-white/95" : "text-gray-200/92"
        )}
      >
        {label}
      </span>
    </motion.div>
  )
}

export function NextLevelGoalsSection({
  stats,
  aiPercentUsed,
  className,
}: NextLevelGoalsSectionProps) {
  const hasVerifiedWins = (stats?.verified_wins?.lifetime ?? 0) > 0
  const hasRecentWins = (stats?.verified_wins?.last_30_days ?? 0) > 0
  const hasBuilderUsage = (stats?.custom_ai_parlays?.period_used ?? 0) > 0
  const hasOnChainVerification =
    (stats?.usage_breakdown?.custom_ai_behavior?.verified_on_chain_this_period ?? 0) > 0
  const pacingOk = aiPercentUsed === null || aiPercentUsed <= 85

  const goals = [
    { done: pacingOk, label: "Stay within cycle pacing" },
    { done: hasBuilderUsage, label: "Use Gorilla Parlay Builder this cycle" },
    { done: hasOnChainVerification, label: "Verify at least one parlay on-chain" },
    { done: hasVerifiedWins, label: "Log a verified win (lifetime)" },
    { done: hasRecentWins, label: "Log a verified win in the last 30 days" },
  ]

  return (
    <motion.section
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.15 }}
      className={cn("space-y-4", className)}
    >
      <div className="flex items-center gap-2">
        <span className="text-lg font-black text-white">Next Level Goals</span>
      </div>

      <div
        className={cn(
          "rounded-xl border border-white/10 backdrop-blur-xl p-6",
          "bg-black/45 shadow-[0_4px_24px_-8px_rgba(0,0,0,0.5)]"
        )}
      >
        <p className="text-xs uppercase tracking-wider text-gray-200/90 mb-4">
          Progress toward a higher performance tier
        </p>
        <div className="space-y-3">
          {goals.map((g, i) => (
            <GoalItem key={g.label} done={g.done} label={g.label} delay={i * 0.05} />
          ))}
        </div>
      </div>
    </motion.section>
  )
}
