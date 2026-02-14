"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { Calendar, ChevronLeft, ChevronRight, Loader2, RefreshCw } from "lucide-react"

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
import { addDays, formatDateString, formatDisplayDate, getTargetDate } from "@/components/games/gamesDateUtils"
import { useGamesForSportDate, type GamesListMeta } from "@/components/games/useGamesForSportDate"
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

export default function GameAnalysisHubClient() {
  const [sport, setSport] = useState("nfl")
  const [date, setDate] = useState("today")
  const [hasRefreshed, setHasRefreshed] = useState(false)
  const [availabilityBySport, setAvailabilityBySport] = useState<Record<string, SportAvailability>>({})

  const { user } = useAuth()
  const { isPremium } = useSubscription()
  const canViewWinProb = isPremium || !!user

  const { games, loading, refreshing, error, refresh, listMeta } = useGamesForSportDate({ sport, date })

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

  // Force refresh on mount and when sport/date changes to ensure fresh data
  useEffect(() => {
    // Reset refresh flag when sport or date changes
    setHasRefreshed(false)
    // Force refresh to get fresh data from API
    const timer = setTimeout(() => {
      refresh()
      setHasRefreshed(true)
    }, 100)
    return () => clearTimeout(timer)
  }, [sport, date]) // eslint-disable-line react-hooks/exhaustive-deps

  // Filter out completed/finished games - only show scheduled or in-progress games.
  // Keep started games visible for a full day to avoid empty slates when users open
  // the page later in the day.
  const activeGames = useMemo(() => {
    const now = new Date()
    const maxHoursSinceStart = 24
    return games.filter((game) => {
      const gameTime = new Date(game.start_time)
      const gameStatus = game.status?.toLowerCase() || ""
      
      // Exclude finished/closed games
      if (gameStatus === "finished" || gameStatus === "closed" || gameStatus === "complete") {
        return false
      }
      
      // For games that have started, keep them visible for a generous window.
      if (gameTime < now) {
        const hoursSinceStart = (now.getTime() - gameTime.getTime()) / (1000 * 60 * 60)
        return hoursSinceStart <= maxHoursSinceStart
      }
      
      // Show all future games
      return true
    })
  }, [games])

  const sportName = SPORT_NAMES[sport] || sport.toUpperCase()
  const backgroundImage = SPORT_BACKGROUNDS[sport] || "/images/nflll.png"

  const prevDate = useMemo(() => formatDateString(addDays(getTargetDate(date), -1)), [date])
  const nextDate = useMemo(() => formatDateString(addDays(getTargetDate(date), 1)), [date])
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
                  <div className="flex items-center gap-2 bg-white/5 rounded-lg p-1">
                    <button
                      className="p-2 rounded hover:bg-white/10 transition-colors"
                      onClick={() => setDate(prevDate)}
                      aria-label="Previous day"
                    >
                      <ChevronLeft className="h-4 w-4 text-gray-400" />
                    </button>
                    <div className="flex items-center gap-2 px-3 py-1.5">
                      <Calendar className="h-4 w-4 text-emerald-400" />
                      <span className="text-sm font-medium text-white">{formatDisplayDate(date)}</span>
                    </div>
                    <button
                      className="p-2 rounded hover:bg-white/10 transition-colors"
                      onClick={() => setDate(nextDate)}
                      aria-label="Next day"
                    >
                      <ChevronRight className="h-4 w-4 text-gray-400" />
                    </button>
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
              ) : activeGames.length === 0 ? (
                <div className="text-center py-20">
                  <div className="text-gray-400 font-semibold mb-2">No active games found</div>
                  {emptyStateLine ? <div className="text-sm text-gray-400 mb-2">{emptyStateLine}</div> : null}
                  {error ? <div className="text-sm text-gray-500">{error.message}</div> : null}
                  <div className="text-xs text-gray-500 mt-4">
                    {games.length > 0 ? (
                      <>Showing only upcoming and recent games. {games.length - activeGames.length} completed games filtered out.</>
                    ) : (
                      <>
                        Tip: If this is a new sport, open{" "}
                        <Link href="/sports" className="text-emerald-400 hover:underline">
                          Sports
                        </Link>{" "}
                        and try "Refresh".
                      </>
                    )}
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {activeGames.map((game, idx) => (
                    <GameRow
                      key={game.id}
                      sport={sport}
                      game={game}
                      index={idx}
                      canViewWinProb={canViewWinProb}
                      selectedMarket="all"
                      parlayLegs={new Set()} // analysis hub is "read-only" (no slip)
                      onToggleParlayLeg={() => {}}
                      showMarkets={false}
                    />
                  ))}
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


