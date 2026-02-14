import { describe, expect, it } from "vitest"

import type { SportListItem } from "@/lib/api/types"
import {
  buildAvailabilityBySport,
  availabilityBadgeText,
  emptyStateContextLine,
  sportKey,
  type SportAvailability,
} from "@/app/analysis/GameAnalysisHubClient"

describe("GameAnalysisHubClient sport tabs (is_enabled)", () => {
  it("normalizes keys to lowercase so slug and tab id match", () => {
    expect(sportKey("nfl")).toBe("nfl")
    expect(sportKey("NCAAF")).toBe("ncaaf")
    expect(sportKey("")).toBe("")
    const map = buildAvailabilityBySport([
      { slug: "NCAAF", code: "x", display_name: "NCAAF", default_markets: [], is_enabled: false },
    ])
    expect(map[sportKey("ncaaf")]?.isEnabled).toBe(false)
    expect(map[sportKey("NCAAF")]?.isEnabled).toBe(false)
  })

  it("disables tab when is_enabled is false and enables when true", () => {
    const sportsList: SportListItem[] = [
      {
        slug: "nfl",
        code: "americanfootball_nfl",
        display_name: "NFL",
        default_markets: [],
        is_enabled: false,
        sport_state: "OFFSEASON",
      },
      {
        slug: "nba",
        code: "basketball_nba",
        display_name: "NBA",
        default_markets: [],
        is_enabled: true,
        sport_state: "IN_SEASON",
      },
    ]
    const map = buildAvailabilityBySport(sportsList)
    expect(map.nfl?.isEnabled).toBe(false)
    expect(map.nba?.isEnabled).toBe(true)
  })

  it("falls back to in_season when is_enabled is missing (backward compat)", () => {
    const sportsList: SportListItem[] = [
      { slug: "nfl", code: "x", display_name: "NFL", default_markets: [], in_season: false },
      { slug: "nba", code: "y", display_name: "NBA", default_markets: [], in_season: true },
    ]
    const map = buildAvailabilityBySport(sportsList)
    expect(map.nfl?.isEnabled).toBe(false)
    expect(map.nba?.isEnabled).toBe(true)
  })

  it("NFL tab shows Offseason badge when disabled and sport_state OFFSEASON", () => {
    const meta: SportAvailability = {
      isEnabled: false,
      sportState: "OFFSEASON",
    }
    expect(availabilityBadgeText(meta)).toBe("Offseason")
  })

  it("Preseason / Break / Postseason badge text", () => {
    expect(availabilityBadgeText({ isEnabled: false, sportState: "PRESEASON" })).toBe("Preseason")
    expect(availabilityBadgeText({ isEnabled: false, sportState: "IN_BREAK" })).toBe("Break")
    expect(availabilityBadgeText({ isEnabled: false, sportState: "POSTSEASON" })).toBe("Postseason")
  })

  it("returns empty string when enabled (no badge)", () => {
    expect(availabilityBadgeText({ isEnabled: true, sportState: "IN_SEASON" })).toBe("")
    expect(availabilityBadgeText(undefined)).toBe("")
  })

  it("clicking disabled sport does not change selection (tab disabled state)", () => {
    const map = buildAvailabilityBySport([
      { slug: "nfl", code: "x", display_name: "NFL", default_markets: [], is_enabled: false },
      { slug: "nba", code: "y", display_name: "NBA", default_markets: [], is_enabled: true },
    ])
    const nflDisabled = !(map.nfl?.isEnabled ?? true)
    const nbaDisabled = !(map.nba?.isEnabled ?? true)
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
    it("returns empty when listMeta is null or missing sport_state", () => {
      expect(emptyStateContextLine(null)).toBe("")
      expect(emptyStateContextLine({})).toBe("")
    })
  })
})
