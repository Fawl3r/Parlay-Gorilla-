"use client"

import { useCallback, useEffect, useMemo, useState } from "react"

import type { GameResponse } from "@/lib/api"
import { api } from "@/lib/api"
import { addDays, formatDateString, getTargetDate } from "@/components/games/gamesDateUtils"
import { filterSaneGames } from "@/lib/games/GameDeduper"
import { dedupeGamesPreferOdds } from "@/lib/games/GameOddsDeduper"

export type MarketFilter = "all" | "h2h" | "spreads" | "totals"

export type GamesLoadError =
  | { kind: "rate_limit"; message: string }
  | { kind: "network"; message: string }
  | { kind: "server"; message: string }
  | { kind: "unknown"; message: string }

type Options = {
  sport: string
  date: string
}

export function useGamesForSportDate({ sport, date }: Options) {
  const [games, setGames] = useState<GameResponse[]>([])
  const [oddsPreferredKeys, setOddsPreferredKeys] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<GamesLoadError | null>(null)

  // Some sports run longer than 2 hours (NBA/NHL/NCAAF), and backend statuses may not flip to "finished" immediately.
  // Keep started games visible for a generous window to avoid "missing games" reports.
  // Keep started games visible for a full day to avoid "no games" reports
  // when users open the app after games have already started (especially for
  // sports where slates can span late-night UTC kickoffs).
  const maxHoursSinceStart = 24

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
        
        // First, filter by date and status
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

        // If no games match the exact date, expand the range to include nearby dates
        // This ensures games are visible even if there are no games for the selected date
        let gamesToShow = filtered
        if (filtered.length === 0 && gamesData.length > 0) {
          // Expand to include yesterday, today, and tomorrow
          const expandedStart = new Date(startOfDay)
          expandedStart.setDate(expandedStart.getDate() - 1)
          const expandedEnd = new Date(endOfDay)
          expandedEnd.setDate(expandedEnd.getDate() + 1)
          
          gamesToShow = gamesData.filter((game) => {
            const gameDate = new Date(game.start_time)
            const gameStatus = game.status?.toLowerCase() || ""
            
            // Filter by expanded date range
            const isInExpandedRange = gameDate >= expandedStart && gameDate <= expandedEnd
            if (!isInExpandedRange) return false
            
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
          
          // If still no games and date is "today", show the next upcoming game
          // This prevents showing "no games" when user is on today's view
          if (gamesToShow.length === 0 && date === "today") {
            const nextUpcoming = gamesData
              .filter((game) => {
                const gameDate = new Date(game.start_time)
                const gameStatus = game.status?.toLowerCase() || ""
                
                // Exclude finished/closed games
                if (gameStatus === "finished" || gameStatus === "closed" || gameStatus === "complete") {
                  return false
                }
                
                // Only show future games (not past games)
                return gameDate > now
              })
              .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
            
            // Show the next upcoming game (or a few if available)
            if (nextUpcoming.length > 0) {
              gamesToShow = [nextUpcoming[0]]
            }
          }
        }
        
        const sorted = [...gamesToShow].sort(
          (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
        )

        const sane = filterSaneGames(sorted)
        const { games: deduped, oddsPreferredKeys: keys } = dedupeGamesPreferOdds(sane)
        setGames(deduped)
        setOddsPreferredKeys(keys)
      } catch (err: any) {
        setGames([])
        setOddsPreferredKeys(new Set())

        const status = err?.response?.status
        if (status === 429) {
          const detail = err?.response?.data?.detail
          const message =
            detail?.message || detail || "Rate limit exceeded. Please wait a few minutes before refreshing."
          setError({ kind: "rate_limit", message: `Rate Limit: ${message}` })
          return
        }

        if (typeof status === "number" && status >= 500) {
          setError({
            kind: "server",
            message:
              `Server error (${status}). If you are running locally, verify ` +
              "`frontend/.env.local` has PG_BACKEND_URL/NEXT_PUBLIC_API_URL set to `http://localhost:8000` " +
              "and restart the Next.js dev server.",
          })
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
    oddsPreferredKeys,
    loading,
    refreshing,
    error,
    dateLabel,
    previousDateHref,
    nextDateHref,
    refresh,
  }
}


