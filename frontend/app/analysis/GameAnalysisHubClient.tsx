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

import { GameRow } from "@/components/games/GameRow"
import { SPORT_BACKGROUNDS, SPORT_NAMES } from "@/components/games/gamesConfig"
import { SportBackground } from "@/components/games/SportBackground"
import { addDays, formatDateString, formatDisplayDate, getTargetDate } from "@/components/games/gamesDateUtils"
import { useGamesForSportDate } from "@/components/games/useGamesForSportDate"
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

export default function GameAnalysisHubClient() {
  const [sport, setSport] = useState("nfl")
  const [date, setDate] = useState("today")
  const [hasRefreshed, setHasRefreshed] = useState(false)
  const [inSeasonBySport, setInSeasonBySport] = useState<Record<string, boolean>>({})

  const { user } = useAuth()
  const { isPremium } = useSubscription()
  const canViewWinProb = isPremium || !!user

  const { games, loading, refreshing, error, refresh } = useGamesForSportDate({ sport, date })

  // Fetch sports availability (in-season) so we can disable out-of-season tabs.
  useEffect(() => {
    let cancelled = false
    async function loadSportsStatus() {
      try {
        const sportsList = await api.listSports()
        if (cancelled) return
        const map: Record<string, boolean> = {}
        for (const s of sportsList) {
          map[s.slug] = s.in_season !== false
        }
        setInSeasonBySport(map)
      } catch {
        // Best-effort; default to enabled if backend status is unavailable.
        if (!cancelled) setInSeasonBySport({})
      }
    }
    loadSportsStatus()
    return () => {
      cancelled = true
    }
  }, [])

  // If the currently selected sport becomes out-of-season, fall back to the first in-season tab.
  useEffect(() => {
    if (!Object.keys(inSeasonBySport).length) return
    if (inSeasonBySport[sport] !== false) return
    const firstAvailable = SPORT_TABS.find((t) => inSeasonBySport[t.id] !== false)?.id
    if (firstAvailable && firstAvailable !== sport) setSport(firstAvailable)
  }, [inSeasonBySport, sport])

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

  // Filter out completed/finished games - only show scheduled or in-progress games
  const activeGames = useMemo(() => {
    const now = new Date()
    const maxHoursSinceStart = 8
    return games.filter((game) => {
      const gameTime = new Date(game.start_time)
      const gameStatus = game.status?.toLowerCase() || ""
      
      // Exclude finished/closed games
      if (gameStatus === "finished" || gameStatus === "closed" || gameStatus === "complete") {
        return false
      }
      
      // For games that have started, only show if they're very recent (within 2 hours)
      // This allows live games to show but filters out old completed games
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
                  const inSeason = inSeasonBySport[s.id] !== false
                  const disabled = !inSeason
                  return (
                    <button
                      key={s.id}
                      onClick={() => (disabled ? null : setSport(s.id))}
                      disabled={disabled}
                      role="tab"
                      aria-selected={active}
                      className={cn(
                        "shrink-0 inline-flex items-center px-4 py-2 rounded-lg text-sm font-semibold transition-all whitespace-nowrap",
                        active ? "bg-emerald-500 text-black" : "bg-white/5 text-gray-300 hover:bg-white/10",
                        disabled && "opacity-40 cursor-not-allowed hover:bg-white/5"
                      )}
                      title={disabled ? "Not in season" : undefined}
                    >
                      <span className="mr-2">{s.icon}</span>
                      {s.label}
                      {disabled ? (
                        <span className="ml-2 text-[10px] font-bold uppercase text-gray-400">Not in season</span>
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
              {loading ? (
                <div className="flex justify-center items-center py-20">
                  <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
                  <span className="ml-3 text-gray-400">Loading {sportName} games...</span>
                </div>
              ) : activeGames.length === 0 ? (
                <div className="text-center py-20">
                  <div className="text-gray-400 font-semibold mb-2">No active games found</div>
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


