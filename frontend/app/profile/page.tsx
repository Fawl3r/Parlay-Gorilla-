"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { Loader2, ArrowLeft } from "lucide-react"
import Link from "next/link"
import { useAuth } from "@/lib/auth-context"
import { api, ProfileResponse } from "@/lib/api"
import { AnimatedBackground } from "@/components/AnimatedBackground"
import { Header } from "@/components/Header"
import { ProfileHeader } from "@/components/profile/ProfileHeader"
import { ProfileStats } from "@/components/profile/ProfileStats"
import { ProfileUsageStatsCard, type UserStatsResponse } from "@/components/profile/ProfileUsageStatsCard"
import { BadgeGrid } from "@/components/profile/BadgeGrid"
import { SubscriptionPanel } from "@/components/profile/SubscriptionPanel"
import { BillingHistory } from "@/components/profile/BillingHistory"
import { LeaderboardPrivacyCard } from "@/components/profile/LeaderboardPrivacyCard"

export default function ProfilePage() {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()
  
  const [profile, setProfile] = useState<ProfileResponse | null>(null)
  const [usageStats, setUsageStats] = useState<UserStatsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/auth/login")
      return
    }

    if (user) {
      loadProfile()
    }
  }, [user, authLoading, router])

  const loadProfile = async () => {
    try {
      setLoading(true)
      setError(null)

      const [profileRes, statsRes] = await Promise.allSettled([
        api.getMyProfile(),
        api.get("/api/users/me/stats"),
      ])

      if (profileRes.status !== "fulfilled") {
        throw profileRes.reason
      }
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

  const handleEdit = () => {
    // TODO: Open edit modal or navigate to edit page
    router.push("/profile/setup")
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center relative">
        <AnimatedBackground variant="subtle" />
        <Loader2 className="h-8 w-8 animate-spin text-emerald-500 relative z-10" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center relative">
        <AnimatedBackground variant="subtle" />
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

  return (
    <div className="min-h-screen flex flex-col relative" style={{ backgroundColor: "#0a0a0f" }}>
      <AnimatedBackground variant="subtle" />
      <Header />

      <main className="flex-1 py-8 px-4 relative z-10">
        <div className="max-w-6xl mx-auto space-y-8">
          {/* Back Button */}
          <Link
            href="/app"
            className="inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to App
          </Link>

          {/* Profile Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <ProfileHeader user={profile.user} onEdit={handleEdit} />
          </motion.div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column - Stats & Badges */}
            <div className="lg:col-span-2 space-y-8">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                <h2 className="text-lg font-semibold text-white mb-4">Statistics</h2>
                <ProfileStats stats={profile.stats} />
                <div className="mt-6">
                  <ProfileUsageStatsCard stats={usageStats} />
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <BadgeGrid badges={profile.badges} />
              </motion.div>
            </div>

            {/* Right Column - Subscription */}
            <div className="space-y-6">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                <LeaderboardPrivacyCard
                  initialVisibility={(profile.user.leaderboard_visibility as any) || "public"}
                  onSaved={() => loadProfile()}
                />
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.35 }}
              >
                <SubscriptionPanel />
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.45 }}
              >
                <BillingHistory />
              </motion.div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

