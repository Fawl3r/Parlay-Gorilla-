"use client"

import { motion } from "framer-motion"
import { Brain, Zap, Target } from "lucide-react"

import { cn } from "@/lib/utils"
import type { UserStatsResponse } from "@/lib/usage/UserStatsRepository"

export type BehavioralIntelligenceSectionProps = {
  stats: UserStatsResponse | null
  coachInsight: string
  className?: string
}

function Bullet({
  icon: Icon,
  phrase,
  className,
}: {
  icon: React.ComponentType<{ className?: string }>
  phrase: string
  className?: string
}) {
  return (
    <div className={cn("flex items-start gap-3", className)}>
      <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-cyan-500/15 flex items-center justify-center">
        <Icon className="w-4 h-4 text-cyan-400" />
      </div>
      <p className="text-sm text-white/95 leading-relaxed">{phrase}</p>
    </div>
  )
}

export function BehavioralIntelligenceSection({
  stats,
  coachInsight,
  className,
}: BehavioralIntelligenceSectionProps) {
  const weeklyActivity = stats?.usage_breakdown?.weekly_activity
  const customAiBehavior = stats?.usage_breakdown?.custom_ai_behavior
  const mostActiveDay = weeklyActivity?.most_active_day
  const customAiShare = customAiBehavior?.custom_ai_share_percent ?? 0
  const verifiedOnChain = customAiBehavior?.verified_on_chain_this_period ?? 0

  const rhythmPhrase = mostActiveDay
    ? `Pattern identified: your activity peaks on ${mostActiveDay}s.`
    : "AI detected a consistent usage pattern across the week."

  const builderPhrase =
    customAiShare <= 25 && (stats?.custom_ai_parlays?.period_used ?? 0) > 0
      ? "AI detected selective Gorilla Parlay Builder usage — typically the most effective approach."
      : customAiShare > 50
        ? "Pattern identified: heavy Builder usage; you're targeting specific games effectively."
        : "Efficiency observation: balanced use of AI parlays and Builder this cycle."

  const verificationPhrase =
    verifiedOnChain > 0
      ? `Optimization opportunity: you've verified ${verifiedOnChain} parlays on-chain this period — strong accountability.`
      : "Optimization opportunity: verify Builder parlays on-chain for a permanent record and leaderboard impact."

  const insightPhrase = coachInsight
    ? `AI insight: ${coachInsight}`
    : "Performance tendencies look healthy. Keep pacing as-is."

  return (
    <motion.section
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.1 }}
      className={cn("space-y-4", className)}
    >
      <div className="flex items-center gap-2">
        <Brain className="w-5 h-5 text-cyan-400" />
        <h2 className="text-lg font-black text-white">Behavioral Intelligence</h2>
      </div>

      <div
        className={cn(
          "rounded-xl border border-white/10 backdrop-blur-xl p-6",
          "bg-gradient-to-br from-cyan-950/25 to-black/55",
          "shadow-[0_4px_24px_-8px_rgba(0,0,0,0.5)]"
        )}
      >
        <div className="space-y-5">
          <Bullet icon={Zap} phrase={insightPhrase} />
          <Bullet icon={Target} phrase={rhythmPhrase} />
          <Bullet icon={Brain} phrase={builderPhrase} />
          <Bullet icon={Target} phrase={verificationPhrase} />
        </div>
      </div>
    </motion.section>
  )
}
