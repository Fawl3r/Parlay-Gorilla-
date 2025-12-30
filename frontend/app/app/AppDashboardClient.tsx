"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { BarChart3, Calendar, Target, Zap } from "lucide-react"
import { motion } from "framer-motion"
import { useSearchParams } from "next/navigation"

import { Header } from "@/components/Header"
import { AnimatedBackground } from "@/components/AnimatedBackground"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { Analytics } from "@/components/Analytics"
import { ParlayBuilder } from "@/components/ParlayBuilder"
import { CustomParlayBuilder } from "@/components/CustomParlayBuilder"
import { BalanceStrip } from "@/components/billing/BalanceStrip"
import { SportBackground } from "@/components/games/SportBackground"
import { SPORT_BACKGROUNDS, type SportSlug } from "@/components/games/gamesConfig"

import { DashboardTabs, type TabType } from "@/app/app/_components/DashboardTabs"
import { UpcomingGamesTab } from "@/app/app/_components/tabs/UpcomingGamesTab"

export default function AppDashboardClient() {
  const searchParams = useSearchParams()
  const [activeTab, setActiveTab] = useState<TabType>("games")
  const [gamesSport, setGamesSport] = useState<SportSlug>("nfl")

  const tabParam = String(searchParams.get("tab") || "")
  useEffect(() => {
    const next = tabParam as TabType
    if (next === "games" || next === "ai-builder" || next === "custom-builder" || next === "analytics") {
      setActiveTab(next)
    }
  }, [tabParam])

  const prefillRequest = useMemo(() => {
    const sport = String(searchParams.get("sport") || "").toLowerCase().trim() || undefined
    const gameId = String(searchParams.get("prefill_game_id") || "").trim() || undefined
    const marketType = (String(searchParams.get("prefill_market_type") || "").trim() || undefined) as
      | "h2h"
      | "spreads"
      | "totals"
      | undefined
    const pick = String(searchParams.get("prefill_pick") || "").trim() || undefined
    const pointRaw = String(searchParams.get("prefill_point") || "").trim()
    const point = pointRaw ? Number(pointRaw) : undefined
    const pointSafe = Number.isFinite(point) ? point : undefined

    if (!sport || !gameId || !marketType || !pick) return undefined
    return { sport, gameId, marketType, pick, point: pointSafe }
  }, [searchParams])

  const tabs = useMemo(
    () => [
      { id: "games" as const, label: "Games", icon: Calendar },
      { id: "ai-builder" as const, label: "Build", icon: Zap },
      { id: "custom-builder" as const, label: "Your Picks", icon: Target },
      { id: "analytics" as const, label: "Insights", icon: BarChart3 },
    ],
    []
  )

  const gamesBackgroundImage = SPORT_BACKGROUNDS[gamesSport] || "/images/nflll.png"

  return (
    <ProtectedRoute>
      <div className="min-h-screen flex flex-col relative" style={{ backgroundColor: "#0a0a0f" }}>
        <AnimatedBackground variant="intense" />
        {activeTab === "games" && <SportBackground imageUrl={gamesBackgroundImage} overlay="light" className="bg-transparent" />}
        <Header />

        {/* Keep the dashboard “one screen” and scroll inside tab panels when needed. */}
        <main className="flex-1 relative z-10 overflow-hidden flex flex-col">
          {/* Header */}
          <section className="border-b border-white/10 bg-black/40 backdrop-blur-md">
            <div className="container mx-auto px-4 py-4 sm:py-5">
              <div className="flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <h1 className="text-xl sm:text-2xl font-black text-white">Gorilla Dashboard</h1>
                  <p className="text-xs sm:text-sm text-gray-400">Upcoming games, AI parlays, custom slips, and analytics</p>
                </div>
                <Link
                  href="/analysis"
                  className="px-3 py-2 text-xs sm:text-sm font-semibold text-emerald-400 border border-emerald-500/30 rounded-lg hover:bg-emerald-500/10 transition-all"
                >
                  Game Insights
                </Link>
              </div>

              <div className="mt-3">
                <BalanceStrip />
              </div>
            </div>
          </section>

          {/* Tabs */}
          <DashboardTabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

          {/* Content */}
          <section className="flex-1 overflow-hidden">
            <div className="container mx-auto px-3 sm:px-4 py-4 sm:py-6 h-full pb-20 sm:pb-6">
              {activeTab === "games" && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="h-full">
                  <UpcomingGamesTab sport={gamesSport} onSportChange={setGamesSport} />
                </motion.div>
              )}

              {activeTab === "ai-builder" && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="h-full overflow-y-auto pr-1"
                >
                  <ParlayBuilder />
                </motion.div>
              )}

              {activeTab === "custom-builder" && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="h-full overflow-y-auto pr-1"
                >
                  <CustomParlayBuilder prefillRequest={prefillRequest} />
                </motion.div>
              )}

              {activeTab === "analytics" && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="h-full overflow-y-auto pr-1"
                >
                  <Analytics />
                </motion.div>
              )}
            </div>
          </section>
        </main>
      </div>
    </ProtectedRoute>
  )
}


