"use client"

import { motion } from "framer-motion"
import { Target, Zap, BarChart2, Activity } from "lucide-react"
import type { ParlayStatsResponse } from "@/lib/api"
import { cn } from "@/lib/utils"

interface PerformanceIdentityProps {
  stats: ParlayStatsResponse
  className?: string
}

const RISK_ICONS: Record<string, string> = {
  conservative: "🛡️",
  balanced: "⚖️",
  degen: "🔥",
}

export function PerformanceIdentity({ stats, className }: PerformanceIdentityProps) {
  const topSports = Object.entries(stats.by_sport)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5)
  const total = stats.total_parlays
  const sportPcts = topSports.map(([sport, count]) => ({
    sport,
    count,
    pct: total > 0 ? (count / total) * 100 : 0,
  }))

  const riskEntries = Object.entries(stats.by_risk_profile).sort(
    ([, a], [, b]) => b - a
  )
  const topRisk = riskEntries[0]?.[0] ?? "balanced"
  const riskPcts = riskEntries.map(([name, count]) => ({
    name,
    count,
    pct: total > 0 ? (count / total) * 100 : 0,
  }))

  const activityLevel =
    total === 0 ? 0 : total < 5 ? 1 : total < 20 ? 2 : total < 50 ? 3 : 4

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className={cn(
        "rounded-2xl border border-white/10 bg-black/20 backdrop-blur p-6",
        className
      )}
    >
      <p className="text-xs uppercase tracking-widest text-white/50 mb-4">
        Performance Identity
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h3 className="text-sm font-bold text-white mb-3">Playstyle & risk</h3>
          <div className="space-y-3">
            {riskPcts.map(({ name, pct }, i) => (
              <div key={name} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-white/70 capitalize flex items-center gap-1">
                    {RISK_ICONS[name] ?? "•"} {name}
                  </span>
                  <span className="text-white/90 font-semibold">{pct.toFixed(0)}%</span>
                </div>
                <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.5, delay: 0.1 * i }}
                    className="h-full bg-gradient-to-r from-[#00FF5E] to-emerald-400 rounded-full"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
        <div>
          <h3 className="text-sm font-bold text-white mb-3">Sports preference</h3>
          <div className="space-y-3">
            {sportPcts.map(({ sport, pct }, i) => (
              <div key={sport} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-white/70">{sport}</span>
                  <span className="text-white/90 font-semibold">{pct.toFixed(0)}%</span>
                </div>
                <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.5, delay: 0.1 * i }}
                    className="h-full bg-gradient-to-r from-amber-500/80 to-amber-400/80 rounded-full"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="mt-6 flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10">
          <Target className="h-4 w-4 text-[#00FF5E]" />
          <span className="text-sm font-bold text-white">{stats.total_parlays}</span>
          <span className="text-xs text-white/50">Total parlays</span>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10">
          <Zap className="h-4 w-4 text-amber-400" />
          <span className="text-sm font-bold text-white capitalize">{topRisk}</span>
          <span className="text-xs text-white/50">Most used style</span>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10">
          <Activity className="h-4 w-4 text-cyan-400" />
          <span className="text-sm font-bold text-white">
            {activityLevel === 0 ? "New" : activityLevel === 1 ? "Light" : activityLevel === 2 ? "Active" : "Power user"}
          </span>
          <span className="text-xs text-white/50">Activity</span>
        </div>
      </div>
    </motion.section>
  )
}
