"use client"

import { useEffect, useState } from "react"
import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import Link from "next/link"
import { ArrowLeft, Star, StarOff } from "lucide-react"
import type { GameResponse } from "@/lib/api/types/game"

export default function WatchlistPage() {
  const [games, setGames] = useState<GameResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [userId] = useState<string>("default") // TODO: Get from auth

  useEffect(() => {
    const fetchWatchlist = async () => {
      try {
        const response = await fetch(`/api/user/${userId}/watchlist`)
        if (!response.ok) throw new Error("Failed to fetch watchlist")

        const data: GameResponse[] = await response.json()
        setGames(data || [])
      } catch (error) {
        console.error("Error fetching watchlist:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchWatchlist()
  }, [userId])

  const handleUnwatch = async (gameId: string) => {
    try {
      const response = await fetch(`/api/games/${gameId}/watch?user_id=${userId}`, {
        method: "DELETE",
      })
      if (!response.ok) throw new Error("Failed to unwatch game")

      setGames(games.filter((g) => g.id !== gameId))
    } catch (error) {
      console.error("Error unwatching game:", error)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-gray-900 to-black">
      <Header />
      <main className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-white/60 hover:text-white transition-colors mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>
          <h1 className="text-3xl font-extrabold text-white mb-2">My Watchlist</h1>
          <p className="text-white/60">Games you're tracking</p>
        </div>

        {loading ? (
          <div className="text-white/60">Loading...</div>
        ) : games.length === 0 ? (
          <div className="text-white/60">No games in your watchlist</div>
        ) : (
          <div className="grid gap-4">
            {games.map((game) => (
              <div
                key={game.id}
                className="rounded-xl border border-white/10 bg-black/25 backdrop-blur-sm p-5"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-white mb-1">
                      {game.away_team} @ {game.home_team}
                    </h3>
                    <div className="text-sm text-white/60 mb-2">{game.sport}</div>
                    <div className="text-sm text-white/60">
                      {new Date(game.start_time).toLocaleString()}
                    </div>
                    <Link
                      href={`/analysis/${game.sport.toLowerCase()}/${game.away_team.toLowerCase()}-vs-${game.home_team.toLowerCase()}`}
                      className="text-sm text-emerald-500 hover:text-emerald-400 mt-2 inline-block"
                    >
                      View Analysis →
                    </Link>
                  </div>
                  <button
                    onClick={() => handleUnwatch(game.id)}
                    className="p-2 rounded-lg border border-white/15 bg-white/5 hover:bg-white/10 transition-colors"
                    title="Remove from watchlist"
                  >
                    <StarOff className="w-5 h-5 text-white/60" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
      <Footer />
    </div>
  )
}
