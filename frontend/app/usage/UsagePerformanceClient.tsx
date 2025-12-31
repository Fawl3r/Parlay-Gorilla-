"use client"

import { useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { AlertCircle, Loader2 } from "lucide-react"

import { AnimatedBackground } from "@/components/AnimatedBackground"
import { Footer } from "@/components/Footer"
import { Header } from "@/components/Header"
import { AiCoachInsight } from "@/components/usage/AiCoachInsight"
import { useAuth } from "@/lib/auth-context"
import { useSubscription } from "@/lib/subscription-context"
import { CREDITS_COST_AI_PARLAY } from "@/lib/pricingConfig"
import { UsageCoachInsightManager } from "@/lib/usage/UsageCoachInsightManager"
import { UserStatsRepository, type UserStatsResponse } from "@/lib/usage/UserStatsRepository"
import { cn } from "@/lib/utils"

function formatResetDate(iso?: string | null) {
  if (!iso) return "—"
  const d = new Date(iso)
  if (!Number.isFinite(d.getTime())) return "—"
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" })
}

function StatCard({
  title,
  lines,
  className,
}: {
  title: string
  lines: Array<{ label: string; value: string }>
  className?: string
}) {
  return (
    <div className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur p-5", className)}>
      <div className="text-xs uppercase tracking-wide text-gray-200/60">{title}</div>
      <div className="mt-3 space-y-2 text-sm text-gray-200/80">
        {lines.map((line) => (
          <div key={line.label} className="flex items-center justify-between gap-4">
            <span className="text-gray-200/70">{line.label}</span>
            <span className="font-black text-white">{line.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

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

  const creditsEstimate = useMemo(() => {
    const mgr = new UsageCoachInsightManager()
    return mgr.estimateAiRunsFromCredits(subscription.creditsRemaining, CREDITS_COST_AI_PARLAY)
  }, [subscription.creditsRemaining])

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
          <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
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
        <div className="max-w-6xl mx-auto space-y-8">
          <div>
            <h1 className="text-2xl md:text-3xl font-black text-white mb-2">Usage &amp; Performance</h1>
            <p className="text-gray-200/70">
              A clear view of what you have, what you’ve used, and how to stay in control.
            </p>
          </div>

          {error ? (
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 shrink-0" />
              <div className="text-sm text-red-200">{error}</div>
            </div>
          ) : null}

          <AiCoachInsight insight={coachInsight} />

          {/* This Cycle Overview */}
          <section className="space-y-3">
            <div className="text-sm font-black text-white">This Cycle Overview</div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <StatCard
                title="AI Parlays"
                lines={[
                  { label: "Used", value: `${subscription.aiParlaysUsed} / ${subscription.aiParlaysLimit}` },
                  { label: "Remaining", value: String(subscription.aiParlaysRemaining) },
                  { label: "Reset", value: formatResetDate(stats?.ai_parlays?.period_end ?? null) },
                ]}
              />
              <StatCard
                title="Custom AI"
                lines={[
                  { label: "Used", value: `${subscription.customAiParlaysUsed} / ${subscription.customAiParlaysLimit}` },
                  { label: "Remaining", value: String(subscription.customAiParlaysRemaining) },
                  { label: "Reset", value: formatResetDate(stats?.custom_ai_parlays?.period_end ?? null) },
                ]}
              />
              <StatCard
                title="Credits"
                lines={[
                  { label: "Balance", value: String(subscription.creditsRemaining) },
                  { label: "Estimated value", value: `~${creditsEstimate} AI runs` },
                ]}
              />
            </div>
          </section>

          {/* Usage Breakdown */}
          <section className="space-y-3">
            <div className="text-sm font-black text-white">Usage Breakdown</div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <StatCard
                title="Weekly Activity"
                lines={[
                  {
                    label: "This week",
                    value: `${stats?.usage_breakdown?.weekly_activity?.ai_parlays_this_week ?? 0} AI parlays`,
                  },
                  {
                    label: "Most active day",
                    value: String(stats?.usage_breakdown?.weekly_activity?.most_active_day ?? "—"),
                  },
                ]}
              />
              <StatCard
                title="Custom AI Behavior"
                lines={[
                  {
                    label: "Share (this cycle)",
                    value: `${stats?.usage_breakdown?.custom_ai_behavior?.custom_ai_share_percent ?? 0}%`,
                  },
                  {
                    label: "Verified on-chain",
                    value: `${stats?.usage_breakdown?.custom_ai_behavior?.verified_on_chain_this_period ?? 0} times`,
                  },
                ]}
              />
            </div>
          </section>

          {/* Performance Insights */}
          <section className="space-y-3">
            <div className="text-sm font-black text-white">Performance Insights</div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <StatCard
                title="Pacing"
                lines={[
                  {
                    label: "Coach",
                    value: coachInsight,
                  },
                ]}
              />
              <StatCard
                title="Rhythm"
                lines={[
                  {
                    label: "Pattern",
                    value:
                      stats?.usage_breakdown?.weekly_activity?.most_active_day
                        ? `Most active on ${stats.usage_breakdown.weekly_activity.most_active_day}`
                        : "—",
                  },
                ]}
              />
              <StatCard
                title="Custom AI"
                lines={[
                  {
                    label: "Context",
                    value:
                      (stats?.usage_breakdown?.custom_ai_behavior?.custom_ai_share_percent ?? 0) <= 25 &&
                      subscription.customAiParlaysUsed > 0
                        ? "Used selectively this cycle"
                        : "Balanced usage this cycle",
                  },
                ]}
              />
            </div>
          </section>

          {/* Smart Usage Tips */}
          <section className="space-y-3">
            <div className="text-sm font-black text-white">Smart Usage Tips</div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <StatCard title="Tip" lines={[{ label: "1", value: "Save Custom AI for games you already like." }]} />
              <StatCard title="Tip" lines={[{ label: "2", value: "AI Parlays are great for exploring slate-wide opportunities." }]} />
              <StatCard title="Tip" lines={[{ label: "3", value: "Credits are best used late in the cycle if needed." }]} />
            </div>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  )
}


