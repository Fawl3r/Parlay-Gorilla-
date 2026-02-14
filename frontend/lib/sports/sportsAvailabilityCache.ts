"use client"

import type { SportListItem } from "@/lib/api/types"

export const SPORTS_AVAILABILITY_CACHE_KEY = "pg_sports_availability_cache_v1"

export type SportsAvailabilityCacheEntry = {
  savedAt: number
  data: SportListItem[]
}

let memoryCache: SportsAvailabilityCacheEntry | null = null

/**
 * SSR-safe read from sessionStorage. Returns null on server or on any error.
 * Only stores normalized sports list + savedAt; never env, tokens, or raw responses.
 */
function readFromStorage(): SportsAvailabilityCacheEntry | null {
  if (typeof window === "undefined") return null
  try {
    const raw = sessionStorage.getItem(SPORTS_AVAILABILITY_CACHE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as SportsAvailabilityCacheEntry
    if (!parsed || typeof parsed.savedAt !== "number" || !Array.isArray(parsed.data)) return null
    return parsed
  } catch {
    return null
  }
}

/**
 * Returns the last known good sports list from memory or sessionStorage.
 * SSR-safe: returns null when window is undefined (server render).
 * Used for stale-while-error: show this when /api/sports fails.
 */
export function getSportsAvailabilityCache(): SportsAvailabilityCacheEntry | null {
  if (typeof window === "undefined") return null
  if (memoryCache) return memoryCache
  const fromStorage = readFromStorage()
  if (fromStorage) memoryCache = fromStorage
  return fromStorage
}

/**
 * Stores the normalized sports list to memory and sessionStorage.
 * SSR-safe: no-ops when window is undefined. Writes never throw.
 * Call on successful /api/sports response only.
 */
export function setSportsAvailabilityCache(data: SportListItem[]): void {
  if (typeof window === "undefined") return
  const entry: SportsAvailabilityCacheEntry = { savedAt: Date.now(), data }
  memoryCache = entry
  try {
    sessionStorage.setItem(SPORTS_AVAILABILITY_CACHE_KEY, JSON.stringify(entry))
  } catch {
    // Quota, private mode, or disabled storage — never throw
  }
}
