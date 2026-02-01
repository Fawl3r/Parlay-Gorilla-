"use client"

import { useEffect, useMemo, useState } from "react"
import { BarChart3, Calendar, Target, Trophy, Zap, Map, AlertTriangle } from "lucide-react"
import { motion } from "framer-motion"
import { useSearchParams } from "next/navigation"

import { DashboardLayout } from "@/components/layout/DashboardLayout"
import { AnimatedBackground } from "@/components/AnimatedBackground"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { Analytics } from "@/components/Analytics"
import { ParlayBuilder } from "@/components/ParlayBuilder"
import { CustomParlayBuilder } from "@/components/CustomParlayBuilder"
import { DashboardAccountCommandCenter } from "@/components/usage/DashboardAccountCommandCenter"
import { BalanceStrip } from "@/components/billing/BalanceStrip"
import { SportBackground } from "@/components/games/SportBackground"
import { SPORT_BACKGROUNDS, type SportSlug } from "@/components/games/gamesConfig"

import { DashboardTabs, type TabType } from "@/app/app/_components/DashboardTabs"
import { UpcomingGamesTab } from "@/app/app/_components/tabs/UpcomingGamesTab"
import { FeedTab } from "@/app/app/_components/tabs/FeedTab"
import { OddsHeatmapTab } from "@/app/app/_components/tabs/OddsHeatmapTab"
import { UpsetFinderTab } from "@/app/app/_components/tabs/UpsetFinderTab"
import { LiveMarquee } from "@/components/feed/LiveMarquee"

export default function AppDashboardClient() {
  const searchParams = useSearchParams()
  const [activeTab, setActiveTab] = useState<TabType>("games")
  const [gamesSport, setGamesSport] = useState<SportSlug>("nfl")

  // #region agent log
  useEffect(() => {
    try {
      fetch('http://127.0.0.1:7242/ingest/abd8edf1-767f-4ebd-9040-91726939b7d4', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId: 'debug-session',
          runId: 'run1',
          hypothesisId: 'F',
          location: 'AppDashboardClient.tsx:22',
          message: 'Dashboard loaded',
          data: { initialTab: activeTab, sport: gamesSport },
          timestamp: Date.now()
        })
      }).catch(() => {})
    } catch {}
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  // #endregion

  const tabParam = String(searchParams.get("tab") || "")
  useEffect(() => {
    const next = tabParam as TabType
    if (next === "games" || next === "ai-builder" || next === "custom-builder" || next === "analytics" || next === "feed" || next === "odds-heatmap" || next === "upset-finder") {
      setActiveTab(next)
      // #region agent log
      try {
        fetch('http://127.0.0.1:7242/ingest/abd8edf1-767f-4ebd-9040-91726939b7d4', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sessionId: 'debug-session',
            runId: 'run1',
            hypothesisId: 'F',
            location: 'AppDashboardClient.tsx:30',
            message: 'Tab changed from URL param',
            data: { tab: next },
            timestamp: Date.now()
          })
        }).catch(() => {})
      } catch {}
      // #endregion
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
      { id: "ai-builder" as const, label: "AI Picks", icon: Zap },
      { id: "custom-builder" as const, label: "Gorilla Parlay Builder", icon: Target },
      { id: "analytics" as const, label: "Insights", icon: BarChart3 },
      { id: "odds-heatmap" as const, label: "Odds Heatmap", icon: Map },
      { id: "upset-finder" as const, label: "Upset Finder", icon: AlertTriangle },
      { id: "feed" as const, label: "Win Wall", icon: Trophy },
    ],
    []
  )

  const gamesBackgroundImage = SPORT_BACKGROUNDS[gamesSport] || "/images/nflll.png"

  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="min-h-screen flex flex-col relative" style={{ backgroundColor: "#0a0a0f" }}>
          <AnimatedBackground variant="intense" />
          {activeTab === "games" && <SportBackground imageUrl={gamesBackgroundImage} overlay="light" className="bg-transparent" />}

          <div className="flex-1 relative z-10 flex flex-col">
          {/* Live Marquee - At the very top (mobile: sticky band under nav) */}
          <LiveMarquee variant="mobile" />

          <section className="border-b border-white/10 bg-black/40 backdrop-blur-md">
            <div className="w-full px-2 sm:container sm:mx-auto sm:px-4 py-2 sm:py-4 md:py-5">
              <div className="mb-2 sm:mb-4 rounded-xl border border-white/10 bg-black/25 backdrop-blur-sm p-1.5 sm:p-2">
                <BalanceStrip compact />
              </div>
              <DashboardAccountCommandCenter />
            </div>
          </section>

          {/* Tabs */}
          <DashboardTabs tabs={tabs} activeTab={activeTab} onChange={(tab) => {
            // #region agent log
            try {
              fetch('http://127.0.0.1:7242/ingest/abd8edf1-767f-4ebd-9040-91726939b7d4', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  sessionId: 'debug-session',
                  runId: 'run1',
                  hypothesisId: 'F',
                  location: 'AppDashboardClient.tsx:82',
                  message: 'Tab changed by user',
                  data: { fromTab: activeTab, toTab: tab },
                  timestamp: Date.now()
                })
              }).catch(() => {})
            } catch {}
            // #endregion
            setActiveTab(tab)
          }} />

          {/* Content */}
          <section className="flex-1">
            <div className="w-full px-2 sm:container sm:mx-auto sm:px-3 md:px-4 py-3 sm:py-4 md:py-6 pb-24 sm:pb-6 md:pb-6">
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

              {activeTab === "odds-heatmap" && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="h-full overflow-y-auto pr-1"
                >
                  <OddsHeatmapTab />
                </motion.div>
              )}

              {activeTab === "upset-finder" && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="h-full overflow-y-auto pr-1"
                >
                  <UpsetFinderTab />
                </motion.div>
              )}

              {activeTab === "feed" && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="h-full overflow-y-auto pr-1"
                >
                  <FeedTab />
                </motion.div>
              )}
            </div>
          </section>
          </div>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}


