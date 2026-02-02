"use client"

import { useEffect, useState, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { api, GameFeedResponse } from "@/lib/api"
import { cn } from "@/lib/utils"
import {
  getWindowType,
  getCategoryLabel,
  getLeagueLabel,
  formatUpcomingMeta,
  formatUpdatedAgo,
} from "@/lib/games/GameFeedDisplayManager"
import { filterSaneGames, dedupeGames } from "@/lib/games/GameDeduper"

export type LiveMarqueeVariant = "mobile" | "desktop"

export type LiveMarqueeProps = {
  variant?: LiveMarqueeVariant
}

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

/** Exported for unit tests: combined feed after sanity filter, dedupe, and ordering. */
export function buildCombinedFeed(
  live: GameFeedResponse[],
  today: GameFeedResponse[],
  upcoming: GameFeedResponse[]
): GameFeedResponse[] {
  const saneLive = filterSaneGames(live)
  const saneToday = filterSaneGames(today)
  const saneUpcoming = filterSaneGames(upcoming)
  const finalsFromToday = saneToday.filter((g) => getWindowType(g.status) === "final")

  const liveSorted = [...saneLive].sort(
    (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
  )
  const finalSorted = [...finalsFromToday].sort(
    (a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime()
  )
  const upcomingSorted = [...saneUpcoming].sort(
    (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
  )

  const combined = dedupeGames([...liveSorted, ...finalSorted, ...upcomingSorted])
  return combined.slice(0, CAP)
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

export function LiveMarquee({ variant = "desktop" }: LiveMarqueeProps) {
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

  const isMobileVariant = variant === "mobile"

  return (
    <div
      className={cn(
        "relative overflow-hidden border-b border-white/10",
        isMobileVariant
          ? "sticky top-[calc(4rem+env(safe-area-inset-top))] z-40 min-h-[96px] bg-black/90 py-3 backdrop-blur md:static md:z-auto md:min-h-0 md:bg-black/40 md:py-2"
          : "bg-black/40 py-2"
      )}
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <div className={cn("mx-auto w-full", isMobileVariant ? "px-3 md:container md:px-4" : "container px-4")}>
        <div
          className={cn(
            "flex gap-2 overflow-hidden md:items-center md:gap-4",
            isMobileVariant && "flex-col"
          )}
        >
          <div className="flex shrink-0 items-center gap-2">
            <span
              className={cn(
                "font-semibold uppercase tracking-wide text-emerald-400",
                isMobileVariant ? "text-sm md:text-xs md:font-bold" : "text-xs font-bold"
              )}
            >
              Live Feed
            </span>
            {lastUpdatedAt && isMobileVariant && (
              <span className="text-[11px] text-white/40 md:hidden">
                {formatUpdatedAgo(lastUpdatedAt, nowTick)}
              </span>
            )}
          </div>
          <div
            className="min-w-0 flex-1 overflow-hidden"
            aria-live="polite"
            aria-atomic="true"
          >
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
                  className={cn(
                    "flex min-w-0 shrink-0 gap-2",
                    isMobileVariant ? "flex-col gap-1.5 px-0 py-0 md:flex-row md:items-center" : "flex items-center"
                  )}
                >
                  <div
                    className={cn(
                      "flex items-center gap-1.5 shrink-0",
                      isMobileVariant ? "text-[11px] md:text-[11px]" : "text-[11px]"
                    )}
                  >
                    <span
                      className={cn(
                        "text-[11px] rounded-full border border-white/10 bg-white/5 text-gray-300",
                        isMobileVariant ? "px-2.5 py-1 md:px-2 md:py-0.5" : "px-2 py-0.5"
                      )}
                      title={currentItem.categoryLabel}
                    >
                      {currentItem.categoryLabel}
                    </span>
                    <span
                      className={cn(
                        "text-[11px] rounded-full border border-white/10 bg-white/5 text-gray-300",
                        isMobileVariant ? "px-2.5 py-1 md:px-2 md:py-0.5" : "px-2 py-0.5"
                      )}
                      title={currentItem.leagueLabel}
                    >
                      {currentItem.leagueLabel}
                    </span>
                  </div>
                  <div className={cn("flex min-w-0 items-center gap-2", isMobileVariant && "flex-wrap gap-x-2 gap-y-0.5")}>
                    {currentItem.type === "live" && (
                      <span className="relative flex h-2 w-2 shrink-0">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500" />
                      </span>
                    )}
                    <span
                      className={cn(
                        "min-w-0 truncate text-sm",
                        currentItem.type === "live"
                          ? "text-red-300 font-semibold"
                          : currentItem.type === "final"
                            ? "text-gray-300 font-medium"
                            : "text-white"
                      )}
                    >
                      {currentItem.displayText}
                    </span>
                    {currentItem.type === "upcoming" && currentItem.upcomingMeta && (
                      <span className="shrink-0 text-xs text-gray-400">
                        {currentItem.upcomingMeta}
                      </span>
                    )}
                  </div>
                </motion.div>
              </AnimatePresence>
            ) : (
              <div className="text-sm text-gray-400">No games scheduled. Check back soon!</div>
            )}
          </div>
          <div className="flex shrink-0 items-center gap-2 max-md:hidden">
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
                    className={cn(
                      "h-1 w-1 rounded-full",
                      idx === currentIndex % displayItems.length ? "bg-emerald-400" : "bg-white/20"
                    )}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
        {isMobileVariant && (
          <div className="mt-2 flex items-center gap-2 md:hidden">
            {isStale && <span className="text-xs text-amber-400">Reconnecting…</span>}
            {displayItems.length > 0 && (
              <div className="flex gap-1">
                {displayItems.map((_, idx) => (
                  <div
                    key={idx}
                    className={cn(
                      "h-1 w-1 rounded-full",
                      idx === currentIndex % displayItems.length ? "bg-emerald-400" : "bg-white/20"
                    )}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
