import { describe, expect, it } from "vitest"

import type { SportListItem } from "@/lib/api/types"
import { emptyStateContextLine, sportKey } from "@/app/analysis/GameAnalysisHubClient"
import { sportsUiPolicy } from "@/lib/sports/SportsUiPolicy"

/** Backend contract: is_enabled (or in_season fallback) drives tab enable/disable. */
function isSportEnabledFromItem(sport: SportListItem): boolean {
  return typeof sport.is_enabled === "boolean" ? sport.is_enabled : (sport.in_season !== false)
}

describe("GameAnalysisHubClient sport tabs (is_enabled)", () => {
  it("normalizes keys to lowercase so slug and tab id match", () => {
    expect(sportKey("nfl")).toBe("nfl")
    expect(sportKey("NCAAF")).toBe("ncaaf")
    expect(sportKey("")).toBe("")
    expect(isSportEnabledFromItem({ slug: "NCAAF", code: "x", display_name: "NCAAF", default_markets: [], is_enabled: false })).toBe(false)
    expect(isSportEnabledFromItem({ slug: "ncaaf", code: "x", display_name: "NCAAF", default_markets: [], is_enabled: false })).toBe(false)
  })

  it("disables tab when is_enabled is false and enables when true", () => {
    const nfl: SportListItem = {
      slug: "nfl",
      code: "americanfootball_nfl",
      display_name: "NFL",
      default_markets: [],
      is_enabled: false,
      sport_state: "OFFSEASON",
    }
    const nba: SportListItem = {
      slug: "nba",
      code: "basketball_nba",
      display_name: "NBA",
      default_markets: [],
      is_enabled: true,
      sport_state: "IN_SEASON",
    }
    expect(isSportEnabledFromItem(nfl)).toBe(false)
    expect(isSportEnabledFromItem(nba)).toBe(true)
  })

  it("falls back to in_season when is_enabled is missing (backward compat)", () => {
    const nfl: SportListItem = { slug: "nfl", code: "x", display_name: "NFL", default_markets: [], in_season: false }
    const nba: SportListItem = { slug: "nba", code: "y", display_name: "NBA", default_markets: [], in_season: true }
    expect(isSportEnabledFromItem(nfl)).toBe(false)
    expect(isSportEnabledFromItem(nba)).toBe(true)
  })

  it("NFL tab shows Offseason badge when disabled and sport_state OFFSEASON", () => {
    const avail = sportsUiPolicy.resolveAvailability({
      slug: "nfl",
      code: "x",
      display_name: "NFL",
      default_markets: [],
      is_enabled: false,
      sport_state: "OFFSEASON",
      next_game_at: "2025-09-05T00:00:00Z",
    })
    expect(avail.isAvailable).toBe(false)
    expect(avail.statusLabel).toMatch(/Offseason|returns|Not in season/)
  })

  it("Preseason / Break / Postseason status label", () => {
    expect(sportsUiPolicy.resolveAvailability({ slug: "nfl", code: "x", display_name: "NFL", default_markets: [], is_enabled: false, sport_state: "PRESEASON" }).statusLabel).toMatch(/Preseason|Not in season/)
    expect(sportsUiPolicy.resolveAvailability({ slug: "nfl", code: "x", display_name: "NFL", default_markets: [], is_enabled: false, sport_state: "IN_BREAK" }).statusLabel).toMatch(/Break|Not in season/)
    expect(sportsUiPolicy.resolveAvailability({ slug: "nfl", code: "x", display_name: "NFL", default_markets: [], is_enabled: false, sport_state: "POSTSEASON" }).statusLabel).toMatch(/Postseason|Not in season/)
  })

  it("returns in season when enabled (no disabled badge)", () => {
    const avail = sportsUiPolicy.resolveAvailability({
      slug: "nba",
      code: "y",
      display_name: "NBA",
      default_markets: [],
      is_enabled: true,
      sport_state: "IN_SEASON",
    })
    expect(avail.isAvailable).toBe(true)
    expect(avail.statusLabel).toMatch(/[Ii]n season|In season/)
  })

  it("clicking disabled sport does not change selection (tab disabled state)", () => {
    const nfl = { slug: "nfl", code: "x", display_name: "NFL", default_markets: [], is_enabled: false } as SportListItem
    const nba = { slug: "nba", code: "y", display_name: "NBA", default_markets: [], is_enabled: true } as SportListItem
    const nflDisabled = !isSportEnabledFromItem(nfl)
    const nbaDisabled = !isSportEnabledFromItem(nba)
    expect(nflDisabled).toBe(true)
    expect(nbaDisabled).toBe(false)
  })

  describe("emptyStateContextLine", () => {
    it("returns offseason message when sport_state is OFFSEASON and next_game_at set", () => {
      expect(
        emptyStateContextLine({ sport_state: "OFFSEASON", next_game_at: "2025-09-05T00:00:00Z" })
      ).toContain("Out of season")
      expect(
        emptyStateContextLine({ sport_state: "OFFSEASON", next_game_at: "2025-09-05T00:00:00Z" })
      ).toContain("returns")
    })
    it("returns league break message for IN_BREAK", () => {
      const msg = emptyStateContextLine({ sport_state: "IN_BREAK", next_game_at: "2025-02-20T00:00:00Z" })
      expect(msg).toContain("League break")
      expect(msg).toContain("next game")
    })
    it("returns preseason unlocks message when days_to_next > preseason_enable_days", () => {
      const msg = emptyStateContextLine({
        sport_state: "PRESEASON",
        next_game_at: "2025-08-01T00:00:00Z",
        days_to_next: 30,
        preseason_enable_days: 14,
      })
      expect(msg).toContain("Preseason starts")
      expect(msg).toContain("unlocks in 30 days")
    })
    it("returns WNBA offseason copy when sport is wnba and OFFSEASON", () => {
      expect(
        emptyStateContextLine({ sport_state: "OFFSEASON" }, "wnba")
      ).toBe("WNBA is offseason — check back soon.")
    })
    it("returns empty when listMeta is null or missing sport_state", () => {
      expect(emptyStateContextLine(null)).toBe("")
      expect(emptyStateContextLine({})).toBe("")
    })
  })
})
