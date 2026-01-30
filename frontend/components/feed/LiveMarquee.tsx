"use client"

import { useEffect, useState, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { api, GameFeedResponse } from "@/lib/api"
import {
  getWindowType,
  getCategoryLabel,
  getLeagueLabel,
  formatUpcomingMeta,
  formatUpdatedAgo,
} from "@/lib/games/GameFeedDisplayManager"

interface MarqueeItem {
  id: string
  type: "live" | "final" | "upcoming"
  displayText: string
  upcomingMeta: string
  categoryLabel: string
  leagueLabel: string
  game: GameFeedResponse
}

const CAP = 10

function buildCombinedFeed(
  live: GameFeedResponse[],
  today: GameFeedResponse[],
  upcoming: GameFeedResponse[]
): GameFeedResponse[] {
  const finalsFromToday = today.filter((g) => getWindowType(g.status) === "final")
  const seen = new Set<string>()
  const combined: GameFeedResponse[] = []

  const addUpToCap = (list: GameFeedResponse[]) => {
    for (const g of list) {
      if (combined.length >= CAP) break
      if (!seen.has(g.id)) {
        seen.add(g.id)
        combined.push(g)
      }
    }
  }

  const liveSorted = [...live].sort(
    (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
  )
  const finalSorted = [...finalsFromToday].sort(
    (a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime()
  )
  const upcomingSorted = [...upcoming].sort(
    (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
  )

  addUpToCap(liveSorted)
  addUpToCap(finalSorted)
  addUpToCap(upcomingSorted)

  return combined
}

function formatGameForMarquee(game: GameFeedResponse, now: Date): MarqueeItem {
  const type = getWindowType(game.status)
  const categoryLabel = getCategoryLabel(game.sport)
  const leagueLabel = getLeagueLabel(game.sport)
  const matchup = `${game.away_team} @ ${game.home_team}`

  let displayText = ""
  let upcomingMeta = ""

  if (type === "live") {
    const hasScores = game.home_score !== null && game.away_score !== null
    const scorePart = hasScores ? ` | ${game.away_score}-${game.home_score}` : ""
    const periodPart = game.period ? ` | ${game.period}${game.clock ? ` ${game.clock}` : ""}` : ""
    displayText = `LIVE: ${matchup}${scorePart}${periodPart}`
  } else if (type === "final") {
    const hasScores = game.home_score !== null && game.away_score !== null
    const scorePart = hasScores ? ` | ${game.away_score}-${game.home_score}` : ""
    displayText = `FINAL: ${matchup}${scorePart}`
  } else {
    displayText = matchup
    upcomingMeta = formatUpcomingMeta(game.start_time, now)
  }

  return {
    id: game.id,
    type,
    displayText,
    upcomingMeta,
    categoryLabel,
    leagueLabel,
    game,
  }
}

export function LiveMarquee() {
  const [items, setItems] = useState<MarqueeItem[]>([])
  const [lastGoodItems, setLastGoodItems] = useState<MarqueeItem[]>([])
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null)
  const [isStale, setIsStale] = useState(false)
  const [nowTick, setNowTick] = useState(() => new Date())
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isPaused, setIsPaused] = useState(false)
  const [loading, setLoading] = useState(true)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const hasLoadedOnce = useRef(false)

  useEffect(() => {
    const fetchGames = async () => {
      try {
        if (!hasLoadedOnce.current) setLoading(true)
        const [liveGames, todayGames, upcomingGames] = await Promise.all([
          api.getGameFeed(undefined, "live").catch(() => [] as GameFeedResponse[]),
          api.getGameFeed(undefined, "today").catch(() => [] as GameFeedResponse[]),
          api.getGameFeed(undefined, "upcoming").catch(() => [] as GameFeedResponse[]),
        ])

        const now = new Date()
        const combined = buildCombinedFeed(liveGames, todayGames, upcomingGames)
        const marqueeItems = combined.map((g) => formatGameForMarquee(g, now))

        setItems(marqueeItems)
        setLastGoodItems(marqueeItems)
        setLastUpdatedAt(now)
        setIsStale(false)
        setCurrentIndex((prev) =>
          marqueeItems.length > 0 && prev >= marqueeItems.length ? 0 : prev
        )
        hasLoadedOnce.current = true
      } catch (error) {
        console.error("Error fetching games for marquee:", error)
        setIsStale(true)
      } finally {
        setLoading(false)
      }
    }

    fetchGames()
    const pollInterval = setInterval(fetchGames, 15000)

    return () => {
      clearInterval(pollInterval)
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [])

  useEffect(() => {
    const t = setInterval(() => setNowTick(new Date()), 2000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    if (items.length === 0 || isPaused) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      return
    }
    intervalRef.current = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % items.length)
    }, 5000)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [items.length, isPaused])

  const displayItems = items.length > 0 ? items : lastGoodItems
  const currentItem = displayItems.length > 0 ? displayItems[currentIndex % displayItems.length] : null

  return (
    <div
      className="relative overflow-hidden bg-black/40 border-b border-white/10 py-2"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <div className="container mx-auto px-4">
        <div className="flex items-center gap-4">
          <div className="flex-shrink-0">
            <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">
              Live Feed
            </span>
          </div>
          <div className="flex-1 min-w-0 flex items-center gap-2 overflow-hidden">
            {loading && displayItems.length === 0 ? (
              <div className="text-sm text-gray-400">Loading games...</div>
            ) : currentItem ? (
              <AnimatePresence mode="wait">
                <motion.div
                  key={currentItem.id}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                  className="flex items-center gap-2 min-w-0 shrink-0"
                >
                  <span className="flex items-center gap-1.5 shrink-0">
                    <span
                      className="text-[11px] px-2 py-0.5 rounded-full border border-white/10 bg-white/5 text-gray-300"
                      title={currentItem.categoryLabel}
                    >
                      {currentItem.categoryLabel}
                    </span>
                    <span
                      className="text-[11px] px-2 py-0.5 rounded-full border border-white/10 bg-white/5 text-gray-300"
                      title={currentItem.leagueLabel}
                    >
                      {currentItem.leagueLabel}
                    </span>
                  </span>
                  {currentItem.type === "live" && (
                    <span className="relative flex h-2 w-2 shrink-0">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500" />
                    </span>
                  )}
                  <span
                    className={`min-w-0 truncate text-sm ${
                      currentItem.type === "live"
                        ? "text-red-300 font-semibold"
                        : currentItem.type === "final"
                          ? "text-gray-300 font-medium"
                          : "text-white"
                    }`}
                  >
                    {currentItem.displayText}
                  </span>
                  {currentItem.type === "upcoming" && currentItem.upcomingMeta && (
                    <span className="text-xs text-gray-400 shrink-0">
                      {currentItem.upcomingMeta}
                    </span>
                  )}
                </motion.div>
              </AnimatePresence>
            ) : (
              <div className="text-sm text-gray-400">No games scheduled. Check back soon!</div>
            )}
          </div>
          <div className="flex-shrink-0 flex items-center gap-2">
            {lastUpdatedAt && (
              <span className="text-xs text-gray-500">
                {formatUpdatedAgo(lastUpdatedAt, nowTick)}
              </span>
            )}
            {isStale && (
              <span className="text-xs text-amber-400">Reconnecting…</span>
            )}
            {displayItems.length > 0 && (
              <div className="flex gap-1">
                {displayItems.map((_, idx) => (
                  <div
                    key={idx}
                    className={`h-1 w-1 rounded-full ${
                      idx === currentIndex % displayItems.length ? "bg-emerald-400" : "bg-white/20"
                    }`}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
