"use client"

import { useState, useEffect } from "react"
import { Star, StarOff } from "lucide-react"
import { cn } from "@/lib/utils"

export type WatchButtonProps = {
  gameId: string
  userId?: string
  className?: string
}

export function WatchButton({ gameId, userId = "default", className }: WatchButtonProps) {
  const [isWatched, setIsWatched] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    // Check if game is in watchlist
    const checkWatchlist = async () => {
      try {
        const response = await fetch(`/api/user/${userId}/watchlist`)
        if (response.ok) {
          const games = await response.json()
          setIsWatched(games.some((g: any) => g.id === gameId))
        }
      } catch (error) {
        console.error("Error checking watchlist:", error)
      }
    }

    checkWatchlist()
  }, [gameId, userId])

  const handleToggle = async () => {
    setLoading(true)
    try {
      if (isWatched) {
        const response = await fetch(`/api/games/${gameId}/watch?user_id=${userId}`, {
          method: "DELETE",
        })
        if (response.ok) {
          setIsWatched(false)
        }
      } else {
        const response = await fetch(`/api/games/${gameId}/watch?user_id=${userId}`, {
          method: "POST",
        })
        if (response.ok) {
          setIsWatched(true)
        }
      }
    } catch (error) {
      console.error("Error toggling watchlist:", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <button
      type="button"
      onClick={handleToggle}
      disabled={loading}
      className={cn(
        "px-4 py-2 rounded-lg border border-white/15 bg-white/5 text-white font-extrabold hover:bg-white/10 transition-colors flex items-center gap-2",
        className
      )}
      title={isWatched ? "Remove from watchlist" : "Add to watchlist"}
    >
      {isWatched ? (
        <>
          <Star className="w-4 h-4 fill-yellow-500 text-yellow-500" />
          <span>Watching</span>
        </>
      ) : (
        <>
          <StarOff className="w-4 h-4" />
          <span>Watch</span>
        </>
      )}
    </button>
  )
}
