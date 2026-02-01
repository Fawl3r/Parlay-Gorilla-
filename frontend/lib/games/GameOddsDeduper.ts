/**
 * Odds-preference deduplication for Games list.
 * Deduplicates by matchup + 5-minute bucket and prefers the odds-backed game when duplicates exist.
 */

import type { GameResponse } from "@/lib/api"
import { buildDedupeKey, isGameSane } from "@/lib/games/GameDeduper"

export type DedupeGamesPreferOddsResult = {
  games: GameResponse[]
  /** Dedupe keys where we kept the odds-backed game (for "Odds just posted" highlight). */
  oddsPreferredKeys: Set<string>
}

/**
 * True if the game has a usable h2h (moneyline) market with at least two odds.
 */
export function hasUsableOdds(game: GameResponse): boolean {
  return (
    game.markets?.some(
      (m) => m.market_type === "h2h" && Array.isArray(m.odds) && m.odds.length >= 2
    ) ?? false
  )
}

function isDev(): boolean {
  return typeof process !== "undefined" && process.env.NODE_ENV === "development"
}

/**
 * Deduplicate games by matchup + 5-minute start-time bucket.
 * When duplicates exist, prefer the game that has usable odds.
 * Drops malformed games (sanity check).
 * In development, logs dedupe_reason counts (schedule_only_dropped, odds_preferred).
 */
export function dedupeGamesPreferOdds(games: GameResponse[]): DedupeGamesPreferOddsResult {
  const map = new Map<string, GameResponse>()
  const oddsPreferredKeys = new Set<string>()
  let scheduleOnlyDropped = 0
  let oddsPreferred = 0

  for (const game of games) {
    if (!isGameSane(game)) continue

    const key = buildDedupeKey(game)
    const existing = map.get(key)

    if (!existing) {
      map.set(key, game)
      continue
    }

    const existingHasOdds = hasUsableOdds(existing)
    const currentHasOdds = hasUsableOdds(game)

    if (!existingHasOdds && currentHasOdds) {
      map.set(key, game)
      oddsPreferredKeys.add(key)
      oddsPreferred += 1
    } else if (existingHasOdds && !currentHasOdds) {
      scheduleOnlyDropped += 1
    }
  }

  if (isDev() && (scheduleOnlyDropped > 0 || oddsPreferred > 0)) {
    console.log("[dedupe_reason]", { schedule_only_dropped: scheduleOnlyDropped, odds_preferred: oddsPreferred })
  }

  return { games: Array.from(map.values()), oddsPreferredKeys }
}
