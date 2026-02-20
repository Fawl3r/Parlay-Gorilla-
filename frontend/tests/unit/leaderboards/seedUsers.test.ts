import { describe, expect, it } from "vitest"
import {
  buildLeaderboardRows,
  getSeedUsers,
  SEED_TARGET_COUNT,
} from "@/lib/leaderboards/seedUsers"

describe("seedUsers", () => {
  it("SEED_TARGET_COUNT is 10", () => {
    expect(SEED_TARGET_COUNT).toBe(10)
  })

  it("getSeedUsers returns 10 entries per kind", () => {
    expect(getSeedUsers("verified")).toHaveLength(10)
    expect(getSeedUsers("power")).toHaveLength(10)
    expect(getSeedUsers("arcade")).toHaveLength(10)
  })

  it("seed entries have isSeed true and plausible display names", () => {
    const verified = getSeedUsers("verified") as { isSeed?: boolean; username: string }[]
    expect(verified.every((r) => r.isSeed === true)).toBe(true)
    expect(verified[0].username).toBe("GridIronGorilla")
  })

  describe("buildLeaderboardRows", () => {
    it("with 0 real entries returns exactly SEED_TARGET_COUNT seed rows", () => {
      const combined = buildLeaderboardRows("verified", [])
      expect(combined).toHaveLength(SEED_TARGET_COUNT)
      expect(combined.every((r) => (r as { isSeed?: boolean }).isSeed)).toBe(true)
      expect(combined.map((r) => r.rank)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    })

    it("with 3 real entries returns 3 real first then 7 seeds", () => {
      const real = [
        { rank: 1, username: "Alice", verified_wins: 5, win_rate: 0.5 },
        { rank: 2, username: "Bob", verified_wins: 3, win_rate: 0.4 },
        { rank: 3, username: "Carol", verified_wins: 2, win_rate: 0.3 },
      ]
      const combined = buildLeaderboardRows("verified", real)
      expect(combined).toHaveLength(10)
      expect(combined[0].username).toBe("Alice")
      expect(combined[1].username).toBe("Bob")
      expect(combined[2].username).toBe("Carol")
      expect((combined[3] as { isSeed?: boolean }).isSeed).toBe(true)
      expect(combined.map((r) => r.rank)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    })

    it("with 10+ real entries returns only real rows, no seeds", () => {
      const real = Array.from({ length: 12 }, (_, i) => ({
        rank: i + 1,
        username: `User${i + 1}`,
        verified_wins: 10 - i,
        win_rate: 0.5,
      }))
      const combined = buildLeaderboardRows("verified", real)
      expect(combined).toHaveLength(12)
      expect(combined.every((r) => !(r as { isSeed?: boolean }).isSeed)).toBe(true)
      expect(combined[0].username).toBe("User1")
      expect(combined[11].username).toBe("User12")
    })

    it("real users always sort above seed users", () => {
      const real = [{ rank: 1, username: "OnlyReal", verified_wins: 1, win_rate: 0.2 }]
      const combined = buildLeaderboardRows("verified", real)
      const first = combined[0]
      const rest = combined.slice(1)
      expect(first.username).toBe("OnlyReal")
      expect((first as { isSeed?: boolean }).isSeed).not.toBe(true)
      expect(rest.every((r) => (r as { isSeed?: boolean }).isSeed)).toBe(true)
    })
  })
})
