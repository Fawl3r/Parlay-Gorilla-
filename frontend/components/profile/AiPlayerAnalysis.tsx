"use client"

import { motion } from "framer-motion"
import { Brain, TrendingUp, Lightbulb } from "lucide-react"
import type { ParlayStatsResponse } from "@/lib/api"
import { cn } from "@/lib/utils"

interface AiPlayerAnalysisProps {
  stats: ParlayStatsResponse
  className?: string
}

function deriveInsights(stats: ParlayStatsResponse): string[] {
  const insights: string[] = []
  const total = stats.total_parlays
  if (total === 0) {
    insights.push("AI detected you're new. Generate a few parlays to get personalized insights.")
    return insights
  }
  const topSport = Object.entries(stats.by_sport).sort(([, a], [, b]) => b - a)[0]
  if (topSport) {
    const pct = total > 0 ? ((topSport[1] / total) * 100).toFixed(0) : "0"
    insights.push(`Your strongest pattern: ${pct}% of parlays are ${topSport[0]}.`)
  }
  const topRisk = Object.entries(stats.by_risk_profile).sort(([, a], [, b]) => b - a)[0]
  if (topRisk) {
    insights.push(`AI detected a ${topRisk[0]} tendency — good for consistency.`)
  }
  if (total >= 10) {
    insights.push("Usage pattern suggests you're engaging regularly. Consider upgrading for more AI parlays.")
  }
  return insights
}

export function AiPlayerAnalysis({ stats, className }: AiPlayerAnalysisProps) {
  const insights = deriveInsights(stats)

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className={cn(
        "rounded-2xl border border-[#00FF5E]/20 bg-[#00FF5E]/5 backdrop-blur p-6",
        className
      )}
    >
      <div className="flex items-center gap-2 mb-4">
        <Brain className="h-5 w-5 text-[#00FF5E]" />
        <h2 className="text-lg font-black text-white">How Gorilla AI Understands You</h2>
      </div>
      <p className="text-sm text-white/70 mb-4">
        Betting tendencies, usage patterns, and improvement insights — derived from your activity.
      </p>
      <ul className="space-y-3">
        {insights.map((text, i) => (
          <motion.li
            key={i}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 * i }}
            className="flex items-start gap-3 text-sm text-white/90"
          >
            <Lightbulb className="h-4 w-4 text-[#00FF5E] shrink-0 mt-0.5" />
            {text}
          </motion.li>
        ))}
      </ul>
    </motion.section>
  )
}
