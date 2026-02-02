import { describe, expect, it } from "vitest"

import {
  buildTemplateSlip,
  getRequiredCount,
} from "@/lib/custom-parlay/templateEngine"
import type { GameResponse } from "@/lib/api"

function makeOdds(outcome: string, price: string, decimal_price: number = 2): { id: string; outcome: string; price: string; decimal_price: number; implied_prob: number; created_at: string } {
  return {
    id: `o-${outcome}-${price}`,
    outcome,
    price,
    decimal_price,
    implied_prob: 1 / decimal_price,
    created_at: "",
  }
}

function makeGame(
  id: string,
  home: string,
  away: string,
  opts: { h2h?: boolean; spreads?: boolean; totals?: boolean } = { h2h: true }
): GameResponse {
  const markets: GameResponse["markets"] = []
  if (opts.h2h !== false) {
    markets.push({
      id: `m-${id}-h2h`,
      market_type: "h2h",
      book: "fd",
      odds: [
        makeOdds(home, "+120", 2.2),
        makeOdds(away, "-140", 1.71),
      ],
    })
  }
  if (opts.spreads) {
    markets.push({
      id: `m-${id}-spreads`,
      market_type: "spreads",
      book: "fd",
      odds: [
        makeOdds(`${home} -3.5`, "-110", 1.91),
        makeOdds(`${away} +3.5`, "-110", 1.91),
      ],
    })
  }
  if (opts.totals) {
    markets.push({
      id: `m-${id}-totals`,
      market_type: "totals",
      book: "fd",
      odds: [
        makeOdds("Over 45.5", "-110", 1.91),
        makeOdds("Under 45.5", "-110", 1.91),
      ],
    })
  }
  return {
    id,
    external_game_id: `ext-${id}`,
    sport: "nfl",
    home_team: home,
    away_team: away,
    start_time: "2025-02-01T18:30:00Z",
    status: "scheduled",
    markets,
  }
}

describe("templateEngine", () => {
  describe("getRequiredCount", () => {
    it("returns 2 for safer_2", () => {
      expect(getRequiredCount("safer_2")).toBe(2)
    })
    it("returns 3 for solid_3", () => {
      expect(getRequiredCount("solid_3")).toBe(3)
    })
    it("returns 4 for longshot_4", () => {
      expect(getRequiredCount("longshot_4")).toBe(4)
    })
  })

  describe("buildTemplateSlip", () => {
    it("safer_2 returns <= 2 picks and no duplicate games", () => {
      const games = [
        makeGame("g1", "Chiefs", "Bills"),
        makeGame("g2", "Cowboys", "Eagles"),
        makeGame("g3", "Ravens", "Dolphins"),
      ]
      const picks = buildTemplateSlip("safer_2", games, {
        maxPicks: 20,
        selectedSport: "nfl",
      })
      expect(picks.length).toBeLessThanOrEqual(2)
      const gameIds = new Set(picks.map((p) => p.game_id))
      expect(gameIds.size).toBe(picks.length)
    })

    it("partial behavior returns fewer picks without throwing", () => {
      const games = [makeGame("g1", "Chiefs", "Bills")]
      const picks = buildTemplateSlip("solid_3", games, {
        maxPicks: 20,
        selectedSport: "nfl",
      })
      expect(picks.length).toBeLessThanOrEqual(3)
      expect(picks.length).toBe(1)
    })

    it("longshot_4 never duplicates a game", () => {
      const games = [
        makeGame("g1", "Chiefs", "Bills"),
        makeGame("g2", "Cowboys", "Eagles"),
        makeGame("g3", "Ravens", "Dolphins"),
        makeGame("g4", "49ers", "Packers"),
        makeGame("g5", "Bengals", "Browns"),
      ]
      const picks = buildTemplateSlip("longshot_4", games, {
        maxPicks: 20,
        selectedSport: "nfl",
      })
      const gameIds = picks.map((p) => p.game_id)
      const unique = new Set(gameIds)
      expect(unique.size).toBe(gameIds.length)
    })

    it("returns empty when no games have valid markets", () => {
      const games = [
        makeGame("g1", "Chiefs", "Bills", { h2h: false, spreads: false, totals: false }),
      ]
      const picks = buildTemplateSlip("safer_2", games, {
        maxPicks: 20,
        selectedSport: "nfl",
      })
      expect(picks).toHaveLength(0)
    })
  })
})
