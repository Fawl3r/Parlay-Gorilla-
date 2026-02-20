import { describe, expect, it } from "vitest"

import {
  buildDedupeKey,
  getStartTimeBucket,
  isGameSane,
  dedupeGames,
  filterSaneGames,
} from "@/lib/games/GameDeduper"

function game(overrides: Partial<{
  id: string
  sport: string
  home_team: string
  away_team: string
  start_time: string
  status: string
  home_score: number | null
  away_score: number | null
  period: string | null
  clock: string | null
  is_stale: boolean
}> = {}) {
  return {
    id: "g1",
    sport: "NFL",
    home_team: "Chiefs",
    away_team: "Bills",
    start_time: "2025-02-01T18:30:00Z",
    status: "LIVE",
    home_score: 14,
    away_score: 10,
    period: "Q2",
    clock: "8:42",
    is_stale: false,
    ...overrides,
  }
}

describe("GameDeduper", () => {
  describe("getStartTimeBucket", () => {
    it("same time gives same 5-min bucket", () => {
      const t = "2025-02-01T18:30:00Z"
      expect(getStartTimeBucket(t)).toBe(getStartTimeBucket(t))
    })

    it("times within 5 minutes share same bucket", () => {
      const a = "2025-02-01T18:30:00Z"
      const b = "2025-02-01T18:32:00Z"
      const c = "2025-02-01T18:34:59.999Z"
      expect(getStartTimeBucket(a)).toBe(getStartTimeBucket(b))
      expect(getStartTimeBucket(a)).toBe(getStartTimeBucket(c))
    })

    it("times more than 5 minutes apart have different buckets", () => {
      const a = "2025-02-01T18:30:00Z"
      const b = "2025-02-01T18:36:00Z"
      expect(getStartTimeBucket(a)).not.toBe(getStartTimeBucket(b))
    })
  })

  describe("buildDedupeKey", () => {
    it("same matchup within ±5 minutes produces same key", () => {
      const g1 = game({ start_time: "2025-02-01T18:30:00Z" })
      const g2 = game({ start_time: "2025-02-01T18:32:00Z", id: "g2" })
      expect(buildDedupeKey(g1)).toBe(buildDedupeKey(g2))
    })

    it("different matchups produce different keys", () => {
      const g1 = game({ home_team: "Chiefs", away_team: "Bills" })
      const g2 = game({ home_team: "Ravens", away_team: "49ers" })
      expect(buildDedupeKey(g1)).not.toBe(buildDedupeKey(g2))
    })

    it("same matchup but >5 minutes apart produces different keys", () => {
      const g1 = game({ start_time: "2025-02-01T18:30:00Z" })
      const g2 = game({ start_time: "2025-02-01T18:36:00Z", id: "g2" })
      expect(buildDedupeKey(g1)).not.toBe(buildDedupeKey(g2))
    })

    it("swapped home/away produces same key (order-insensitive)", () => {
      const g1 = game({ home_team: "Chiefs", away_team: "Bills" })
      const g2 = game({ home_team: "Bills", away_team: "Chiefs", id: "g2" })
      expect(buildDedupeKey(g1)).toBe(buildDedupeKey(g2))
    })
  })

  describe("dedupeGames", () => {
    it("same matchup within ±5 minutes collapses to one", () => {
      const g1 = game({ id: "a", start_time: "2025-02-01T18:30:00Z" })
      const g2 = game({ id: "b", start_time: "2025-02-01T18:32:00Z" })
      const result = dedupeGames([g1, g2])
      expect(result).toHaveLength(1)
      expect(result[0]!.id).toBe("a")
    })

    it("different matchups or >5 min apart do not collapse", () => {
      const g1 = game({ id: "a", start_time: "2025-02-01T18:30:00Z" })
      const g2 = game({ id: "b", home_team: "Ravens", away_team: "49ers", start_time: "2025-02-01T19:00:00Z" })
      const g3 = game({ id: "c", start_time: "2025-02-01T18:36:00Z" })
      const result = dedupeGames([g1, g2, g3])
      expect(result).toHaveLength(3)
    })

    it("duplicate payload with swapped home/away collapses to one", () => {
      const g1 = game({ id: "a", home_team: "Chiefs", away_team: "Bills", start_time: "2025-02-01T18:30:00Z" })
      const g2 = game({ id: "b", home_team: "Bills", away_team: "Chiefs", start_time: "2025-02-01T18:32:00Z" })
      const result = dedupeGames([g1, g2])
      expect(result).toHaveLength(1)
    })
  })

  describe("isGameSane", () => {
    it("keeps valid game", () => {
      expect(isGameSane(game())).toBe(true)
    })

    it("drops game missing both team names", () => {
      expect(isGameSane(game({ home_team: "", away_team: "" }))).toBe(false)
    })

    it("drops game where home === away", () => {
      expect(isGameSane(game({ home_team: "Chiefs", away_team: "Chiefs" }))).toBe(false)
    })

    it("drops game with invalid or missing start_time", () => {
      expect(isGameSane(game({ start_time: "" }))).toBe(false)
      expect(isGameSane(game({ start_time: "not-a-date" }))).toBe(false)
    })

    it("drops game missing status", () => {
      expect(isGameSane(game({ status: "" }))).toBe(false)
    })
  })

  describe("filterSaneGames", () => {
    it("keeps only sane games", () => {
      const sane = game()
      const insane = game({ home_team: "", away_team: "" })
      const result = filterSaneGames([sane, insane])
      expect(result).toHaveLength(1)
      expect(result[0]).toEqual(sane)
    })
  })
})
