"use client"

import { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import Link from "next/link"
import { Loader2, ArrowLeft, RefreshCw } from "lucide-react"

import { useAuth } from "@/lib/auth-context"
import { api, type ProfileResponse } from "@/lib/api"
import { AnimatedBackground } from "@/components/AnimatedBackground"
import { DashboardLayout } from "@/components/layout/DashboardLayout"
import { Header } from "@/components/Header"
import { ProfileHeroPanel, derivePersonaFromStats } from "@/components/profile/ProfileHeroPanel"
import { PerformanceIdentity } from "@/components/profile/PerformanceIdentity"
import { AiPlayerAnalysis } from "@/components/profile/AiPlayerAnalysis"
import { ProgressionSystem } from "@/components/profile/ProgressionSystem"
import { PrivacyLeaderboardSection } from "@/components/profile/PrivacyLeaderboardSection"
import { ProfileUsageStatsCard, type UserStatsResponse } from "@/components/profile/ProfileUsageStatsCard"
import { BadgeGrid } from "@/components/profile/BadgeGrid"
import { SubscriptionPanel } from "@/components/profile/SubscriptionPanel"
import { BillingHistory } from "@/components/profile/BillingHistory"
import { PwaInstalledBadge } from "@/components/pwa/PwaInstalledBadge"
import { StripeReconcileService } from "@/lib/billing/StripeReconcileService"

export default function ProfilePage() {
  const { user, loading: authLoading, signOut } = useAuth()
  const router = useRouter()

  const [profile, setProfile] = useState<ProfileResponse | null>(null)
  const [usageStats, setUsageStats] = useState<UserStatsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [syncing, setSyncing] = useState(false)

  const reconciler = useMemo(() => new StripeReconcileService(), [])

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/auth/login")
      return
    }
    if (user) loadProfile()
  }, [user, authLoading, router])

  const loadProfile = async () => {
    try {
      setLoading(true)
      setError(null)
      const [profileRes, statsRes] = await Promise.allSettled([
        api.getMyProfile(),
        api.get("/api/users/me/stats"),
      ])
      if (profileRes.status !== "fulfilled") throw profileRes.reason
      setProfile(profileRes.value)
      if (statsRes.status === "fulfilled") {
        setUsageStats(statsRes.value.data as UserStatsResponse)
      } else {
        setUsageStats(null)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load profile")
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = () => router.push("/profile/edit")
  const handleSignOut = async () => {
    await signOut()
    router.push("/auth/login")
  }

  const handleSync = async () => {
    try {
      setSyncing(true)
      setError(null)
      try {
        await reconciler.reconcileLatest()
      } catch (e) {
        console.warn("Stripe reconcile failed:", e)
      }
      await loadProfile()
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to sync")
      console.error("Sync error:", err)
    } finally {
      setSyncing(false)
    }
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center relative" style={{ backgroundColor: "#050505" }}>
        <AnimatedBackground variant="subtle" />
        <div
          className="fixed inset-0 pointer-events-none z-[1]"
          aria-hidden
          style={{ background: "linear-gradient(180deg, rgba(5,5,5,0.7) 0%, rgba(5,5,5,0.9) 100%)" }}
        />
        <Loader2 className="h-8 w-8 animate-spin text-emerald-500 relative z-10" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center relative" style={{ backgroundColor: "#050505" }}>
        <AnimatedBackground variant="subtle" />
        <div
          className="fixed inset-0 pointer-events-none z-[1]"
          aria-hidden
          style={{ background: "linear-gradient(180deg, rgba(5,5,5,0.7) 0%, rgba(5,5,5,0.9) 100%)" }}
        />
        <div className="text-center relative z-10">
          <p className="text-red-400 mb-4">{error}</p>
          <button
            onClick={loadProfile}
            className="px-4 py-2 bg-emerald-500 text-black rounded-lg hover:bg-emerald-400 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  if (!profile) return null

  const personaLabel = derivePersonaFromStats(profile.stats)

  return (
    <DashboardLayout>
      <div className="min-h-screen flex flex-col relative" style={{ backgroundColor: "#050505" }}>
        <AnimatedBackground variant="subtle" />
        <div
          className="fixed inset-0 pointer-events-none z-[1]"
          aria-hidden
          style={{
            background:
              "linear-gradient(180deg, rgba(5,5,5,0.7) 0%, rgba(5,5,5,0.85) 50%, rgba(5,5,5,0.9) 100%)",
          }}
        />
        <main className="flex-1 py-8 px-4 relative z-10">
          <div className="max-w-6xl mx-auto space-y-8">
            <Link
              href="/app"
              className="inline-flex items-center gap-2 text-white/70 hover:text-white transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to App
            </Link>

            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-sm font-black text-white uppercase tracking-wide">
                Player Intelligence Profile
              </h2>
              <PwaInstalledBadge />
            </div>

            <ProfileHeroPanel
              user={profile.user}
              onEdit={handleEdit}
              personaLabel={personaLabel}
            />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2 space-y-8">
                <PerformanceIdentity stats={profile.stats} />
                <AiPlayerAnalysis stats={profile.stats} />
                <ProgressionSystem
                  totalParlays={profile.stats.total_parlays}
                  nextMilestone={10}
                  streakDays={0}
                />
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">Statistics</h3>
                  <ProfileUsageStatsCard stats={usageStats} />
                </div>
                <BadgeGrid badges={profile.badges} />
              </div>

              <div className="space-y-6">
                <PrivacyLeaderboardSection
                  initialVisibility={(profile.user.leaderboard_visibility as any) || "public"}
                  onSaved={() => loadProfile()}
                />
                <SubscriptionPanel />
                <BillingHistory />
                <section className="rounded-2xl border border-white/10 bg-black/25 backdrop-blur p-5">
                  <div className="flex flex-wrap items-center gap-2 mb-3">
                    <h3 className="text-sm font-black text-white">Account</h3>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    <Link
                      href="/usage"
                      className="min-h-[44px] rounded-xl border border-white/10 bg-black/25 hover:bg-black/40 px-4 py-2 flex items-center text-sm font-semibold text-white/90 hover:text-white"
                    >
                      Usage & Performance
                    </Link>
                    <Link
                      href="/billing"
                      className="min-h-[44px] rounded-xl border border-white/10 bg-black/25 hover:bg-black/40 px-4 py-2 flex items-center text-sm font-semibold text-white/90 hover:text-white"
                    >
                      Plan & Billing
                    </Link>
                    <Link
                      href="/settings"
                      className="min-h-[44px] rounded-xl border border-white/10 bg-black/25 hover:bg-black/40 px-4 py-2 flex items-center text-sm font-semibold text-white/90 hover:text-white"
                    >
                      Settings
                    </Link>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-3">
                    <button
                      type="button"
                      onClick={handleSync}
                      disabled={syncing}
                      className="flex items-center gap-2 min-h-[44px] px-4 py-2 rounded-xl border border-white/10 bg-black/40 text-white/90 hover:bg-black/55 font-semibold disabled:opacity-50"
                    >
                      {syncing ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          Syncing...
                        </>
                      ) : (
                        <>
                          <RefreshCw className="h-4 w-4" />
                          Sync Billing
                        </>
                      )}
                    </button>
                    <button
                      type="button"
                      onClick={handleSignOut}
                      className="min-h-[44px] px-4 py-2 rounded-xl border border-white/10 bg-black/40 text-white/90 hover:bg-black/55 font-semibold"
                    >
                      Log out
                    </button>
                  </div>
                </section>
              </div>
            </div>
          </div>
        </main>
      </div>
    </DashboardLayout>
  )
}
