import { describe, expect, it } from "vitest"

import type { GameResponse } from "@/lib/api"
import { hasUsableOdds, dedupeGamesPreferOdds } from "@/lib/games/GameOddsDeduper"

function game(overrides: Partial<GameResponse> = {}): GameResponse {
  return {
    id: "g1",
    external_game_id: "espn:nba:1",
    sport: "NBA",
    home_team: "Lakers",
    away_team: "Celtics",
    start_time: "2025-02-01T19:00:00Z",
    status: "scheduled",
    markets: [],
    ...overrides,
  }
}

describe("GameListDeduplication", () => {
  describe("hasUsableOdds", () => {
    it("returns false when markets is empty", () => {
      expect(hasUsableOdds(game({ markets: [] }))).toBe(false)
    })

    it("returns false when no h2h market", () => {
      expect(
        hasUsableOdds(
          game({
            markets: [
              {
                id: "m1",
                market_type: "spreads",
                book: "fanduel",
                odds: [
                  { id: "o1", outcome: "Lakers", price: "-3.5", decimal_price: 1.9, implied_prob: 0.5, created_at: "" },
                  { id: "o2", outcome: "Celtics", price: "+3.5", decimal_price: 1.9, implied_prob: 0.5, created_at: "" },
                ],
              },
            ],
          })
        )
      ).toBe(false)
    })

    it("returns false when h2h has fewer than 2 odds", () => {
      expect(
        hasUsableOdds(
          game({
            markets: [
              {
                id: "m1",
                market_type: "h2h",
                book: "fanduel",
                odds: [{ id: "o1", outcome: "Lakers", price: "-150", decimal_price: 1.67, implied_prob: 0.6, created_at: "" }],
              },
            ],
          })
        )
      ).toBe(false)
    })

    it("returns true when h2h market has at least 2 odds", () => {
      expect(
        hasUsableOdds(
          game({
            markets: [
              {
                id: "m1",
                market_type: "h2h",
                book: "fanduel",
                odds: [
                  { id: "o1", outcome: "Lakers", price: "-150", decimal_price: 1.67, implied_prob: 0.6, created_at: "" },
                  { id: "o2", outcome: "Celtics", price: "+120", decimal_price: 2.2, implied_prob: 0.4, created_at: "" },
                ],
              },
            ],
          })
        )
      ).toBe(true)
    })
  })

  describe("dedupeGamesPreferOdds", () => {
    it("same matchup within 5 minutes: only one rendered, odds-backed wins", () => {
      const scheduleOnly = game({
        id: "schedule-1",
        start_time: "2025-02-01T19:00:00Z",
        markets: [],
      })
      const oddsBacked = game({
        id: "odds-1",
        start_time: "2025-02-01T19:02:00Z",
        markets: [
          {
            id: "m1",
            market_type: "h2h",
            book: "fanduel",
            odds: [
              { id: "o1", outcome: "Lakers", price: "-150", decimal_price: 1.67, implied_prob: 0.6, created_at: "" },
              { id: "o2", outcome: "Celtics", price: "+120", decimal_price: 2.2, implied_prob: 0.4, created_at: "" },
            ],
          },
        ],
      })

      const result = dedupeGamesPreferOdds([scheduleOnly, oddsBacked])
      expect(result).toHaveLength(1)
      expect(result[0]!.id).toBe("odds-1")
      expect(hasUsableOdds(result[0]!)).toBe(true)
    })

    it("same matchup within 5 minutes: order does not matter, odds-backed still wins", () => {
      const oddsBacked = game({
        id: "odds-1",
        start_time: "2025-02-01T19:02:00Z",
        markets: [
          {
            id: "m1",
            market_type: "h2h",
            book: "fanduel",
            odds: [
              { id: "o1", outcome: "Lakers", price: "-150", decimal_price: 1.67, implied_prob: 0.6, created_at: "" },
              { id: "o2", outcome: "Celtics", price: "+120", decimal_price: 2.2, implied_prob: 0.4, created_at: "" },
            ],
          },
        ],
      })
      const scheduleOnly = game({
        id: "schedule-1",
        start_time: "2025-02-01T19:00:00Z",
        markets: [],
      })

      const result = dedupeGamesPreferOdds([oddsBacked, scheduleOnly])
      expect(result).toHaveLength(1)
      expect(result[0]!.id).toBe("odds-1")
    })

    it("only schedule-only exists: it is kept", () => {
      const scheduleOnly = game({
        id: "schedule-1",
        start_time: "2025-02-01T19:00:00Z",
        markets: [],
      })

      const result = dedupeGamesPreferOdds([scheduleOnly])
      expect(result).toHaveLength(1)
      expect(result[0]!.id).toBe("schedule-1")
    })

    it("malformed games are dropped", () => {
      const sane = game({ id: "sane", home_team: "Lakers", away_team: "Celtics", start_time: "2025-02-01T19:00:00Z", status: "scheduled" })
      const noTeams = game({ id: "bad1", home_team: "", away_team: "" })
      const sameTeams = game({ id: "bad2", home_team: "Lakers", away_team: "Lakers" })
      const noStartTime = game({ id: "bad3", start_time: "" })
      const noStatus = game({ id: "bad4", status: "" })

      const result = dedupeGamesPreferOdds([sane, noTeams, sameTeams, noStartTime, noStatus])
      expect(result).toHaveLength(1)
      expect(result[0]!.id).toBe("sane")
    })

    it("different matchups or >5 min apart are not collapsed", () => {
      const g1 = game({ id: "a", start_time: "2025-02-01T19:00:00Z", home_team: "Lakers", away_team: "Celtics" })
      const g2 = game({ id: "b", start_time: "2025-02-01T19:00:00Z", home_team: "Heat", away_team: "Bucks" })
      const g3 = game({ id: "c", start_time: "2025-02-01T19:06:00Z", home_team: "Lakers", away_team: "Celtics" })

      const result = dedupeGamesPreferOdds([g1, g2, g3])
      expect(result).toHaveLength(3)
    })
  })
})
