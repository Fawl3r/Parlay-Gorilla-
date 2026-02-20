"use client"

import { useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { AlertCircle, ArrowLeft, Loader2 } from "lucide-react"

import { DashboardLayout } from "@/components/layout/DashboardLayout"
import { AnimatedBackground } from "@/components/AnimatedBackground"
import { GorillaAiPerformanceBrief } from "@/components/usage/GorillaAiPerformanceBrief"
import { PerformanceScoreGauge, computePerformanceScoreFromStats } from "@/components/usage/PerformanceScoreGauge"
import { CycleOverviewSection } from "@/components/usage/CycleOverviewSection"
import { UsageIntelligenceViz } from "@/components/usage/UsageIntelligenceViz"
import { BehavioralIntelligenceSection } from "@/components/usage/BehavioralIntelligenceSection"
import { NextLevelGoalsSection } from "@/components/usage/NextLevelGoalsSection"
import { SmartActionsPanel } from "@/components/usage/SmartActionsPanel"
import { PerformanceMetricsStrip } from "@/components/usage/PerformanceMetricsStrip"
import { SmartTipsSection } from "@/components/usage/SmartTipsSection"
import { useAuth } from "@/lib/auth-context"
import { useSubscription } from "@/lib/subscription-context"
import { CREDITS_COST_AI_PARLAY } from "@/lib/pricingConfig"
import { getCopy } from "@/lib/content"
import { UsageCoachInsightManager } from "@/lib/usage/UsageCoachInsightManager"
import { UserStatsRepository, type UserStatsResponse } from "@/lib/usage/UserStatsRepository"

export default function UsagePerformanceClient() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()
  const subscription = useSubscription()

  const [stats, setStats] = useState<UserStatsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/auth/login?redirect=/usage")
    }
  }, [authLoading, user, router])

  useEffect(() => {
    if (!user) return
    let alive = true
    setLoading(true)
    setError(null)

    const repo = new UserStatsRepository()
    repo
      .getMyStats()
      .then((data) => {
        if (!alive) return
        setStats(data)
      })
      .catch((e: any) => {
        if (!alive) return
        setError(e?.response?.data?.detail || "Failed to load usage stats")
        setStats(null)
      })
      .finally(() => {
        if (!alive) return
        setLoading(false)
      })

    return () => {
      alive = false
    }
  }, [user])

  const coachInsight = useMemo(() => {
    const mgr = new UsageCoachInsightManager()
    return mgr.getSingleInsight({
      ai: {
        used: subscription.aiParlaysUsed,
        limit: subscription.aiParlaysLimit,
        remaining: subscription.aiParlaysRemaining,
        periodStartIso: stats?.ai_parlays?.period_start ?? null,
        periodEndIso: stats?.ai_parlays?.period_end ?? null,
      },
      custom: {
        used: subscription.customAiParlaysUsed,
        limit: subscription.customAiParlaysLimit,
        remaining: subscription.customAiParlaysRemaining,
      },
      credits: {
        balance: subscription.creditsRemaining,
        costPerAiParlay: CREDITS_COST_AI_PARLAY,
      },
    })
  }, [subscription, stats])

  const performanceScore = useMemo(
    () => computePerformanceScoreFromStats(stats),
    [stats]
  )

  const aiPercentUsed = useMemo(() => {
    const limit = subscription.aiParlaysLimit
    if (!(limit > 0)) return null
    return (subscription.aiParlaysUsed / limit) * 100
  }, [subscription.aiParlaysLimit, subscription.aiParlaysUsed])

  const briefStatus = useMemo(() => {
    if (aiPercentUsed === null) return "No limit"
    if (aiPercentUsed >= 86) return "Approaching limit"
    if (aiPercentUsed >= 60) return "Moderate usage"
    return "Healthy pace"
  }, [aiPercentUsed])

  const briefTrend = useMemo((): "up" | "stable" | "attention" => {
    if (aiPercentUsed === null) return "stable"
    if (aiPercentUsed >= 86) return "attention"
    return "stable"
  }, [aiPercentUsed])

  if (authLoading || loading) {
    return (
      <DashboardLayout>
        <div className="min-h-screen flex flex-col relative" style={{ backgroundColor: "#0b0b0b" }}>
          <main className="flex-1 flex items-center justify-center py-8 relative z-10">
            <div className="flex flex-col items-center gap-4">
              <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
              <p className="text-sm text-gray-100/95">{getCopy("states.loading.loadingData")}</p>
            </div>
          </main>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="min-h-screen flex flex-col relative" style={{ backgroundColor: "#0b0b0b" }}>
        <AnimatedBackground variant="subtle" />
        <div
          className="fixed inset-0 pointer-events-none z-[1]"
          aria-hidden
          style={{
            background:
              "linear-gradient(180deg, rgba(14,14,14,0.55) 0%, rgba(14,14,14,0.7) 50%, rgba(14,14,14,0.78) 100%)",
          }}
        />
        <main className="flex-1 py-8 relative z-10">
          <div className="container mx-auto px-4 max-w-6xl space-y-8 lg:space-y-10">
            <Link
              href="/app"
              className="inline-flex items-center gap-2 text-white/70 hover:text-white transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to App
            </Link>

            <div className="space-y-2">
              <h1 className="text-3xl md:text-4xl font-black text-white">Usage &amp; Performance</h1>
              <p className="text-base md:text-lg text-gray-100/95 max-w-2xl">
                A clear view of what you have, what you've used, and how to stay in control of your parlay strategy.
              </p>
            </div>

            {/* Error State */}
            {error ? (
              <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 shrink-0" />
                <div className="flex-1">
                  <div className="text-sm font-semibold text-red-200 mb-1">{getCopy("states.errors.loadFailed")}</div>
                  <div className="text-xs text-red-200/70">{error}</div>
                </div>
              </div>
            ) : null}

            {/* 1. AI Command Center Hero — Gorilla AI Performance Brief */}
            {coachInsight && (
              <GorillaAiPerformanceBrief
                insight={coachInsight}
                statusLabel={briefStatus}
                trend={briefTrend}
              />
            )}

            {/* 2. Performance Score Module */}
            <div className="flex justify-start">
              <PerformanceScoreGauge
                score={performanceScore.score}
                tierLabel={performanceScore.tierLabel}
              />
            </div>

            {/* 3. Cycle Overview — restructured */}
            <CycleOverviewSection stats={stats} />

            {/* 4. Usage Intelligence Visualization */}
            <UsageIntelligenceViz stats={stats} />

            {/* 5. AI Behavioral Analysis */}
            <BehavioralIntelligenceSection stats={stats} coachInsight={coachInsight ?? ""} />

            {/* Key metrics strip — keep all existing metrics visible */}
            <PerformanceMetricsStrip stats={stats} />

            {/* 6. Progression & Goals + Smart Actions */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8">
              <div className="lg:col-span-5">
                <NextLevelGoalsSection stats={stats} aiPercentUsed={aiPercentUsed} />
              </div>
              <div className="lg:col-span-7">
                <SmartActionsPanel />
              </div>
            </div>

            <SmartTipsSection />
          </div>
        </main>
      </div>
    </DashboardLayout>
  )
}
