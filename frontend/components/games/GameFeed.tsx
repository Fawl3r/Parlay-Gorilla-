"use client"

import { useEffect, useState, useRef } from "react"
import { api, GameFeedResponse } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { Loader2, Clock, AlertTriangle } from "lucide-react"
import {
  getWindowType,
  getCategoryLabel,
  getLeagueLabel,
  formatUpcomingMeta,
} from "@/lib/games/GameFeedDisplayManager"

interface GameFeedProps {
  sport?: string
  window?: "today" | "upcoming" | "live" | "all"
}

export function GameFeed({ sport, window = "today" }: GameFeedProps) {
  const [games, setGames] = useState<GameFeedResponse[]>([])
  const [lastGoodGames, setLastGoodGames] = useState<GameFeedResponse[]>([])
  const [isStale, setIsStale] = useState(false)
  const [loading, setLoading] = useState(true)
  const hasLoadedOnce = useRef(false)

  useEffect(() => {
    const fetchGames = async () => {
      try {
        if (!hasLoadedOnce.current) setLoading(true)
        const data = await api.getGameFeed(sport, window)
        setGames(data)
        setLastGoodGames(data)
        setIsStale(false)
        hasLoadedOnce.current = true
      } catch (error) {
        console.error("Error fetching game feed:", error)
        setIsStale(true)
      } finally {
        setLoading(false)
      }
    }

    fetchGames()
    const interval = setInterval(fetchGames, 30000)

    return () => clearInterval(interval)
  }, [sport, window])

  const displayGames = games.length > 0 ? games : lastGoodGames

  const getStatusBadge = (status: string, gameStale: boolean) => {
    if (gameStale || isStale) {
      return (
        <Badge variant="outline" className="bg-yellow-500/20 text-yellow-300 border-yellow-500/30">
          <AlertTriangle className="h-3 w-3 mr-1" />
          Stale
        </Badge>
      )
    }

    const windowType = getWindowType(status)
    if (windowType === "live") {
      return (
        <Badge variant="outline" className="bg-red-500/20 text-red-300 border-red-500/30">
          LIVE
        </Badge>
      )
    }
    if (windowType === "final") {
      return (
        <Badge variant="outline" className="bg-gray-500/20 text-gray-300 border-gray-500/30">
          FINAL
        </Badge>
      )
    }
    return (
      <Badge variant="outline" className="bg-blue-500/20 text-blue-300 border-blue-500/30">
        {status || "Upcoming"}
      </Badge>
    )
  }

  if (loading && displayGames.length === 0) {
    return (
      <div className="flex justify-center items-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
      </div>
    )
  }

  if (displayGames.length === 0) {
    return <div className="text-center py-20 text-gray-400">No games found</div>
  }

  return (
    <div className="space-y-2">
      {isStale && (
        <div className="text-xs text-amber-400 flex items-center gap-1">
          <AlertTriangle className="h-3 w-3 shrink-0" />
          Reconnecting…
        </div>
      )}
      {displayGames.map((game) => {
        const windowType = getWindowType(game.status)
        const categoryLabel = getCategoryLabel(game.sport)
        const leagueLabel = getLeagueLabel(game.sport)
        const upcomingMeta =
          windowType === "upcoming" ? formatUpcomingMeta(game.start_time, new Date()) : null

        return (
          <div
            key={game.id}
            className="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-all"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 flex-wrap">
                <span
                  className="text-[11px] px-2 py-0.5 rounded-full border border-white/10 bg-white/5 text-gray-300"
                  title={categoryLabel}
                >
                  {categoryLabel}
                </span>
                <span
                  className="text-[11px] px-2 py-0.5 rounded-full border border-white/10 bg-white/5 text-gray-300"
                  title={leagueLabel}
                >
                  {leagueLabel}
                </span>
                {getStatusBadge(game.status, game.is_stale)}
              </div>
              <div className="text-xs text-gray-500 flex items-center gap-1 shrink-0">
                <Clock className="h-3 w-3" />
                {upcomingMeta ?? new Date(game.start_time).toLocaleString()}
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex-1 min-w-0">
                <div className="text-lg font-bold text-white">
                  {game.away_team} @ {game.home_team}
                </div>
                {windowType === "live" && (game.period || game.clock) && (
                  <div className="text-sm text-gray-400 mt-1">
                    {game.period} {game.clock && `• ${game.clock}`}
                  </div>
                )}
              </div>

              {(game.home_score !== null || game.away_score !== null) && (
                <div className="text-2xl font-bold text-white ml-4 shrink-0">
                  {game.away_score ?? 0} - {game.home_score ?? 0}
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
