import type {
  VerifiedWinnersEntry,
  AiPowerUsersEntry,
  ArcadePointsEntry,
} from "@/lib/leaderboards-api"

/** Number of rows to fill with seed entries when real entries are below this. */
export const SEED_TARGET_COUNT = 10

const ENABLE_SEEDS =
  typeof process !== "undefined" &&
  (process.env.NEXT_PUBLIC_ENABLE_LEADERBOARD_SEEDS ?? "true") === "true"

/** Row that may be a seed (for merge logic). */
export type VerifiedRow = VerifiedWinnersEntry & { isSeed?: boolean }
export type PowerRow = AiPowerUsersEntry & { isSeed?: boolean }
export type ArcadeRow = ArcadePointsEntry & { isSeed?: boolean }

/** Deterministic seed entries for Verified Winners. */
const SEED_VERIFIED: VerifiedRow[] = [
  { rank: 1, username: "GridIronGorilla", verified_wins: 3, win_rate: 0.6, last_win_at: "2025-02-15T18:00:00Z", isSeed: true },
  { rank: 2, username: "SlipSniper", verified_wins: 2, win_rate: 0.5, last_win_at: "2025-02-14T12:00:00Z", isSeed: true },
  { rank: 3, username: "OddsOracle", verified_wins: 2, win_rate: 0.4, last_win_at: "2025-02-12T20:00:00Z", isSeed: true },
  { rank: 4, username: "ParlayPilot", verified_wins: 1, win_rate: 0.33, last_win_at: "2025-02-10T14:00:00Z", isSeed: true },
  { rank: 5, username: "LegBuilder", verified_wins: 1, win_rate: 0.25, last_win_at: "2025-02-08T09:00:00Z", isSeed: true },
  { rank: 6, username: "CashoutKing", verified_wins: 1, win_rate: 0.2, last_win_at: "2025-02-05T16:00:00Z", isSeed: true },
  { rank: 7, username: "TeaserPro", verified_wins: 1, win_rate: 0.18, last_win_at: "2025-02-02T11:00:00Z", isSeed: true },
  { rank: 8, username: "RoundRobinRookie", verified_wins: 1, win_rate: 0.15, last_win_at: "2025-01-30T19:00:00Z", isSeed: true },
  { rank: 9, username: "SpreadSheet", verified_wins: 1, win_rate: 0.12, last_win_at: "2025-01-28T08:00:00Z", isSeed: true },
  { rank: 10, username: "UnderdogUprising", verified_wins: 1, win_rate: 0.1, last_win_at: "2025-01-25T22:00:00Z", isSeed: true },
]

/** Deterministic seed entries for AI Power Users. */
const SEED_POWER: PowerRow[] = [
  { rank: 1, username: "GridIronGorilla", ai_parlays_generated: 42, last_generated_at: "2025-02-18T14:00:00Z", isSeed: true },
  { rank: 2, username: "SlipSniper", ai_parlays_generated: 38, last_generated_at: "2025-02-18T10:00:00Z", isSeed: true },
  { rank: 3, username: "OddsOracle", ai_parlays_generated: 31, last_generated_at: "2025-02-17T20:00:00Z", isSeed: true },
  { rank: 4, username: "ParlayPilot", ai_parlays_generated: 28, last_generated_at: "2025-02-17T12:00:00Z", isSeed: true },
  { rank: 5, username: "LegBuilder", ai_parlays_generated: 24, last_generated_at: "2025-02-16T18:00:00Z", isSeed: true },
  { rank: 6, username: "CashoutKing", ai_parlays_generated: 19, last_generated_at: "2025-02-16T09:00:00Z", isSeed: true },
  { rank: 7, username: "TeaserPro", ai_parlays_generated: 15, last_generated_at: "2025-02-15T16:00:00Z", isSeed: true },
  { rank: 8, username: "RoundRobinRookie", ai_parlays_generated: 12, last_generated_at: "2025-02-14T11:00:00Z", isSeed: true },
  { rank: 9, username: "SpreadSheet", ai_parlays_generated: 9, last_generated_at: "2025-02-13T08:00:00Z", isSeed: true },
  { rank: 10, username: "UnderdogUprising", ai_parlays_generated: 6, last_generated_at: "2025-02-12T20:00:00Z", isSeed: true },
]

/** Deterministic seed entries for Arcade Points. */
const SEED_ARCADE: ArcadeRow[] = [
  { rank: 1, username: "GridIronGorilla", total_points: 440, total_qualifying_wins: 2, last_win_at: "2025-02-15T18:00:00Z", isSeed: true },
  { rank: 2, username: "SlipSniper", total_points: 280, total_qualifying_wins: 1, last_win_at: "2025-02-14T12:00:00Z", isSeed: true },
  { rank: 3, username: "OddsOracle", total_points: 200, total_qualifying_wins: 1, last_win_at: "2025-02-12T20:00:00Z", isSeed: true },
  { rank: 4, username: "ParlayPilot", total_points: 140, total_qualifying_wins: 1, last_win_at: "2025-02-10T14:00:00Z", isSeed: true },
  { rank: 5, username: "LegBuilder", total_points: 100, total_qualifying_wins: 1, last_win_at: "2025-02-08T09:00:00Z", isSeed: true },
  { rank: 6, username: "CashoutKing", total_points: 100, total_qualifying_wins: 1, last_win_at: "2025-02-05T16:00:00Z", isSeed: true },
  { rank: 7, username: "TeaserPro", total_points: 100, total_qualifying_wins: 1, last_win_at: "2025-02-02T11:00:00Z", isSeed: true },
  { rank: 8, username: "RoundRobinRookie", total_points: 100, total_qualifying_wins: 1, last_win_at: "2025-01-30T19:00:00Z", isSeed: true },
  { rank: 9, username: "SpreadSheet", total_points: 100, total_qualifying_wins: 1, last_win_at: "2025-01-28T08:00:00Z", isSeed: true },
  { rank: 10, username: "UnderdogUprising", total_points: 100, total_qualifying_wins: 1, last_win_at: "2025-01-25T22:00:00Z", isSeed: true },
]

export function getSeedUsers(
  kind: "verified" | "power" | "arcade"
): VerifiedRow[] | PowerRow[] | ArcadeRow[] {
  if (!ENABLE_SEEDS) return []
  switch (kind) {
    case "verified":
      return [...SEED_VERIFIED]
    case "power":
      return [...SEED_POWER]
    case "arcade":
      return [...SEED_ARCADE]
  }
}

/**
 * Merges real leaderboard rows with seed fillers so the list never looks empty.
 * Real users always appear first; seeds fill up to SEED_TARGET_COUNT total rows.
 */
export function buildLeaderboardRows<T extends { isSeed?: boolean; rank: number }>(
  kind: "verified" | "power" | "arcade",
  realRows: T[]
): T[] {
  const real = realRows.filter((r) => !r.isSeed)
  if (!ENABLE_SEEDS) return real

  const seeds = getSeedUsers(kind) as T[]
  const needed = Math.max(0, SEED_TARGET_COUNT - real.length)
  const fillers = seeds.slice(0, needed)
  const combined = [...real, ...fillers]

  return combined.map((row, index) => ({ ...row, rank: index + 1 }))
}
