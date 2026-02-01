/**
 * Odds-preference deduplication for Games list.
 * Deduplicates by matchup + 5-minute bucket and prefers the odds-backed game when duplicates exist.
 */

import type { GameResponse } from "@/lib/api"
import { buildDedupeKey, isGameSane } from "@/lib/games/GameDeduper"

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

/**
 * Deduplicate games by matchup + 5-minute start-time bucket.
 * When duplicates exist, prefer the game that has usable odds.
 * Drops malformed games (sanity check).
 */
export function dedupeGamesPreferOdds(games: GameResponse[]): GameResponse[] {
  const map = new Map<string, GameResponse>()

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
    }
  }

  return Array.from(map.values())
}
