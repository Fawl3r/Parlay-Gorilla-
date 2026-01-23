"use client"

import { useEffect, useState } from "react"
import { api, GameFeedResponse } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { Loader2, Clock, AlertTriangle } from "lucide-react"
import { cn } from "@/lib/utils"

interface GameFeedProps {
  sport?: string
  window?: "today" | "upcoming" | "live" | "all"
}

export function GameFeed({ sport, window = "today" }: GameFeedProps) {
  const [games, setGames] = useState<GameFeedResponse[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchGames = async () => {
      setLoading(true)
      try {
        const data = await api.getGameFeed(sport, window)
        setGames(data)
      } catch (error) {
        console.error("Error fetching game feed:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchGames()
    const interval = setInterval(fetchGames, 30000) // Refresh every 30 seconds

    return () => clearInterval(interval)
  }, [sport, window])

  const getStatusBadge = (status: string, isStale: boolean) => {
    if (isStale) {
      return (
        <Badge variant="outline" className="bg-yellow-500/20 text-yellow-300 border-yellow-500/30">
          <AlertTriangle className="h-3 w-3 mr-1" />
          Stale
        </Badge>
      )
    }

    switch (status.toUpperCase()) {
      case "LIVE":
        return (
          <Badge variant="outline" className="bg-red-500/20 text-red-300 border-red-500/30">
            LIVE
          </Badge>
        )
      case "FINAL":
        return (
          <Badge variant="outline" className="bg-gray-500/20 text-gray-300 border-gray-500/30">
            FINAL
          </Badge>
        )
      default:
        return (
          <Badge variant="outline" className="bg-blue-500/20 text-blue-300 border-blue-500/30">
            {status}
          </Badge>
        )
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
      </div>
    )
  }

  if (games.length === 0) {
    return <div className="text-center py-20 text-gray-400">No games found</div>
  }

  return (
    <div className="space-y-2">
      {games.map((game) => (
        <div
          key={game.id}
          className="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-all"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-white uppercase">{game.sport}</span>
              {getStatusBadge(game.status, game.is_stale)}
            </div>
            <div className="text-xs text-gray-500 flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {new Date(game.start_time).toLocaleString()}
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="text-lg font-bold text-white">
                {game.away_team} @ {game.home_team}
              </div>
              {game.status === "LIVE" && (game.period || game.clock) && (
                <div className="text-sm text-gray-400 mt-1">
                  {game.period} {game.clock && `• ${game.clock}`}
                </div>
              )}
            </div>

            {(game.home_score !== null || game.away_score !== null) && (
              <div className="text-2xl font-bold text-white ml-4">
                {game.away_score ?? 0} - {game.home_score ?? 0}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
