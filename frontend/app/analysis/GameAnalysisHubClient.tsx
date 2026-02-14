"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { Loader2, RefreshCw } from "lucide-react"

import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import { cn } from "@/lib/utils"
import { useAuth } from "@/lib/auth-context"
import { useSubscription } from "@/lib/subscription-context"
import { api } from "@/lib/api"
import type { SportListItem } from "@/lib/api/types"
import { BalanceStrip } from "@/components/billing/BalanceStrip"

import { GameRow } from "@/components/games/GameRow"
import { SPORT_BACKGROUNDS, SPORT_NAMES } from "@/components/games/gamesConfig"
import { SportBackground } from "@/components/games/SportBackground"
import { useGamesForSportDate, type GamesListMeta } from "@/components/games/useGamesForSportDate"
import { normalizeGameStatus } from "@/components/games/gameStatusUtils"
import { PushNotificationsToggle } from "@/components/notifications/PushNotificationsToggle"
import { HorizontalScrollCue } from "@/components/ui/HorizontalScrollCue"

const SPORT_TABS: Array<{ id: string; label: string; icon: string }> = [
  { id: "nfl", label: "NFL", icon: "🏈" },
  { id: "nba", label: "NBA", icon: "🏀" },
  { id: "nhl", label: "NHL", icon: "🏒" },
  { id: "mlb", label: "MLB", icon: "⚾" },
  { id: "ncaaf", label: "NCAAF", icon: "🏈" },
  { id: "ncaab", label: "NCAAB", icon: "🏀" },
  { id: "epl", label: "Premier League", icon: "⚽" },
  { id: "mls", label: "MLS", icon: "⚽" },
]

export type SportAvailability = {
  isEnabled: boolean
  sportState?: string
  statusLabel?: string
  nextGameAt?: string | null
  daysToNext?: number | null
  preseasonEnableDays?: number | null
}

/** Normalize sport key for map lookups (slug/id). Prevents NCAAF vs ncaaf mismatches. */
export function sportKey(slugOrId: string): string {
  return (slugOrId || "").toLowerCase()
}

/** Build availability map from listSports response. Keys are normalized lowercase (slug). */
export function buildAvailabilityBySport(sportsList: SportListItem[]): Record<string, SportAvailability> {
  const map: Record<string, SportAvailability> = {}
  for (const s of sportsList) {
    const key = sportKey(s.slug)
    const isEnabled =
      typeof s.is_enabled === "boolean" ? s.is_enabled : (s.in_season !== false)
    map[key] = {
      isEnabled,
      sportState: s.sport_state,
      statusLabel: s.status_label,
      nextGameAt: s.next_game_at ?? null,
      daysToNext: typeof s.days_to_next === "number" ? s.days_to_next : null,
      preseasonEnableDays:
        typeof s.preseason_enable_days === "number" ? s.preseason_enable_days : null,
    }
  }
  return map
}

export function availabilityBadgeText(meta: SportAvailability | undefined): string {
  if (!meta || meta.isEnabled) return ""
  const state = (meta.sportState ?? "").toUpperCase()
  if (meta.daysToNext != null && meta.preseasonEnableDays != null && state === "PRESEASON" && meta.daysToNext > meta.preseasonEnableDays) {
    return `Unlocks in ${meta.daysToNext} days`
  }
  if (meta.nextGameAt && state === "OFFSEASON") {
    try {
      const d = new Date(meta.nextGameAt)
      if (!Number.isNaN(d.getTime())) return `Returns ${d.toLocaleDateString()}`
    } catch {
      /* ignore */
    }
  }
  switch (state) {
    case "OFFSEASON":
      return "Offseason"
    case "PRESEASON":
      return "Preseason"
    case "IN_BREAK":
      return "Break"
    case "POSTSEASON":
      return "Postseason"
    default:
      return meta.statusLabel ?? "Not in season"
  }
}

