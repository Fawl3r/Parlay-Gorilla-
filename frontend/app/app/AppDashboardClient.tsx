"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { BarChart3, Calendar, Target, Trophy, Zap, Map, AlertTriangle } from "lucide-react"
import { recordReturnVisit, recordBuilderInteraction } from "@/lib/monetization-timing"
import { motion } from "framer-motion"
import { useSearchParams, useRouter, usePathname } from "next/navigation"

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
import { DashboardRetentionStrip } from "@/app/app/_components/DashboardRetentionStrip"
import { MarketSnapshotCard } from "@/app/app/_components/MarketSnapshotCard"
import { UpcomingGamesTab } from "@/app/app/_components/tabs/UpcomingGamesTab"
import { useSportsAvailability } from "@/lib/sports/useSportsAvailability"
import { FeedTab } from "@/app/app/_components/tabs/FeedTab"
import { OddsHeatmapTab } from "@/app/app/_components/tabs/OddsHeatmapTab"
import { UpsetFinderTab } from "@/app/app/_components/tabs/UpsetFinderTab"
import { LiveMarquee } from "@/components/feed/LiveMarquee"
import { PwaInstallCta } from "@/components/pwa/PwaInstallCta"

/** URL param value for Performance Rankings tab (shareable /app?tab=leaderboards) */
const TAB_PARAM_LEADERBOARDS = "leaderboards"

/** Map tab id to URL param (feed -> leaderboards for shareability) */
function tabIdToParam(tabId: TabType): string {
  return tabId === "feed" ? TAB_PARAM_LEADERBOARDS : tabId
}

/** Map URL param to tab id; invalid params return null */
function paramToTabId(param: string): TabType | null {
  if (param === TAB_PARAM_LEADERBOARDS) return "feed"
  const allowed: TabType[] = ["games", "ai-builder", "custom-builder", "analytics", "feed", "odds-heatmap", "upset-finder"]
  return allowed.includes(param as TabType) ? (param as TabType) : null
}

export default function AppDashboardClient() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()
  const [activeTab, setActiveTab] = useState<TabType>("games")
  const [gamesSport, setGamesSport] = useState<SportSlug>("nfl")
  const builderRecordedRef = useRef(false)
  const { sports, isLoading: sportsLoading, isSportInSeason, normalizeSlug } = useSportsAvailability()

  // Default games tab to first in-season sport when NFL is offseason (avoid defaulting to NFL when inactive).
  useEffect(() => {
    if (sportsLoading || sports.length === 0) return
    if (gamesSport !== "nfl") return
    if (isSportInSeason("nfl")) return
    const firstInSeason = sports.find((s) => isSportInSeason(s.slug))
    if (firstInSeason) {
      const slug = normalizeSlug(firstInSeason.slug) as SportSlug
      if (slug) setGamesSport(slug)
    }
  }, [sportsLoading, sports, gamesSport, isSportInSeason, normalizeSlug])

  useEffect(() => {
    recordReturnVisit()
  }, [])

  useEffect(() => {
    if (activeTab === "custom-builder" && !builderRecordedRef.current) {
      builderRecordedRef.current = true
      recordBuilderInteraction()
    }
  }, [activeTab])

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
    const next = paramToTabId(tabParam)
    if (next != null) {
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
      { id: "ai-builder" as const, label: "AI Selections", icon: Zap },
      { id: "custom-builder" as const, label: "Strategy Builder", icon: Target },
      { id: "analytics" as const, label: "Insights", icon: BarChart3 },
      { id: "odds-heatmap" as const, label: "Odds Heatmap", icon: Map },
      { id: "upset-finder" as const, label: "Upset Finder", icon: AlertTriangle },
      { id: "feed" as const, label: "Performance Rankings", icon: Trophy },
    ],
    []
  )

  const gamesBackgroundImage = SPORT_BACKGROUNDS[gamesSport] || "/images/nflll.png"

  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="min-h-screen flex flex-col relative" style={{ backgroundColor: "#0b0b0b" }}>
          <AnimatedBackground variant="intense" />
          {/* Dark overlay so content sits on darker ground for readability */}
          <div className="fixed inset-0 pointer-events-none z-[1]" aria-hidden style={{ background: "linear-gradient(180deg, rgba(14,14,14,0.55) 0%, rgba(14,14,14,0.7) 50%, rgba(14,14,14,0.78) 100%)" }} />
          {activeTab === "games" && <SportBackground imageUrl={gamesBackgroundImage} overlay="light" className="bg-transparent" />}

          <div className="flex-1 relative z-10 flex flex-col">
          {/* Live Marquee - At the very top (mobile: sticky band under nav) */}
          <LiveMarquee variant="mobile" />

          <div className="w-full px-2 sm:container sm:mx-auto sm:px-4 py-1.5 sm:py-2">
            <PwaInstallCta variant="inline" context="dashboard" />
          </div>

          <section className="border-b border-white/10 bg-black/40 backdrop-blur-md">
            <div className="w-full px-2 sm:container sm:mx-auto sm:px-4 py-2 sm:py-4 md:py-5">
              <div className="mb-2 sm:mb-4 rounded-xl border border-white/10 bg-black/25 backdrop-blur-sm p-1.5 sm:p-2">
                <BalanceStrip compact />
              </div>
              <DashboardRetentionStrip />
              <MarketSnapshotCard />
              <DashboardAccountCommandCenter />
            </div>
          </section>

          {/* Tabs */}
          <DashboardTabs
            tabs={tabs}
            activeTab={activeTab}
            onChange={(tab) => {
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
              const param = tabIdToParam(tab)
              const next = new URLSearchParams(searchParams.toString())
              next.set("tab", param)
              router.replace(`${pathname}?${next.toString()}`, { scroll: false })
            }}
          />

          {/* Content */}
          <section className="flex-1">
            <div className="w-full px-2 sm:container sm:mx-auto sm:px-3 md:px-4 py-3 sm:py-4 md:py-6 pb-24 sm:pb-6 md:pb-6">
              {activeTab === "games" && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="h-full overflow-y-auto pr-1"
                  data-page="games"
                >
                  <UpcomingGamesTab sport={gamesSport} onSportChange={setGamesSport} />
                </motion.div>
              )}

              {activeTab === "ai-builder" && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="h-full overflow-y-auto pr-1"
                  data-page="ai-builder"
                >
                  <ParlayBuilder />
                </motion.div>
              )}

              {activeTab === "custom-builder" && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="h-full overflow-y-auto pr-1"
                  data-page="custom-builder"
                >
                  <CustomParlayBuilder prefillRequest={prefillRequest} />
                </motion.div>
              )}

              {activeTab === "analytics" && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="h-full overflow-y-auto pr-1"
                  data-page="analytics"
                >
                  <Analytics />
                </motion.div>
              )}

              {activeTab === "odds-heatmap" && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="h-full overflow-y-auto pr-1"
                  data-page="odds-heatmap"
                >
                  <OddsHeatmapTab />
                </motion.div>
              )}

              {activeTab === "upset-finder" && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="h-full overflow-y-auto pr-1"
                  data-page="upset-finder"
                >
                  <UpsetFinderTab />
                </motion.div>
              )}

              {activeTab === "feed" && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="h-full overflow-y-auto pr-1"
                  data-page="feed"
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


