"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2, AlertCircle, TrendingUp, TrendingDown, Target, BarChart3 } from "lucide-react"
import { cn } from "@/lib/utils"
import { api } from "@/lib/api"
import { motion } from "framer-motion"
import { SavedParlaysSection } from "@/components/analytics/SavedParlaysSection"

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

        // Fetch performance stats
        const statsData = await api.getAnalyticsPerformance(selectedRiskProfile || undefined)
        setStats(statsData)

        // Fetch parlay history
        try {
          const historyData = await api.getMyParlays(50)
          setHistory(historyData)
        } catch (historyErr) {
          // History fetch is optional, don't fail if it errors
          console.warn("Failed to fetch parlay history:", historyErr)
        }
      } catch (err: any) {
        console.error('Error fetching analytics:', err)
        const message = err.response?.data?.detail || err.message || "Failed to fetch analytics"
        setError(message)
      } finally {
        setLoading(false)
      }
    }

    fetchAnalytics()
  }, [selectedRiskProfile])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Card className="w-full max-w-md">
          <CardContent className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            <span className="ml-2 text-muted-foreground">Loading analytics...</span>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-12">
        <Card className="w-full max-w-md">
          <CardContent className="flex items-center justify-center gap-3 py-12">
            <AlertCircle className="h-8 w-8 text-destructive" />
            <div>
              <h3 className="font-semibold text-destructive">Error loading analytics</h3>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8 max-w-6xl mx-auto"
    >
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-foreground mb-2">Analytics Dashboard</h2>
        <p className="text-muted-foreground">Track your parlay performance and insights</p>
      </div>

      {/* Risk Profile Filter */}
      <div className="flex justify-center gap-2">
        <button
          onClick={() => setSelectedRiskProfile(null)}
          className={cn(
            "px-4 py-2 rounded-md border-2 transition-colors text-sm",
            selectedRiskProfile === null
              ? "border-emerald-500 bg-emerald-500/10 text-emerald-400"
              : "border-white/10 bg-white/5 text-gray-400 hover:border-white/20"
          )}
        >
          All Profiles
        </button>
        {["conservative", "balanced", "degen"].map((profile) => (
          <button
            key={profile}
            onClick={() => setSelectedRiskProfile(profile)}
            className={cn(
              "px-4 py-2 rounded-md border-2 transition-colors capitalize text-sm",
              selectedRiskProfile === profile
                ? "border-emerald-500 bg-emerald-500/10 text-emerald-400"
                : "border-white/10 bg-white/5 text-gray-400 hover:border-white/20"
            )}
          >
            {profile}
          </button>
        ))}
      </div>

      {/* Performance Stats */}
      {stats && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <Card className="bg-white/[0.02] border-white/10">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-gray-400">
                Total Parlays
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-white">{stats.total_parlays}</div>
            </CardContent>
          </Card>

          <Card className="bg-white/[0.02] border-white/10">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-gray-400">
                Hit Rate
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <div className="text-3xl font-bold text-white">
                  {(stats.hit_rate * 100).toFixed(1)}%
                </div>
                {stats.hit_rate > 0.5 ? (
                  <TrendingUp className="h-5 w-5 text-emerald-400" />
                ) : (
                  <TrendingDown className="h-5 w-5 text-red-400" />
                )}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {stats.hits} hits / {stats.misses} misses
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white/[0.02] border-white/10">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-gray-400">
                Avg Predicted Prob
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-white">
                {(stats.avg_predicted_prob * 100).toFixed(1)}%
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/[0.02] border-white/10">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-gray-400">
                Calibration Error
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-white">
                {(stats.avg_calibration_error * 100).toFixed(2)}%
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Lower is better
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      <SavedParlaysSection />

      {/* Parlay History */}
      <Card className="bg-white/[0.02] border-white/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <BarChart3 className="h-5 w-5" />
            Recent Parlays
          </CardTitle>
          <CardDescription className="text-gray-400">
            Your parlay history and performance
          </CardDescription>
        </CardHeader>
        <CardContent>
          {history.length === 0 ? (
            <div className="text-center py-12">
              <Target className="h-12 w-12 mx-auto text-gray-500 mb-4" />
              <p className="text-gray-400">No parlay history yet</p>
              <p className="text-sm text-gray-500 mt-2">
                Start building parlays to see your analytics here
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {history.map((parlay) => (
                <div
                  key={parlay.id}
                  className="border border-white/10 rounded-lg p-4 bg-white/[0.02] hover:bg-white/[0.04] transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-semibold text-emerald-400">
                          {parlay.num_legs}-Leg Parlay
                        </span>
                        <span className="text-xs px-2 py-1 rounded-full bg-emerald-500/20 text-emerald-400 capitalize border border-emerald-500/30">
                          {parlay.risk_profile}
                        </span>
                      </div>
                      <p className="text-sm text-gray-400">
                        Hit Probability: {(parlay.parlay_hit_prob * 100).toFixed(1)}%
                      </p>
                      {parlay.created_at && (
                        <p className="text-xs text-gray-500 mt-1">
                          {new Date(parlay.created_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}



