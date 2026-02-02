/**
 * Persist Custom Builder slip (sport + picks) for 12h with safe restore.
 * Per-user key when userId exists; anon key otherwise.
 */

import type { GameResponse } from "@/lib/api"
import type { SelectedPick } from "@/components/custom-parlay/types"

const STORAGE_KEY_PREFIX = "pg_custom_builder_slip"
const TTL_MS = 12 * 60 * 60 * 1000
const SCHEMA_VERSION = 1

export type PersistedCustomBuilderSlip = {
  v: typeof SCHEMA_VERSION
  savedAt: number
  selectedSport: string
  picks: SelectedPick[]
}

function storageKey(userId: string | null): string {
  return `${STORAGE_KEY_PREFIX}:${userId ?? "anon"}`
}

/**
 * Load persisted slip if present and not expired. Returns null when missing or expired.
 */
export function loadSlip(userId: string | null): PersistedCustomBuilderSlip | null {
  if (typeof window === "undefined") return null
  try {
    const raw = localStorage.getItem(storageKey(userId))
    if (!raw) return null
    const data = JSON.parse(raw) as PersistedCustomBuilderSlip
    if (data?.v !== SCHEMA_VERSION || typeof data.savedAt !== "number") return null
    if (Date.now() - data.savedAt > TTL_MS) {
      localStorage.removeItem(storageKey(userId))
      return null
    }
    return data
  } catch {
    return null
  }
}

/**
 * Persist slip. Overwrites existing; TTL is enforced on load.
 */
export function saveSlip(userId: string | null, slip: PersistedCustomBuilderSlip): void {
  if (typeof window === "undefined") return
  try {
    const payload: PersistedCustomBuilderSlip = {
      v: SCHEMA_VERSION,
      savedAt: Date.now(),
      selectedSport: slip.selectedSport,
      picks: slip.picks,
    }
    localStorage.setItem(storageKey(userId), JSON.stringify(payload))
  } catch {
    // Silent fail
  }
}

/**
 * Remove persisted slip for the user.
 */
export function clearSlip(userId: string | null): void {
  if (typeof window === "undefined") return
  try {
    localStorage.removeItem(storageKey(userId))
  } catch {
    // Silent fail
  }
}

/**
 * Filter picks to those valid against the current games list.
 * A pick is valid if: game exists, game has markets, market_type exists on game, pick matches an outcome (or minimal: game + market_type exist).
 */
export function filterValidPicks(picks: SelectedPick[], games: GameResponse[]): SelectedPick[] {
  const gameMap = new Map<string, GameResponse>()
  for (const g of games) {
    gameMap.set(String(g.id), g)
  }

  return picks.filter((pick) => {
    const game = gameMap.get(String(pick.game_id))
    if (!game || !game.markets?.length) return false

    const market = game.markets.find((m) => m.market_type === pick.market_type)
    if (!market) return false

    if (pick.market_id) {
      const hasMarketId = game.markets.some((m) => String(m.id) === String(pick.market_id))
      if (!hasMarketId) return false
    }

    const pickLower = String(pick.pick ?? "").toLowerCase()
    const homeLower = String(game.home_team ?? "").toLowerCase()
    const awayLower = String(game.away_team ?? "").toLowerCase()

    const hasOutcome = market.odds?.some((o) => {
      const out = String(o.outcome ?? "").toLowerCase()
      return out === pickLower || out.includes(pickLower) || pickLower.includes(out)
    })
    if (hasOutcome) return true

    if (pick.market_type === "h2h" && (pickLower === "home" || pickLower === "away")) return true
    if (pick.market_type === "spreads" && (pickLower === "home" || pickLower === "away")) return true
    if (pick.market_type === "totals" && (pickLower === "over" || pickLower === "under")) return true
    if (pickLower === homeLower || pickLower === awayLower) return true

    return false
  })
}
