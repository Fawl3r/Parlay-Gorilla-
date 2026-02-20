"use client"

import { motion } from "framer-motion"

import { cn } from "@/lib/utils"

export type PerformanceScoreGaugeProps = {
  score: number
  tierLabel: string
  className?: string
}

const TIER_COLORS = {
  learning: { ring: "stroke-amber-400", text: "text-amber-300", bg: "from-amber-500/10" },
  optimized: { ring: "stroke-emerald-400", text: "text-emerald-300", bg: "from-emerald-500/10" },
  elite: { ring: "stroke-cyan-400", text: "text-cyan-300", bg: "from-cyan-500/10" },
} as const

function getTier(score: number): keyof typeof TIER_COLORS {
  if (score >= 75) return "elite"
  if (score >= 45) return "optimized"
  return "learning"
}

export function PerformanceScoreGauge({
  score,
  tierLabel,
  className,
}: PerformanceScoreGaugeProps) {
  const clamped = Math.max(0, Math.min(100, Math.round(score)))
  const tier = getTier(clamped)
  const colors = TIER_COLORS[tier]

  const size = 180
  const strokeWidth = 12
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (clamped / 100) * circumference

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={cn(
        "rounded-xl border border-white/10 backdrop-blur-xl p-6",
        "bg-gradient-to-br",
        colors.bg,
        "to-black/60 shadow-[0_4px_24px_-8px_rgba(0,0,0,0.6)]",
        "hover:shadow-[0_4px_28px_-8px_rgba(0,0,0,0.6)] transition-shadow duration-200",
        className
      )}
    >
      <div className="flex flex-col items-center">
        <div className="relative" style={{ width: size, height: size }}>
          <svg width={size} height={size} className="rotate-[-90deg]" aria-hidden>
            <circle
              className="stroke-white/10"
              fill="transparent"
              strokeWidth={strokeWidth}
              r={radius}
              cx={size / 2}
              cy={size / 2}
              strokeLinecap="round"
            />
            <motion.circle
              className={cn("transition-colors duration-300", colors.ring)}
              fill="transparent"
              strokeWidth={strokeWidth}
              r={radius}
              cx={size / 2}
              cy={size / 2}
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              strokeLinecap="round"
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset: offset }}
              transition={{ duration: 1, ease: "easeOut" }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <motion.span
              className={cn("text-3xl font-black tabular-nums", colors.text)}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2, duration: 0.25 }}
            >
              {clamped}
            </motion.span>
            <span className="text-xs uppercase tracking-wider text-gray-200/90 mt-1">
              Performance
            </span>
          </div>
        </div>
        <p className="mt-4 text-xs uppercase tracking-wider text-gray-100/95">{tierLabel}</p>
      </div>
    </motion.div>
  )
}

export function computePerformanceScoreFromStats(stats: {
  ai_parlays?: { period_used?: number; period_limit?: number; last_30_days?: number }
  verified_wins?: { lifetime?: number; last_30_days?: number }
  leaderboards?: { ai_usage_30d?: { rank?: number | null } }
  usage_breakdown?: { custom_ai_behavior?: { custom_ai_share_percent?: number } }
} | null): { score: number; tierLabel: string } {
  if (!stats) return { score: 50, tierLabel: "Learning" }

  let score = 40
  const limit = stats.ai_parlays?.period_limit
  const used = stats.ai_parlays?.period_used ?? 0
  const pctUsed = limit && limit > 0 ? (used / limit) * 100 : 0

  if (pctUsed <= 85 && used > 0) score += 20
  if (stats.verified_wins?.lifetime && stats.verified_wins.lifetime > 0) score += 15
  if (stats.verified_wins?.last_30_days && stats.verified_wins.last_30_days > 0) score += 10
  const rank = stats.leaderboards?.ai_usage_30d?.rank
  if (rank != null && rank <= 100) score += 10
  const builderShare = stats.usage_breakdown?.custom_ai_behavior?.custom_ai_share_percent ?? 0
  if (builderShare > 0 && builderShare <= 60) score += 5

  const s = Math.max(0, Math.min(100, score))
  const tierLabel = s >= 75 ? "Elite" : s >= 45 ? "Optimized" : "Learning"
  return { score: s, tierLabel }
}
