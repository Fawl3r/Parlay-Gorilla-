"use client"

import { useCallback, useEffect, useMemo, useState } from "react"

import type { GameResponse } from "@/lib/api"
import { api } from "@/lib/api"
import { addDays, formatDateString, getTargetDate } from "@/components/games/gamesDateUtils"

export type MarketFilter = "all" | "h2h" | "spreads" | "totals"

export type GamesLoadError =
  | { kind: "rate_limit"; message: string }
  | { kind: "network"; message: string }
  | { kind: "unknown"; message: string }

type Options = {
  sport: string
  date: string
}

export function useGamesForSportDate({ sport, date }: Options) {
  const [games, setGames] = useState<GameResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<GamesLoadError | null>(null)

  // Some sports run longer than 2 hours (NBA/NHL/NCAAF), and backend statuses may not flip to "finished" immediately.
  // Keep started games visible for a generous window to avoid "missing games" reports.
  const maxHoursSinceStart = 8

  const loadGames = useCallback(
    async (forceRefresh: boolean) => {
      setLoading(true)
      setError(null)
      try {
        const gamesData = await api.getGames(sport, undefined, forceRefresh)

        const targetDate = getTargetDate(date)
        const startOfDay = new Date(targetDate)
        startOfDay.setHours(0, 0, 0, 0)
        const endOfDay = new Date(targetDate)
        endOfDay.setHours(23, 59, 59, 999)

        const now = new Date()
        
        const filtered = gamesData.filter((game) => {
          const gameDate = new Date(game.start_time)
          const gameStatus = game.status?.toLowerCase() || ""
          
          // Filter by date
          const isInDateRange = gameDate >= startOfDay && gameDate <= endOfDay
          if (!isInDateRange) return false
          
          // Exclude finished/closed games
          if (gameStatus === "finished" || gameStatus === "closed" || gameStatus === "complete") {
            return false
          }
          
          // For games that have started, keep them visible for a reasonable window.
          if (gameDate < now) {
            const hoursSinceStart = (now.getTime() - gameDate.getTime()) / (1000 * 60 * 60)
            return hoursSinceStart <= maxHoursSinceStart
          }
          
          // Include all future games
          return true
        })

        const gamesToShow = filtered.length > 0 ? filtered : gamesData.filter((game) => {
          // If no games match the date filter, still filter out old completed games
          const gameStatus = game.status?.toLowerCase() || ""
          if (gameStatus === "finished" || gameStatus === "closed" || gameStatus === "complete") {
            return false
          }
          const gameDate = new Date(game.start_time)
          if (gameDate < now) {
            const hoursSinceStart = (now.getTime() - gameDate.getTime()) / (1000 * 60 * 60)
            return hoursSinceStart <= maxHoursSinceStart
          }
          return true
        })
        
        const sorted = [...gamesToShow].sort(
          (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
        )

        setGames(sorted)
      } catch (err: any) {
        setGames([])

        const status = err?.response?.status
        if (status === 429) {
          const detail = err?.response?.data?.detail
          const message =
            detail?.message || detail || "Rate limit exceeded. Please wait a few minutes before refreshing."
          setError({ kind: "rate_limit", message: `Rate Limit: ${message}` })
          return
        }

        if (err?.isTimeout || err?.code === "ECONNABORTED" || String(err?.message || "").includes("timeout")) {
          setError({
            kind: "network",
            message:
              "Connection timeout. The backend server may not be reachable. Please verify the backend is running.",
          })
          return
        }

        if (err?.code === "ERR_NETWORK") {
          setError({
            kind: "network",
            message: "Network error. Unable to connect to the backend server. Please check if it's running.",
          })
          return
        }

        setError({ kind: "unknown", message: "Failed to load games. Please try again later." })
      } finally {
        setLoading(false)
      }
    },
    [date, sport]
  )

  useEffect(() => {
    let cancelled = false
    if (cancelled) return
    loadGames(false)
    return () => {
      cancelled = true
    }
  }, [loadGames])

  const dateLabel = useMemo(() => {
    return date === "today" || date === "tomorrow" ? date : formatDateString(getTargetDate(date))
  }, [date])

  const previousDateHref = useMemo(() => {
    const base = getTargetDate(date)
    return formatDateString(addDays(base, -1))
  }, [date])

  const nextDateHref = useMemo(() => {
    const base = getTargetDate(date)
    return formatDateString(addDays(base, 1))
  }, [date])

  const refresh = async () => {
    setRefreshing(true)
    try {
      await loadGames(true)
    } finally {
      setRefreshing(false)
    }
  }

  return {
    games,
    loading,
    refreshing,
    error,
    dateLabel,
    previousDateHref,
    nextDateHref,
    refresh,
  }
}


