"use client"

import { useEffect, useState, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { api, GameFeedResponse } from "@/lib/api"

interface MarqueeItem {
  id: string
  type: "live" | "upcoming"
  displayText: string
  game: GameFeedResponse
}

export function LiveMarquee() {
  const [items, setItems] = useState<MarqueeItem[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isPaused, setIsPaused] = useState(false)
  const [loading, setLoading] = useState(true)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  const formatGameForMarquee = (game: GameFeedResponse): MarqueeItem => {
    const isLive = game.status === "LIVE"
    const hasScores = game.home_score !== null && game.away_score !== null
    
    let displayText = ""
    
    if (isLive && hasScores) {
      // Live game with scores: "LIVE: TeamA @ TeamB | 24-21 | Q3 5:32"
      const scoreText = `${game.away_score}-${game.home_score}`
      const periodText = game.period || ""
      const clockText = game.clock ? ` ${game.clock}` : ""
      displayText = `LIVE: ${game.away_team} @ ${game.home_team} | ${scoreText}${periodText ? ` | ${periodText}${clockText}` : ""}`
    } else if (isLive) {
      // Live game without scores yet
      displayText = `LIVE: ${game.away_team} @ ${game.home_team}${game.period ? ` | ${game.period}${game.clock ? ` ${game.clock}` : ""}` : ""}`
    } else {
      // Upcoming game: "UPCOMING: TeamA @ TeamB | 7:00 PM EST"
      const startTime = new Date(game.start_time)
      const timeStr = startTime.toLocaleTimeString("en-US", { 
        hour: "numeric", 
        minute: "2-digit",
        timeZoneName: "short"
      })
      displayText = `UPCOMING: ${game.away_team} @ ${game.home_team} | ${timeStr}`
    }
    
    return {
      id: game.id,
      type: isLive ? "live" : "upcoming",
      displayText,
      game,
    }
  }

  useEffect(() => {
    const fetchGames = async () => {
      try {
        setLoading(true)
        
        // Fetch both live and upcoming games
        const [liveGames, upcomingGames] = await Promise.all([
          api.getGameFeed(undefined, "live").catch(() => [] as GameFeedResponse[]),
          api.getGameFeed(undefined, "upcoming").catch(() => [] as GameFeedResponse[]),
        ])
        
        // Combine and prioritize live games
        const allGames = [...liveGames, ...upcomingGames.slice(0, 10)] // Limit upcoming to 10
        const marqueeItems = allGames.map(formatGameForMarquee)
        
        setItems(marqueeItems)
        // Reset index if it's out of bounds
        setCurrentIndex((prev) => (marqueeItems.length > 0 && prev >= marqueeItems.length ? 0 : prev))
      } catch (error) {
        console.error("Error fetching games for marquee:", error)
        setItems([])
      } finally {
        setLoading(false)
      }
    }

    fetchGames()
    const pollInterval = setInterval(fetchGames, 15000) // Refresh every 15 seconds

    return () => {
      clearInterval(pollInterval)
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
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
    }, 5000) // Rotate every 5 seconds

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [items.length, isPaused])

  const currentItem = items.length > 0 ? items[currentIndex] : null

  return (
    <div
      className="relative overflow-hidden bg-black/40 border-b border-white/10 py-2"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <div className="container mx-auto px-4">
        <div className="flex items-center gap-4">
          <div className="flex-shrink-0">
            <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Live Feed</span>
          </div>
          <div className="flex-1 min-w-0">
            {loading ? (
              <div className="text-sm text-gray-400">Loading games...</div>
            ) : currentItem ? (
              <AnimatePresence mode="wait">
                <motion.div
                  key={currentItem.id}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                  className="text-sm text-white truncate flex items-center gap-2"
                >
                  {currentItem.type === "live" && (
                    <span className="inline-flex items-center gap-1">
                      <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                      </span>
                    </span>
                  )}
                  <span className={currentItem.type === "live" ? "text-red-300 font-semibold" : "text-white"}>
                    {currentItem.displayText}
                  </span>
                </motion.div>
              </AnimatePresence>
            ) : (
              <div className="text-sm text-gray-400">No games scheduled. Check back soon!</div>
            )}
          </div>
          {items.length > 0 && (
            <div className="flex-shrink-0 flex items-center gap-2">
              <div className="flex gap-1">
                {items.map((_, idx) => (
                  <div
                    key={idx}
                    className={`h-1 w-1 rounded-full ${
                      idx === currentIndex ? "bg-emerald-400" : "bg-white/20"
                    }`}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
