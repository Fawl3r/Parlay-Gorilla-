"use client"

import { motion } from "framer-motion"
import type { UserStatsResponse } from "@/lib/usage/UserStatsRepository"

export function PerformanceMetricsStrip({ stats }: { stats: UserStatsResponse | null }) {
  if (!stats) return null

  const items = [
    { label: "Verified Wins", value: stats.verified_wins?.lifetime ?? 0, sub: "Lifetime" },
    { label: "30-Day Wins", value: stats.verified_wins?.last_30_days ?? 0, sub: "Recent" },
    { label: "Leaderboard", value: `#${stats.leaderboards?.verified_winners?.rank ?? "—"}`, sub: "Verified" },
    { label: "Usage Rank", value: `#${stats.leaderboards?.ai_usage_30d?.rank ?? "—"}`, sub: "30-day" },
  ]

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.25 }}
      className="grid grid-cols-2 sm:grid-cols-4 gap-3"
    >
      {items.map((item) => (
        <div
          key={item.label}
          className="rounded-xl border border-white/10 bg-black/40 backdrop-blur p-4"
        >
          <div className="text-xs uppercase tracking-wider text-gray-200/90">{item.label}</div>
          <div className="text-lg font-black text-white mt-1">{item.value}</div>
          <div className="text-xs text-gray-200/88 mt-0.5">{item.sub}</div>
        </div>
      ))}
    </motion.div>
  )
}
