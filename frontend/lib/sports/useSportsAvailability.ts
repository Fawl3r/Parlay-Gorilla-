"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { api } from "@/lib/api"
import type { SportListItem } from "@/lib/api/types"
import { sportsUiPolicy } from "@/lib/sports/SportsUiPolicy"
import {
  getSportsAvailabilityCache,
  setSportsAvailabilityCache,
} from "@/lib/sports/sportsAvailabilityCache"

/**
 * Stale-while-error: when /api/sports fails we show the last known good list from
 * sessionStorage so the UI stays usable during transient outages. Backend fallback
 * (hardcoded sports) is NOT allowed here or in GamesApi — the backend is the single
 * source of truth when reachable; only cached payload is used when unreachable.
 */

function normalizeSlug(slug: string): string {
  return (slug || "").toLowerCase().trim()
}

function normalizeSport(s: SportListItem): SportListItem {
  const slug = normalizeSlug(s.slug)
  return { ...s, slug: slug || s.slug }
}

export type SportsAvailabilityError = { message: string }

export function useSportsAvailability() {
  const [sports, setSports] = useState<SportListItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<SportsAvailabilityError | null>(null)
  const [savedAt, setSavedAt] = useState<number | undefined>(undefined)

  // On mount: hydrate from cache (client-only) so first paint is not blank
  useEffect(() => {
    const cached = getSportsAvailabilityCache()
    if (cached?.data?.length) {
      setSports(cached.data)
      setSavedAt(cached.savedAt)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    setError(null)
    setIsLoading(true)

    api
      .listSports()
      .then((list) => {
        if (cancelled) return
        const raw = list || []
        const normalized = raw.map(normalizeSport)
        const visible = sportsUiPolicy.filterVisible(normalized)
        setSports(visible)
        setSavedAt(undefined)
        setError(null)
        setSportsAvailabilityCache(visible)
      })
      .catch((err) => {
        if (cancelled) return
        setError({
          message: err?.message || "Couldn't reach backend. Try refresh.",
        })
        const cached = getSportsAvailabilityCache()
        if (cached?.data?.length) {
          setSports(cached.data)
          setSavedAt(cached.savedAt)
        } else {
          setSports([])
          setSavedAt(undefined)
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const bySlug = useMemo(() => {
    const map = new Map<string, SportListItem>()
    for (const s of sports) {
      const key = normalizeSlug(s.slug)
      if (key) map.set(key, s)
    }
    return map
  }, [sports])

  const getSport = useCallback(
    (slug: string): SportListItem | undefined => {
      return bySlug.get(normalizeSlug(slug))
    },
    [bySlug]
  )

  /**
   * Enable/disable is determined ONLY by backend is_enabled (and policy for coming-soon).
   * No local season logic — backend is source of truth.
   */
  const isSportEnabled = useCallback(
    (slug: string): boolean => {
      const sport = bySlug.get(normalizeSlug(slug))
      if (!sport) return false
      return typeof sport.is_enabled === "boolean"
        ? sport.is_enabled
        : (sport.in_season !== false)
    },
    [bySlug]
  )

  const getSportBadge = useCallback(
    (slug: string): string => {
      const sport = bySlug.get(normalizeSlug(slug))
      if (!sport) return ""
      const availability = sportsUiPolicy.resolveAvailability(sport)
      if (availability.isComingSoon) return "Coming soon"
      return availability.statusLabel || ""
    },
    [bySlug]
  )

  const visibleSports = useMemo(
    () => sportsUiPolicy.filterVisible(sports),
    [sports]
  )
  const isStale = error !== null && savedAt !== undefined

  return {
    sports: visibleSports,
    bySlug,
    isLoading,
    error,
    isStale,
    savedAt,
    getSport,
    isSportEnabled,
    getSportBadge,
    normalizeSlug,
  }
}
