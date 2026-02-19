"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { Filter, Loader2, RefreshCw } from "lucide-react"

import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import { cn } from "@/lib/utils"
import { useAuth } from "@/lib/auth-context"
import { useSubscription } from "@/lib/subscription-context"
import { BalanceStrip } from "@/components/billing/BalanceStrip"

import { GameRow } from "@/components/games/GameRow"
import { SPORT_BACKGROUNDS, SPORT_NAMES, SPORT_ICONS } from "@/components/games/gamesConfig"
import { SportBackground } from "@/components/games/SportBackground"
import { useGamesForSportDate, type GamesListMeta } from "@/components/games/useGamesForSportDate"
import { normalizeGameStatus } from "@/components/games/gameStatusUtils"
import { PushNotificationsToggle } from "@/components/notifications/PushNotificationsToggle"
import { HorizontalScrollCue } from "@/components/ui/HorizontalScrollCue"
import { useSportsAvailability } from "@/lib/sports/useSportsAvailability"
import { recordVisit } from "@/lib/retention"
import { GameAnalysisHowItWorks } from "@/app/analysis/_components/GameAnalysisHowItWorks"

/** Normalize sport key for map lookups (slug/id). */
export function sportKey(slugOrId: string): string {
  return (slugOrId || "").toLowerCase()
}

/** Context-aware empty-state line when there are no games (offseason / preseason / break). */
export function emptyStateContextLine(listMeta: GamesListMeta | null, sportSlug?: string): string {
  if (!listMeta?.sport_state) return ""
  const state = (listMeta.sport_state ?? "").toUpperCase()
  const nextAt = listMeta.next_game_at
  const daysToNext = listMeta.days_to_next
  const preseasonDays = listMeta.preseason_enable_days
  const slug = (sportSlug ?? "").toLowerCase()
  let dateStr = ""
  if (nextAt) {
    try {
      const d = new Date(nextAt)
      if (!Number.isNaN(d.getTime())) dateStr = d.toLocaleDateString()
    } catch {
      /* ignore */
    }
  }
  if (state === "OFFSEASON") {
    if (slug === "wnba") return "WNBA is offseason — check back soon."
    if (dateStr) return `Out of season — returns ${dateStr}`
  }
  if (state === "PRESEASON") {
    if (typeof daysToNext === "number" && typeof preseasonDays === "number" && daysToNext > preseasonDays && dateStr) {
      return `Preseason starts ${dateStr} — unlocks in ${daysToNext} days`
    }
    if (dateStr) return `Preseason — next game ${dateStr}`
  }
  if (state === "IN_BREAK" && dateStr) return `League break — next game ${dateStr}`
  return ""
}

const GAME_TABS: Array<{ id: "UPCOMING" | "LIVE" | "FINAL"; label: string }> = [
  { id: "UPCOMING", label: "Upcoming" },
  { id: "LIVE", label: "Live" },
  { id: "FINAL", label: "Final" },
]

const DISPLAY_CAP = 50

