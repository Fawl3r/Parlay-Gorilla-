import { describe, expect, it } from "vitest"

import { SportsUiPolicy } from "@/lib/sports/SportsUiPolicy"

describe("SportsUiPolicy", () => {
  it("filters hidden sports from the list", () => {
    const policy = SportsUiPolicy.default()
    const visible = policy.filterVisible([
      { slug: "nfl" },
      { slug: "ucl" },
      { slug: "boxing" },
    ])
    expect(visible.map((s) => s.slug)).toEqual(["nfl", "boxing"])
  })

  it("forces UFC/Boxing to Coming Soon and not available", () => {
    const policy = SportsUiPolicy.default()
    const ufc = policy.resolveAvailability({ slug: "ufc", in_season: true, status_label: "In season" })
    const boxing = policy.resolveAvailability({ slug: "boxing" })

    expect(ufc.isAvailable).toBe(false)
    expect(ufc.isComingSoon).toBe(true)
    expect(ufc.statusLabel).toBe("Coming Soon")

    expect(boxing.isAvailable).toBe(false)
    expect(boxing.isComingSoon).toBe(true)
    expect(boxing.statusLabel).toBe("Coming Soon")
  })

  it("uses backend status_label when present for non-coming-soon sports", () => {
    const policy = SportsUiPolicy.default()
    const sport = policy.resolveAvailability({ slug: "mlb", in_season: false, status_label: "Not in season" })
    expect(sport.isAvailable).toBe(false)
    expect(sport.isComingSoon).toBe(false)
    expect(sport.statusLabel).toBe("Not in season")
  })
})


