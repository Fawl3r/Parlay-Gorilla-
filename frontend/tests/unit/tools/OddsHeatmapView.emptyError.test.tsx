/**
 * Regression tests: Odds Heatmap must never show a blank tool.
 * - Left panel always has Force Refresh
 * - Empty and error copy exist in component behavior (covered by backend contract tests + UI copy)
 */
import React from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it, vi, beforeEach } from "vitest"

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => React.createElement("div", props, children),
  },
}))
vi.mock("next/link", () => ({
  default: ({ href, children, ...props }: { href: string; children: React.ReactNode }) =>
    React.createElement("a", { href, ...props }, children),
}))
vi.mock("@/lib/subscription-context", () => ({
  useSubscription: () => ({ isPremium: true }),
}))
vi.mock("@/lib/sports/SportsUiPolicy", () => ({
  sportsUiPolicy: { isComingSoon: () => false },
}))
vi.mock("@/lib/api", () => ({
  api: {
    listSports: vi.fn().mockResolvedValue([{ slug: "nfl", is_enabled: true, in_season: true }]),
    getGames: vi.fn(),
    getHeatmapProbabilities: vi.fn(),
  },
}))

import { api } from "@/lib/api"
import { OddsHeatmapView } from "@/app/tools/odds-heatmap/OddsHeatmapView"

describe("OddsHeatmapView empty and error states", () => {
  beforeEach(() => {
    vi.mocked(api.getGames).mockResolvedValue({ games: [], sport_state: undefined, next_game_at: undefined, status_label: undefined })
    vi.mocked(api.getHeatmapProbabilities).mockResolvedValue([])
  })

  it("renders Force Refresh in left panel so tool is never blank", () => {
    const html = renderToStaticMarkup(<OddsHeatmapView />)
    expect(html).toContain("Force Refresh")
    expect(html).toContain("Odds Heatmap Assistant")
  })

  it("renders loading or empty/error copy so content area is never blank", () => {
    const html = renderToStaticMarkup(<OddsHeatmapView />)
    const hasLoading = html.includes("Loading odds data")
    const hasEmpty = html.includes("No odds available")
    const hasError = html.includes("Retry")
    expect(hasLoading || hasEmpty || hasError || html.includes("No data for this sport")).toBe(true)
  })
})