/** Context-aware empty-state line when there are no games (offseason / preseason / break). */
export function emptyStateContextLine(listMeta: GamesListMeta | null): string {
  if (!listMeta?.sport_state) return ""
  const state = (listMeta.sport_state ?? "").toUpperCase()
  const nextAt = listMeta.next_game_at
  const daysToNext = listMeta.days_to_next
  const preseasonDays = listMeta.preseason_enable_days
  let dateStr = ""
  if (nextAt) {
    try {
      const d = new Date(nextAt)
      if (!Number.isNaN(d.getTime())) dateStr = d.toLocaleDateString()
    } catch {
      /* ignore */
    }
  }
  if (state === "OFFSEASON" && dateStr) return `Out of season — returns ${dateStr}`
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
  const [sport, setSport] = useState("nfl")
  const [activeTab, setActiveTab] = useState<"UPCOMING" | "LIVE" | "FINAL">("UPCOMING")
  const [showAllGames, setShowAllGames] = useState(false)
  const [availabilityBySport, setAvailabilityBySport] = useState<Record<string, SportAvailability>>({})

  const { user } = useAuth()
  const { isPremium } = useSubscription()
  const canViewWinProb = isPremium || !!user

  const { games, loading, refreshing, error, refresh, listMeta } = useGamesForSportDate({ sport, date: "all" })

  // Fetch sports availability once on mount; use is_enabled (fallback in_season) to disable tabs.
  useEffect(() => {
    let cancelled = false
    async function loadSportsStatus() {
      try {
        const sportsList = await api.listSports()
        if (cancelled) return
        setAvailabilityBySport(buildAvailabilityBySport(sportsList))
      } catch {
        if (!cancelled) setAvailabilityBySport({})
      }
    }
    loadSportsStatus()
    return () => {
      cancelled = true
    }
  }, [])

  // If the currently selected sport becomes disabled, switch to first enabled tab.
  useEffect(() => {
    if (!Object.keys(availabilityBySport).length) return
    const sportKeyLower = sportKey(sport)
    if (availabilityBySport[sportKeyLower]?.isEnabled !== false) return
    const firstAvailable = SPORT_TABS.find(
      (t) => availabilityBySport[sportKey(t.id)]?.isEnabled !== false
    )?.id
    if (firstAvailable && firstAvailable !== sport) setSport(firstAvailable)
  }, [availabilityBySport, sport])

  // Refresh when sport changes
  useEffect(() => {
    const t = setTimeout(() => refresh(), 50)
    return () => clearTimeout(t)
  }, [sport]) // eslint-disable-line react-hooks/exhaustive-deps

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

  const sportName = SPORT_NAMES[sport] || sport.toUpperCase()
  const backgroundImage = SPORT_BACKGROUNDS[sport] || "/images/nflll.png"
  const emptyStateLine = useMemo(() => emptyStateContextLine(listMeta), [listMeta])

  return (
    <div className="min-h-screen flex flex-col relative">
      <SportBackground imageUrl={backgroundImage} overlay="medium" />

      <div className="relative z-10 min-h-screen flex flex-col">
        <Header />

        <main className="flex-1">
          {/* Minimal header */}
          <section className="py-8 border-b border-white/10 bg-black/40 backdrop-blur-sm">
            <div className="container mx-auto px-4">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <h1 className="text-3xl md:text-4xl font-black">
                    <span className="text-white">Game </span>
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
                      Analysis
                    </span>
                  </h1>
                  <p className="text-sm text-gray-400 mt-1">Pick a matchup and open the full AI breakdown.</p>
                </div>

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
              </div>

              {/* Sport tabs */}
              <HorizontalScrollCue
                className="mt-6"
                scrollContainerClassName="flex flex-nowrap items-center gap-2"
                scrollContainerProps={{ role: "tablist", "aria-label": "Sports" }}
              >
                {SPORT_TABS.map((s) => {
                  const active = sport === s.id
                  const key = sportKey(s.id)
                  const meta = availabilityBySport[key]
                  const enabled = meta ? meta.isEnabled : true
                  const disabled = !enabled
                  const badgeText = availabilityBadgeText(meta)
                  return (
                    <button
                      key={s.id}
                      onClick={() => (disabled ? undefined : setSport(s.id))}
                      disabled={disabled}
                      role="tab"
                      aria-selected={active}
                      className={cn(
                        "shrink-0 inline-flex items-center px-4 py-2 rounded-lg text-sm font-semibold transition-all whitespace-nowrap",
                        active ? "bg-emerald-500 text-black" : "bg-white/5 text-gray-300 hover:bg-white/10",
                        disabled && "opacity-40 cursor-not-allowed hover:bg-white/5"
                      )}
                      title={disabled ? badgeText || "Not in season" : undefined}
                    >
                      <span className="mr-2">{s.icon}</span>
                      {s.label}
                      {disabled && badgeText ? (
                        <span className="ml-2 text-[10px] font-bold uppercase text-gray-400">{badgeText}</span>
                      ) : null}
                    </button>
                  )
                })}
              </HorizontalScrollCue>

              {/* Sport info */}
              <div className="mt-4">
                <div className="text-xs text-gray-500">
                  Viewing: <span className="text-gray-300 font-medium">{sportName}</span>
                </div>
              </div>
            </div>
          </section>

          {/* Games list */}
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
                  <div className="text-gray-400 font-semibold mb-2">Couldn&apos;t reach the backend. Try refresh.</div>
                  <div className="text-sm text-gray-500">{error.message}</div>
                </div>
              ) : displayedGames.length === 0 ? (
                <div className="text-center py-20">
                  {activeTab === "UPCOMING" && (
                    <>
                      <div className="text-gray-400 font-semibold mb-2">No upcoming games scheduled.</div>
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
                      <div className="text-sm text-gray-400">Check Upcoming for scheduled games.</div>
                    </>
                  )}
                  {activeTab === "FINAL" && (
                    <>
                      <div className="text-gray-400 font-semibold mb-2">No completed games for this sport.</div>
                      <div className="text-sm text-gray-400">Try Yesterday or another tab.</div>
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
        </main>

        <Footer />
      </div>
    </div>
  )
}


