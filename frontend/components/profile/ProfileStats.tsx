"use client"

import { motion } from "framer-motion"
import { TrendingUp, Target, Zap, BarChart2 } from "lucide-react"
import type { ParlayStatsResponse } from "@/lib/api"

interface ProfileStatsProps {
  stats: ParlayStatsResponse
}

export function ProfileStats({ stats }: ProfileStatsProps) {
  const topSports = Object.entries(stats.by_sport)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 4)

  const topRiskProfiles = Object.entries(stats.by_risk_profile)
    .sort(([, a], [, b]) => b - a)

  return (
    <div className="space-y-6">
      {/* Main Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          icon={<Target className="h-5 w-5" />}
          label="Total Parlays"
          value={stats.total_parlays}
          color="emerald"
        />
        <StatCard
          icon={<TrendingUp className="h-5 w-5" />}
          label="Sports Played"
          value={Object.keys(stats.by_sport).length}
          color="blue"
        />
        <StatCard
          icon={<Zap className="h-5 w-5" />}
          label="Most Used Style"
          value={topRiskProfiles[0]?.[0] || "N/A"}
          isText
          color="purple"
        />
        <StatCard
          icon={<BarChart2 className="h-5 w-5" />}
          label="Top Sport"
          value={topSports[0]?.[0] || "N/A"}
          isText
          color="orange"
        />
      </div>

      {/* Sport Breakdown */}
      {topSports.length > 0 && (
        <div className="bg-white/[0.02] border border-white/5 rounded-xl p-6">
          <h3 className="text-sm font-medium text-gray-400 mb-4">Parlays by Sport</h3>
          <div className="space-y-3">
            {topSports.map(([sport, count], index) => {
              const percentage = stats.total_parlays > 0 
                ? (count / stats.total_parlays) * 100 
                : 0
              
              return (
                <div key={sport} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-300">{sport}</span>
                    <span className="text-gray-500">{count} ({percentage.toFixed(0)}%)</span>
                  </div>
                  <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${percentage}%` }}
                      transition={{ duration: 0.5, delay: index * 0.1 }}
                      className="h-full bg-gradient-to-r from-emerald-500 to-green-400 rounded-full"
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Risk Profile Breakdown */}
      {topRiskProfiles.length > 0 && (
        <div className="bg-white/[0.02] border border-white/5 rounded-xl p-6">
          <h3 className="text-sm font-medium text-gray-400 mb-4">Parlays by Risk Profile</h3>
          <div className="grid grid-cols-3 gap-4">
            {["conservative", "balanced", "degen"].map((profile) => {
              const count = stats.by_risk_profile[profile] || 0
              const percentage = stats.total_parlays > 0 
                ? (count / stats.total_parlays) * 100 
                : 0
              
              const icons: Record<string, string> = {
                conservative: "🛡️",
                balanced: "⚖️",
                degen: "🔥",
              }
              
              return (
                <div key={profile} className="text-center p-4 bg-white/[0.02] rounded-lg">
                  <span className="text-2xl">{icons[profile]}</span>
                  <p className="text-white font-semibold mt-2">{count}</p>
                  <p className="text-xs text-gray-500 capitalize">{profile}</p>
                  <p className="text-xs text-emerald-400">{percentage.toFixed(0)}%</p>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

interface StatCardProps {
  icon: React.ReactNode
  label: string
  value: number | string
  isText?: boolean
  color?: "emerald" | "blue" | "purple" | "orange"
}

function StatCard({ icon, label, value, isText, color = "emerald" }: StatCardProps) {
  const colorClasses = {
    emerald: "from-[#00DD55]/20 to-[#00DD55]/5 border-[#00DD55]/20 text-[#00DD55]",
    blue: "from-blue-500/20 to-blue-500/5 border-blue-500/20 text-blue-400",
    purple: "from-purple-500/20 to-purple-500/5 border-purple-500/20 text-purple-400",
    orange: "from-orange-500/20 to-orange-500/5 border-orange-500/20 text-orange-400",
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-gradient-to-br ${colorClasses[color]} border rounded-xl p-4`}
    >
      <div className={`${colorClasses[color].split(" ").pop()} mb-2`}>
        {icon}
      </div>
      <p className={`${isText ? "text-lg" : "text-2xl"} font-bold text-white capitalize`}>
        {value}
      </p>
      <p className="text-xs text-white/60 mt-1">{label}</p>
    </motion.div>
  )
}

