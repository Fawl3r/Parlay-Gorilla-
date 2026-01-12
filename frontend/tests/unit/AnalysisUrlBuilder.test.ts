import { describe, expect, it } from "vitest"

import { buildAnalysisUrl } from "@/lib/routing/AnalysisUrlBuilder"

describe("buildAnalysisUrl", () => {
  it("builds NFL week-based slugs when week is known", () => {
    const url = buildAnalysisUrl(
      "nfl",
      "Chicago Bears",
      "Green Bay Packers",
      "2025-12-07T20:00:00Z",
      14
    )

    expect(url).toBe("/analysis/nfl/chicago-bears-vs-green-bay-packers-week-14-2025")
  })

  it("computes NFL week when week is not provided", () => {
    const url = buildAnalysisUrl(
      "nfl",
      "Dallas Cowboys",
      "Philadelphia Eagles",
      "2025-09-15T20:00:00Z",
      null
    )

    expect(url).toBe("/analysis/nfl/dallas-cowboys-vs-philadelphia-eagles-week-2-2025")
  })

  it("falls back to NFL date slugs when week cannot be computed (preseason/postseason)", () => {
    const url = buildAnalysisUrl(
      "nfl",
      "Carolina Panthers",
      "Tampa Bay Buccaneers",
      "2026-08-20T20:00:00Z",
      null
    )

    expect(url).toBe("/analysis/nfl/carolina-panthers-vs-tampa-bay-buccaneers-2026-08-20")
  })

  it("builds date slugs for non-NFL sports", () => {
    const url = buildAnalysisUrl(
      "nba",
      "Los Angeles Lakers",
      "Boston Celtics",
      "2025-01-15T20:00:00Z",
      null
    )

    expect(url).toBe("/analysis/nba/los-angeles-lakers-vs-boston-celtics-2025-01-15")
  })
})





