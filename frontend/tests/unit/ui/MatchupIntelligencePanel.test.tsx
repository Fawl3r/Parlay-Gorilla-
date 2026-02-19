import React from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it } from "vitest"

import { MatchupIntelligencePanel } from "@/components/analysis/detail/MatchupIntelligencePanel"
import type { AnalysisEnrichment } from "@/lib/api/types/analysis"

const baseEnrichment: AnalysisEnrichment = {
  sport: "nba",
  league: "NBA",
  season: "2024-2025",
  home_team: { name: "Lakers" },
  away_team: { name: "Celtics" },
  data_quality: { has_standings: true, has_team_stats: true, has_form: true, has_injuries: true },
}

describe("MatchupIntelligencePanel", () => {
  it("renders table rows when key_team_stats present", () => {
    const enrichment: AnalysisEnrichment = {
      ...baseEnrichment,
      key_team_stats: [
        { key: "points_for", label: "PPG", home_value: 112.5, away_value: 108.2 },
        { key: "points_against", label: "PAPG", home_value: 109.1, away_value: 105.0 },
      ],
    }
    const html = renderToStaticMarkup(<MatchupIntelligencePanel enrichment={enrichment} />)
    expect(html).toContain("PPG")
    expect(html).toContain("PAPG")
    expect(html).toContain("112.5")
    expect(html).toContain("108.2")
    expect(html).toContain("Stat")
  })

  it("omits rows when both home_value and away_value are null", () => {
    const enrichment: AnalysisEnrichment = {
      ...baseEnrichment,
      key_team_stats: [
        { key: "points_for", label: "PPG", home_value: 112.5, away_value: 108.2 },
        { key: "points_against", label: "PAPG", home_value: null, away_value: null },
      ],
    }
    const html = renderToStaticMarkup(<MatchupIntelligencePanel enrichment={enrichment} />)
    expect(html).toContain("PPG")
    expect(html).not.toContain("PAPG")
  })

  it("shows Last updated when as_of present", () => {
    const enrichment: AnalysisEnrichment = {
      ...baseEnrichment,
      as_of: new Date(Date.now() - 3600 * 1000).toISOString(),
    }
    const html = renderToStaticMarkup(<MatchupIntelligencePanel enrichment={enrichment} />)
    expect(html).toContain("Last updated")
  })

  it("does not show Last updated when as_of absent", () => {
    const enrichment: AnalysisEnrichment = { ...baseEnrichment }
    const html = renderToStaticMarkup(<MatchupIntelligencePanel enrichment={enrichment} />)
    expect(html).not.toContain("Last updated")
  })

  it("shows Limited data badge when data_quality.notes non-empty", () => {
    const enrichment: AnalysisEnrichment = {
      ...baseEnrichment,
      data_quality: {
        ...baseEnrichment.data_quality!,
        notes: ["Team ID not found: Some Team"],
      },
    }
    const html = renderToStaticMarkup(<MatchupIntelligencePanel enrichment={enrichment} />)
    expect(html).toContain("Limited data")
  })

  it("shows Limited data badge when any has_* is false", () => {
    const enrichment: AnalysisEnrichment = {
      ...baseEnrichment,
      data_quality: {
        has_standings: true,
        has_team_stats: false,
        has_form: true,
        has_injuries: false,
        notes: [],
      },
    }
    const html = renderToStaticMarkup(<MatchupIntelligencePanel enrichment={enrichment} />)
    expect(html).toContain("Limited data")
  })

  it("does not show Limited data badge when no notes and all has_* true", () => {
    const enrichment: AnalysisEnrichment = {
      ...baseEnrichment,
      data_quality: {
        has_standings: true,
        has_team_stats: true,
        has_form: true,
        has_injuries: true,
        notes: [],
      },
    }
    const html = renderToStaticMarkup(<MatchupIntelligencePanel enrichment={enrichment} />)
    expect(html).not.toContain("Limited data")
  })
})
