/**
 * Deduplication and sanity checks for game feed items.
 * Prevents duplicate games (same matchup in same 5-min bucket) and drops malformed data.
 */

import type { GameFeedResponse } from "@/lib/api"

const FIVE_MIN_MS = 5 * 60 * 1000

/**
 * Build a stable dedupe key: league + home_team + away_team + 5-minute start_time bucket.
 * Same matchup within ±5 minutes collapses to one.
 */
export function buildDedupeKey(game: GameFeedResponse): string {
  const bucket = getStartTimeBucket(game.start_time)
  const league = (game.sport || "").trim()
  const home = (game.home_team || "").trim()
  const away = (game.away_team || "").trim()
  return `${league}|${home}|${away}|${bucket}`
}

/**
 * 5-minute bucket from start_time (floor of ms / (5 * 60 * 1000)).
 * Invalid/missing start_time returns 0.
 */
export function getStartTimeBucket(startTimeIso: string): number {
  if (!startTimeIso || typeof startTimeIso !== "string") return 0
  const ms = new Date(startTimeIso.trim()).getTime()
  if (!Number.isFinite(ms)) return 0
  return Math.floor(ms / FIVE_MIN_MS)
}

/**
 * Sanity checks: drop games that would break the feed.
 * Fail closed (do not render).
 */
export function isGameSane(game: GameFeedResponse): boolean {
  const home = (game.home_team ?? "").toString().trim()
  const away = (game.away_team ?? "").toString().trim()
  if (!home && !away) return false
  if (home === away) return false
  if (!game.start_time || typeof game.start_time !== "string") return false
  const t = new Date(game.start_time.trim()).getTime()
  if (!Number.isFinite(t)) return false
  if (!game.status || typeof game.status !== "string") return false
  return true
}

/**
 * Dedupe by key: keep first occurrence of each dedupe key.
 */
export function dedupeGames(games: GameFeedResponse[]): GameFeedResponse[] {
  const seen = new Set<string>()
  const out: GameFeedResponse[] = []
  for (const g of games) {
    const key = buildDedupeKey(g)
    if (seen.has(key)) continue
    seen.add(key)
    out.push(g)
  }
  return out
}

/**
 * Apply sanity filter: keep only games that pass isGameSane.
 */
export function filterSaneGames(games: GameFeedResponse[]): GameFeedResponse[] {
  return games.filter(isGameSane)
}