export default function GameAnalysisHubClient() {
  const [sport, setSport] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<"UPCOMING" | "LIVE" | "FINAL">("UPCOMING")
  const [showAllGames, setShowAllGames] = useState(false)
  const [showInSeasonOnly, setShowInSeasonOnly] = useState(false)

  const { user } = useAuth()
  const { isPremium } = useSubscription()
  const canViewWinProb = isPremium || !!user

  const {
    sports,
    inSeasonSports,
    isLoading: sportsLoading,
    error: sportsError,
    isStale: sportsStale,
    isSportEnabled,
    getSportBadge,
    normalizeSlug,
  } = useSportsAvailability()
  const effectiveSport = sport ?? "nfl"
  const { games, loading, refreshing, error, refresh, listMeta } = useGamesForSportDate({ sport: effectiveSport, date: "all" })

  // Once sports list has loaded, set initial sport to first enabled (avoids showing NFL before list is ready).
  useEffect(() => {
    if (sportsLoading || sports.length === 0) return
    if (sport !== null) return
    const firstEnabled = sports.find((s) => isSportEnabled(s.slug))
    const slug = firstEnabled ? normalizeSlug(firstEnabled.slug) : normalizeSlug(sports[0]?.slug ?? "nfl")
    if (slug) setSport(slug)
  }, [sportsLoading, sports, sport, isSportEnabled, normalizeSlug])

  // If the currently selected sport becomes disabled, switch to first enabled sport.
  useEffect(() => {
    if (sport === null || sports.length === 0) return
    if (isSportEnabled(sport)) return
    const firstEnabled = sports.find((s) => isSportEnabled(s.slug))
    if (firstEnabled) {
      const slug = normalizeSlug(firstEnabled.slug)
      if (slug && slug !== normalizeSlug(sport)) setSport(slug)
    }
  }, [sports, sport, isSportEnabled, normalizeSlug])

  // Retention: count visit to analysis hub
  useEffect(() => {
    recordVisit()
  }, [])

  // Refresh when sport changes (only once we have a resolved sport)
  useEffect(() => {
    if (sport === null) return
    const t = setTimeout(() => refresh(), 50)
    return () => clearTimeout(t)
  }, [sport, refresh])

  // Poll every 60s only when Live tab is active and page visible
  useEffect(() => {
    if (activeTab !== "LIVE") return
    const interval = setInterval(() => {
      if (typeof document !== "undefined" && document.visibilityState === "visible") refresh()
    }, 60_000)
    return () => clearInterval(interval)
  }, [activeTab, refresh])

  const upcomingGames = useMemo(() => {
    return games
      .filter((g) => normalizeGameStatus(g.status ?? "", g.start_time) === "UPCOMING")
      .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
  }, [games])
  const liveGames = useMemo(() => {
    return games
      .filter((g) => normalizeGameStatus(g.status ?? "", g.start_time) === "LIVE")
      .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
  }, [games])
  const finalGames = useMemo(() => {
    return games
      .filter((g) => normalizeGameStatus(g.status ?? "", g.start_time) === "FINAL")
      .sort((a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime())
  }, [games])

  const tabGames = useMemo(() => {
    switch (activeTab) {
      case "UPCOMING":
        return upcomingGames
      case "LIVE":
        return liveGames
      case "FINAL":
        return finalGames
      default:
        return upcomingGames
    }
  }, [activeTab, upcomingGames, liveGames, finalGames])

  const displayedGames = useMemo(() => {
    if (showAllGames) return tabGames
    return tabGames.slice(0, DISPLAY_CAP)
  }, [tabGames, showAllGames])
  const hasMore = tabGames.length > DISPLAY_CAP

  const sportName = SPORT_NAMES[effectiveSport] || effectiveSport.toUpperCase()
  const backgroundImage = SPORT_BACKGROUNDS[effectiveSport] || "/images/nflll.png"
  const emptyStateLine = useMemo(() => emptyStateContextLine(listMeta, effectiveSport), [listMeta, effectiveSport])

  const showExplainer = sportsLoading || sport === null
  const sportsForTabs = showInSeasonOnly ? inSeasonSports : sports

  return (
    <div className="min-h-screen flex flex-col relative">
      <SportBackground imageUrl={backgroundImage} overlay="medium" />

      <div className="relative z-10 min-h-screen flex flex-col">
        <Header />

        <main className="flex-1">
          {/* Minimal header — always show */}
          <section className="py-8 border-b border-white/10 bg-black/40 backdrop-blur-sm">
            <div className="container mx-auto px-4">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <h1 className="text-3xl md:text-4xl font-black">
                    <span className="text-white">Matchup </span>
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
                      Intelligence
                    </span>
                  </h1>
                  <p className="text-sm text-gray-400 mt-1">
                    {showExplainer ? "How it works and what to expect." : "Select a matchup for the full analytical breakdown."}
                  </p>
                </div>

                {!showExplainer && (
                  <div className="flex items-center gap-3">
                    <div
                      className="flex rounded-lg bg-white/5 p-1 border border-white/10"
                      role="tablist"
                      aria-label="Game list"
                    >
                      {GAME_TABS.map((tab) => (
                        <button
                          key={tab.id}
                          role="tab"
                          aria-selected={activeTab === tab.id}
                          onClick={() => {
                            setActiveTab(tab.id)
                            setShowAllGames(false)
                          }}
                          className={cn(
                            "px-4 py-2 rounded-md text-sm font-semibold transition-all",
                            activeTab === tab.id ? "bg-emerald-500 text-black" : "text-gray-400 hover:text-white hover:bg-white/10"
                          )}
                        >
                          {tab.label}
                        </button>
                      ))}
                    </div>

                    <button
                      onClick={refresh}
                      disabled={refreshing}
                      className="px-3 py-2 rounded-lg border border-white/10 bg-white/5 text-gray-300 hover:bg-white/10 transition-all text-sm font-semibold disabled:opacity-50"
                    >
                      <RefreshCw className={cn("h-4 w-4 inline mr-2", refreshing && "animate-spin")} />
                      Refresh
                    </button>

                    <PushNotificationsToggle />
                  </div>
                )}
              </div>

              {/* While sports are loading, show explainer instead of sport tabs and games */}
              {showExplainer && <GameAnalysisHowItWorks />}

              {/* Sport tabs — from backend; only when list is ready */}
              {!showExplainer && sportsError && (
                <div className="mt-6 text-center py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-medium">
                  Couldn&apos;t reach backend. Try refresh.
                  {sportsStale && (
                    <div className="text-xs mt-1 text-gray-400">
                      Showing last saved sports list. <span className="text-[10px] uppercase tracking-wide text-gray-500" aria-label="Stale data">Stale data</span>
                    </div>
                  )}
                </div>
              )}
              {!showExplainer && (
                <div className="mt-6 mb-1 flex items-center justify-between text-xs text-gray-400">
                  <span className="uppercase tracking-wide text-gray-500">Sports</span>
                  <button
                    type="button"
                    onClick={() => setShowInSeasonOnly((v) => !v)}
                    className={cn(
                      "inline-flex items-center gap-1 rounded-full border px-3 py-1 text-[11px] font-medium transition-colors",
                      showInSeasonOnly
                        ? "border-emerald-400 text-emerald-300 bg-emerald-500/10"
                        : "border-white/10 text-gray-400 hover:bg-white/10"
                    )}
                  >
                    <Filter className="h-3 w-3" />
                    {showInSeasonOnly ? "In-season only" : "All sports"}
                  </button>
                </div>
              )}
              {!showExplainer && sportsForTabs.length > 0 && (
                <HorizontalScrollCue
                  className="mt-2"
                  scrollContainerClassName="flex flex-nowrap items-center gap-2"
                  scrollContainerProps={{ role: "tablist", "aria-label": "Sports" }}
                >
                  {sportsForTabs.map((s) => {
                    const slug = normalizeSlug(s.slug)
                    const active = sport === slug
                    const enabled = isSportEnabled(slug)
                    const disabled = !enabled
                    const badgeText = getSportBadge(slug)
                    const label = s.display_name || SPORT_NAMES[slug] || slug.toUpperCase()
                    const icon = SPORT_ICONS[slug] ?? "•"
                    return (
                      <button
                        key={slug}
                        onClick={() => (disabled ? undefined : setSport(slug))}
                        disabled={disabled}
                        aria-disabled={disabled}
                        role="tab"
                        aria-selected={active}
                        className={cn(
                          "shrink-0 inline-flex flex-col items-center px-4 py-2 rounded-lg text-sm font-semibold transition-all text-center",
                          active ? "bg-emerald-500 text-black" : "bg-white/5 text-gray-300 hover:bg-white/10",
                          disabled && "opacity-40 cursor-not-allowed hover:bg-white/5"
                        )}
                        title={disabled ? badgeText || "Not in season" : undefined}
                      >
                        <span className="flex items-center gap-2">
                          <span>{icon}</span>
                          <span className="whitespace-nowrap">{label}</span>
                        </span>
                        {disabled && badgeText ? (
                          <span className="mt-1 text-[10px] font-bold uppercase text-gray-400 leading-tight">{badgeText}</span>
                        ) : null}
                      </button>
                    )
                  })}
                </HorizontalScrollCue>
              )}

              {/* Sport info */}
              <div className="mt-4">
                <div className="text-xs text-gray-500">
                  Viewing: <span className="text-gray-300 font-medium">{sportName}</span>
                </div>
              </div>
            </div>
          </section>

          {/* Games list — only when sports are loaded and sport is resolved */}
          {!showExplainer && (
          <section className="py-8">
            <div className="container mx-auto px-4">
              <div className="md:hidden sticky top-16 z-40 mb-4 rounded-xl border border-white/10 bg-black/40 backdrop-blur-sm p-2">
                <BalanceStrip compact />
              </div>
              {loading ? (
                <div className="flex justify-center items-center py-20">
                  <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
                  <span className="ml-3 text-gray-400">Loading {sportName} games...</span>
                </div>
              ) : error ? (
                <div className="text-center py-20">
                  <div className="text-gray-400 font-semibold mb-2">Couldn&apos;t load games. Try refresh.</div>
                  <div className="text-sm text-gray-500">{error.message}</div>
                </div>
              ) : displayedGames.length === 0 ? (
                <div className="text-center py-20">
                  {activeTab === "UPCOMING" && (
                    <>
                      <div className="text-gray-400 font-semibold mb-2">
                        No active matchups today.
                      </div>
                      <div className="text-sm text-gray-400 mb-2">
                        AI continues monitoring league trends.
                      </div>
                      {listMeta?.sport_state === "OFFSEASON" && (
                        <div className="text-sm text-emerald-400/90 mb-2">
                          {sportName} Offseason Tracking Active — Historical trends still monitored.
                        </div>
                      )}
                      {listMeta?.next_game_at && (
                        <div className="text-sm text-gray-400 mb-2">
                          Next game: {new Date(listMeta.next_game_at).toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" })}
                        </div>
                      )}
                      {emptyStateLine ? <div className="text-sm text-gray-400 mb-2">{emptyStateLine}</div> : null}
                    </>
                  )}
                  {activeTab === "LIVE" && (
                    <>
                      <div className="text-gray-400 font-semibold mb-2">No live games right now.</div>
                      <div className="text-sm text-gray-400">AI continues monitoring. Check Upcoming for scheduled games.</div>
                    </>
                  )}
                  {activeTab === "FINAL" && (
                    <>
                      <div className="text-gray-400 font-semibold mb-2">No completed games for this sport.</div>
                      <div className="text-sm text-gray-400">Try another tab or sport. AI continues monitoring trends.</div>
                    </>
                  )}
                  <div className="text-xs text-gray-500 mt-4">
                    <Link href="/sports" className="text-emerald-400 hover:underline">Sports</Link> — try another sport or refresh.
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {displayedGames.map((game, idx) => (
                    <GameRow
                      key={game.id}
                      sport={sport}
                      game={game}
                      index={idx}
                      canViewWinProb={canViewWinProb}
                      selectedMarket="all"
                      parlayLegs={new Set()}
                      onToggleParlayLeg={() => {}}
                      showMarkets={false}
                    />
                  ))}
                  {hasMore && !showAllGames && (
                    <div className="flex justify-center pt-4">
                      <button
                        onClick={() => setShowAllGames(true)}
                        className="px-4 py-2 rounded-lg border border-white/20 text-sm font-medium text-gray-300 hover:bg-white/10"
                      >
                        Show more ({tabGames.length - DISPLAY_CAP} more)
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </section>
          )}
        </main>

        <Footer />
      </div>
    </div>
  )
}


