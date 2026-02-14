"use client"

import { useCallback, useEffect, useMemo, useState } from "react"

import type { GameResponse } from "@/lib/api"
import { api } from "@/lib/api"
import { addDays, formatDateString, getTargetDate, getLocalDateString, isGameOnDate } from "@/components/games/gamesDateUtils"
import { filterSaneGames } from "@/lib/games/GameDeduper"
import { dedupeGamesPreferOdds } from "@/lib/games/GameOddsDeduper"

/**
 * Invariant: scheduled games must render even when markets is empty.
 * Markets/odds must never be required for game visibility — only status and date.
 */

export type MarketFilter = "all" | "h2h" | "spreads" | "totals"

export type GamesLoadError =
  | { kind: "rate_limit"; message: string }
  | { kind: "network"; message: string }
  | { kind: "server"; message: string }
  | { kind: "unknown"; message: string }

/** Metadata from games list API for empty-state UI (offseason / preseason). */
export type GamesListMeta = {
  sport_state?: string | null
  next_game_at?: string | null
  status_label?: string | null
  days_to_next?: number | null
  preseason_enable_days?: number | null
}

type Options = {
  sport: string
  date: string
}

export function useGamesForSportDate({ sport, date }: Options) {
  const [games, setGames] = useState<GameResponse[]>([])
  const [listMeta, setListMeta] = useState<GamesListMeta | null>(null)
  const [suggestedDate, setSuggestedDate] = useState<string | null>(null)
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
      setSuggestedDate(null)
      try {
        const response = await api.getGames(sport, undefined, forceRefresh)
        const gamesData = response.games ?? []
        setListMeta({
          sport_state: response.sport_state ?? undefined,
          next_game_at: response.next_game_at ?? undefined,
          status_label: response.status_label ?? undefined,
          days_to_next: response.days_to_next ?? undefined,
          preseason_enable_days: response.preseason_enable_days ?? undefined,
        })

        // When date is "all", return every game (for DraftKings-style tab filtering in the hub).
        if (date === "all") {
          const sorted = [...gamesData].sort(
            (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
          )
          const sane = filterSaneGames(sorted)
          const { games: deduped, oddsPreferredKeys: keys } = dedupeGamesPreferOdds(sane)
          setGames(deduped)
          setOddsPreferredKeys(keys)
          setLoading(false)
          return
        }

        const targetDate = getTargetDate(date)
        const targetDateStr = formatDateString(targetDate)
        const now = new Date()

        // Filter by calendar day (local). Do NOT require markets.length > 0; include scheduled games.
        const filtered = gamesData.filter((game) => {
          if (!isGameOnDate(game.start_time, date)) return false
          const gameDate = new Date(game.start_time)
          const gameStatus = game.status?.toLowerCase() || ""
          if (["finished", "closed", "complete"].includes(gameStatus)) return false
          if (gameDate < now) {
            const hoursSinceStart = (now.getTime() - gameDate.getTime()) / (1000 * 60 * 60)
            return hoursSinceStart <= maxHoursSinceStart
          }
          return true
        })

        // Option A: When "today" has no games, use next available date so we show upcoming games.
        let gamesToShow = filtered
        let suggestedDate: string | null = null
        if (filtered.length === 0 && gamesData.length > 0 && date === "today") {
          const nextGameAt = response.next_game_at
          const nextDateStr = nextGameAt
            ? getLocalDateString(new Date(nextGameAt))
            : (() => {
                const future = gamesData
                  .filter((g) => {
                    const st = g.status?.toLowerCase() || ""
                    if (["finished", "closed", "complete"].includes(st)) return false
                    return new Date(g.start_time) > now
                  })
                  .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
                return future.length > 0 ? getLocalDateString(new Date(future[0].start_time)) : null
              })()
          if (nextDateStr) {
            suggestedDate = nextDateStr
            gamesToShow = gamesData.filter((game: GameResponse) => {
              if (!isGameOnDate(game.start_time, nextDateStr!)) return false
              const gameDate = new Date(game.start_time)
              const gameStatus = game.status?.toLowerCase() || ""
              if (["finished", "closed", "complete"].includes(gameStatus)) return false
              if (gameDate < now) {
                const hoursSinceStart = (now.getTime() - gameDate.getTime()) / (1000 * 60 * 60)
                return hoursSinceStart <= maxHoursSinceStart
              }
              return true
            })
          }
        }

        // If still empty, include nearby calendar days (yesterday/tomorrow) for non-today
        if (gamesToShow.length === 0 && gamesData.length > 0 && !suggestedDate) {
          const prevDateStr = formatDateString(addDays(targetDate, -1))
          const nextDateStr = formatDateString(addDays(targetDate, 1))
          gamesToShow = gamesData.filter((game: GameResponse) => {
            const gameLocalDateStr = getLocalDateString(new Date(game.start_time))
            const inExpandedRange =
              gameLocalDateStr === targetDateStr ||
              gameLocalDateStr === prevDateStr ||
              gameLocalDateStr === nextDateStr
            if (!inExpandedRange) return false
            const gameDate = new Date(game.start_time)
            const gameStatus = game.status?.toLowerCase() || ""
            if (["finished", "closed", "complete"].includes(gameStatus)) return false
            if (gameDate < now) {
              const hoursSinceStart = (now.getTime() - gameDate.getTime()) / (1000 * 60 * 60)
              return hoursSinceStart <= maxHoursSinceStart
            }
            return true
          })
        }

        if (process.env.NODE_ENV !== "production") {
          console.debug("[useGamesForSportDate]", {
            sport,
            date,
            rawGamesCount: gamesData.length,
            first3Starts: gamesData.slice(0, 3).map((g) => g.start_time),
            visibleCount: gamesToShow.length,
            suggestedDate: suggestedDate ?? undefined,
          })
        }

        const sorted = [...gamesToShow].sort(
          (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
        )

        const sane = filterSaneGames(sorted)
        const { games: deduped, oddsPreferredKeys: keys } = dedupeGamesPreferOdds(sane)
        setGames(deduped)
        setSuggestedDate(suggestedDate)
        setOddsPreferredKeys(keys)
      } catch (err: any) {
        setGames([])
        setSuggestedDate(null)
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
              `Server error (${status}). The backend may not be reachable. ` +
              "If running locally, verify `frontend/.env.local` has PG_BACKEND_URL/NEXT_PUBLIC_API_URL set to `http://localhost:8000` " +
              "and restart the Next.js dev server. " +
              "If running on Cloudflare, verify the frontend build/deploy is configured to reach `https://api.parlaygorilla.com` " +
              "(or set PG_BACKEND_URL/NEXT_PUBLIC_API_URL in the Cloudflare environment and redeploy).",
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
    listMeta,
    suggestedDate,
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


