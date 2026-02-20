"use client"

import { useEffect, useState } from "react"
import { Loader2, AlertCircle, TrendingUp, TrendingDown, Target } from "lucide-react"
import { cn } from "@/lib/utils"
import { api } from "@/lib/api"
import { motion } from "framer-motion"
import { SavedParlaysSection } from "@/components/analytics/SavedParlaysSection"
import { GlassCard } from "@/components/ui/GlassCard"
import { SectionHeader } from "@/components/ui/SectionHeader"
import { ToolShell } from "@/components/tools/ToolShell"
import { useSubscription } from "@/lib/subscription-context"

interface PerformanceStats {
  total_parlays: number
  hits: number
  misses: number
  hit_rate: number
  avg_predicted_prob: number
  avg_actual_prob: number
  avg_calibration_error: number
}

interface ParlayHistory {
  id: string
  num_legs: number
  risk_profile: string
  parlay_hit_prob: number
  created_at: string | null
}

export function Analytics() {
  const { isPremium } = useSubscription()
  const [stats, setStats] = useState<PerformanceStats | null>(null)
  const [history, setHistory] = useState<ParlayHistory[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedRiskProfile, setSelectedRiskProfile] = useState<string | null>(null)

  useEffect(() => {
    async function fetchAnalytics() {
      try {
        setLoading(true)
        setError(null)
        const statsData = await api.getAnalyticsPerformance(selectedRiskProfile || undefined)
        setStats(statsData)
        try {
          const historyData = await api.getMyParlays(50)
          setHistory(historyData)
        } catch (historyErr) {
          console.warn("Failed to fetch parlay history:", historyErr)
        }
      } catch (err: any) {
        console.error("Error fetching analytics:", err)
        setError(err.response?.data?.detail || err.message || "Failed to fetch analytics")
      } finally {
        setLoading(false)
      }
    }
    fetchAnalytics()
  }, [selectedRiskProfile])

  const pills: { label: string; value: string }[] = [
    { label: "Status", value: isPremium ? "Premium" : "Free" },
  ]
  if (stats) {
    pills.push({ label: "Parlays", value: String(stats.total_parlays) })
    pills.push({ label: "Hit rate", value: `${(stats.hit_rate * 100).toFixed(1)}%` })
  }

  const leftPanel = (
    <>
      <SectionHeader title="Risk profile" description="Filter stats by profile" />
      <div className="flex flex-col gap-2">
        <button
          onClick={() => setSelectedRiskProfile(null)}
          className={cn(
            "px-4 py-2 rounded-xl border-2 text-sm font-medium transition-all duration-150 hover:scale-[1.02]",
            selectedRiskProfile === null ? "ring-2 ring-green-500/40 border-emerald-500 bg-emerald-500/10 text-emerald-400" : "border-white/10 bg-white/5 text-gray-400 hover:border-white/20"
          )}
        >
          All Profiles
        </button>
        {["conservative", "balanced", "degen"].map((profile) => (
          <button
            key={profile}
            onClick={() => setSelectedRiskProfile(profile)}
            className={cn(
              "px-4 py-2 rounded-xl border-2 text-sm font-medium capitalize transition-all duration-150 hover:scale-[1.02]",
              selectedRiskProfile === profile ? "ring-2 ring-green-500/40 border-emerald-500 bg-emerald-500/10 text-emerald-400" : "border-white/10 bg-white/5 text-gray-400 hover:border-white/20"
            )}
          >
            {profile}
          </button>
        ))}
      </div>
    </>
  )

  const rightContent = loading ? (
    <div className="min-h-[280px] flex flex-col items-center justify-center py-12">
      <Loader2 className="h-8 w-8 animate-spin text-white/50" />
      <p className="mt-2 text-sm text-white/60">Loading analytics…</p>
    </div>
  ) : error ? (
    <div className="min-h-[280px] flex flex-col items-center justify-center py-12">
      <div className="text-center max-w-md px-4">
        <AlertCircle className="h-10 w-10 text-amber-400 mx-auto mb-3" />
        <h3 className="font-semibold text-white mb-1">Couldn’t load analytics</h3>
        <p className="text-sm text-white/60">{error}</p>
      </div>
    </div>
  ) : (
    <div className="space-y-6">
      {stats && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <GlassCard className="p-4 transition-transform duration-200 hover:-translate-y-1 hover:shadow-lg">
            <p className="text-xs font-medium text-white/50">Total Parlays</p>
            <p className="text-2xl font-bold text-white mt-1">{stats.total_parlays}</p>
          </GlassCard>
          <GlassCard className="p-4 transition-transform duration-200 hover:-translate-y-1 hover:shadow-lg">
            <p className="text-xs font-medium text-white/50">Hit Rate</p>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-2xl font-bold text-white">{(stats.hit_rate * 100).toFixed(1)}%</span>
              {stats.hit_rate > 0.5 ? <TrendingUp className="h-5 w-5 text-emerald-400" /> : <TrendingDown className="h-5 w-5 text-red-400" />}
            </div>
            <p className="text-xs text-white/50 mt-0.5">{stats.hits} hits / {stats.misses} misses</p>
          </GlassCard>
          <GlassCard className="p-4 transition-transform duration-200 hover:-translate-y-1 hover:shadow-lg">
            <p className="text-xs font-medium text-white/50">Avg Predicted Prob</p>
            <p className="text-2xl font-bold text-white mt-1">{(stats.avg_predicted_prob * 100).toFixed(1)}%</p>
          </GlassCard>
          <GlassCard className="p-4 transition-transform duration-200 hover:-translate-y-1 hover:shadow-lg">
            <p className="text-xs font-medium text-white/50">Calibration Error</p>
            <p className="text-2xl font-bold text-white mt-1">{(stats.avg_calibration_error * 100).toFixed(2)}%</p>
            <p className="text-xs text-white/50 mt-0.5">Lower is better</p>
          </GlassCard>
        </div>
      )}

      <SavedParlaysSection />

      <div>
        <SectionHeader title="Recent parlays" description="Your parlay history and performance" />
        {history.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Target className="h-12 w-12 text-white/30 mb-3" />
            <p className="text-white/60">No parlay history yet</p>
            <p className="text-sm text-white/40 mt-1">Start building parlays to see your analytics here</p>
          </div>
        ) : (
          <div className="space-y-3">
            {history.map((parlay) => (
              <div
                key={parlay.id}
                className="border border-white/10 rounded-xl p-4 bg-white/[0.02] hover:bg-white/[0.04] transition-transform duration-200 hover:-translate-y-0.5 hover:shadow-md"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-emerald-400">{parlay.num_legs}-Leg Parlay</span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 capitalize border border-emerald-500/30">{parlay.risk_profile}</span>
                </div>
                <p className="text-sm text-white/60">Hit probability: {(parlay.parlay_hit_prob * 100).toFixed(1)}%</p>
                {parlay.created_at && <p className="text-xs text-white/40 mt-1">{new Date(parlay.created_at).toLocaleDateString()}</p>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-6xl mx-auto overflow-x-hidden"
    >
      <ToolShell
        title="Insights"
        subtitle="Track your parlay performance and insights"
        pills={loading || error ? undefined : pills}
        left={leftPanel}
        right={rightContent}
      />
    </motion.div>
  )
}



