import React from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it } from "vitest"

import { UgieKeyPlayers } from "@/components/analysis/detail/UgieKeyPlayers"

describe("UgieKeyPlayers (SSR smoke)", () => {
  it("renders 'Last refreshed:' when updatedAt is present", () => {
    const keyPlayers = {
      status: "limited" as const,
      reason: "roster_only_no_stats",
      homePlayers: [
        {
          name: "Home QB",
          team: "home" as const,
          role: "QB",
          impact: "High" as const,
          why: "Passing efficiency.",
          confidence: 0.7,
        },
      ],
      awayPlayers: [
        {
          name: "Away WR",
          team: "away" as const,
          role: "WR",
          impact: "Medium" as const,
          why: "Usage and red-zone.",
          confidence: 0.65,
        },
      ],
      verifiedLabel: "Verified current rosters",
      limitedNote: "Based on current rosters.",
      showRosterVerifiedNote: false,
      updatedAt: "2025-01-15T12:00:00Z",
    }
    const html = renderToStaticMarkup(
      <UgieKeyPlayers keyPlayers={keyPlayers} homeTeamName="Home" awayTeamName="Away" />
    )
    expect(html).toContain("Last refreshed:")
    expect(html).toContain("Jan 15, 2025 12:00 UTC")
  })

  it("does not render 'Last refreshed:' when updatedAt is absent", () => {
    const keyPlayers = {
      status: "limited" as const,
      reason: "roster_only_no_stats",
      homePlayers: [
        {
          name: "Home QB",
          team: "home" as const,
          role: "QB",
          impact: "High" as const,
          why: "Passing efficiency.",
          confidence: 0.7,
        },
      ],
      awayPlayers: [],
      verifiedLabel: "Verified current rosters",
      limitedNote: undefined,
      showRosterVerifiedNote: false,
      updatedAt: undefined,
    }
    const html = renderToStaticMarkup(
      <UgieKeyPlayers keyPlayers={keyPlayers} homeTeamName="Home" awayTeamName="Away" />
    )
    expect(html).not.toContain("Last refreshed:")
  })
})
