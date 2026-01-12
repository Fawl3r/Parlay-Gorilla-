"use client"

import { useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { AlertCircle, Loader2 } from "lucide-react"

import { AnimatedBackground } from "@/components/AnimatedBackground"
import { Footer } from "@/components/Footer"
import { Header } from "@/components/Header"
import { AiCoachInsight } from "@/components/usage/AiCoachInsight"
import { CycleOverviewSection } from "@/components/usage/CycleOverviewSection"
import { UsageBreakdownSection } from "@/components/usage/UsageBreakdownSection"
import { PerformanceInsightsSection } from "@/components/usage/PerformanceInsightsSection"
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

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex flex-col bg-gradient-to-b from-[#0a0a0f] via-[#0d1117] to-[#0a0a0f]">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
            <p className="text-sm text-gray-200/70">{getCopy("states.loading.loadingData")}</p>
          </div>
        </main>
        <Footer />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col relative" style={{ backgroundColor: "#0a0a0f" }}>
      <AnimatedBackground variant="subtle" />
      <Header />

      <main className="flex-1 py-8 px-4 relative z-10">
        <div className="max-w-7xl mx-auto space-y-8 lg:space-y-10">
          {/* Header */}
          <div className="space-y-2">
            <h1 className="text-3xl md:text-4xl font-black text-white">Usage &amp; Performance</h1>
            <p className="text-base md:text-lg text-gray-200/70 max-w-2xl">
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

          {/* AI Coach Insight */}
          {coachInsight && <AiCoachInsight insight={coachInsight} />}

          {/* Main Content Sections */}
          <CycleOverviewSection stats={stats} />

          <UsageBreakdownSection stats={stats} />

          <PerformanceInsightsSection stats={stats} coachInsight={coachInsight} />

          <SmartTipsSection />
        </div>
      </main>

      <Footer />
    </div>
  )
}
