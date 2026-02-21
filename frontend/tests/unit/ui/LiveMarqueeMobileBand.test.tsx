import React from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it, vi } from "vitest"

vi.mock("framer-motion", () => {
  return {
    motion: {
      div: ({ children, ...props }: any) => React.createElement("div", props, children),
    },
    AnimatePresence: ({ children }: any) => React.createElement(React.Fragment, null, children),
  }
})

vi.mock("@/lib/api", () => ({
  api: {
    getGameFeed: vi.fn(),
  },
}))

import type { GameFeedResponse } from "@/lib/api"
import { LiveMarquee, buildCombinedFeed } from "@/components/feed/LiveMarquee"

function feedGame(overrides: Partial<GameFeedResponse> = {}): GameFeedResponse {
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

describe("LiveMarquee mobile band (SSR smoke)", () => {
  it("variant=mobile includes sticky band classes (sticky, safe-area top calc, md:static)", () => {
    const html = renderToStaticMarkup(<LiveMarquee variant="mobile" />)
    expect(html).toContain("sticky")
    expect(html).toContain("top-[calc(4rem+env(safe-area-inset-top))]")
    expect(html).toContain("min-h-[112px]")
    expect(html).toContain("md:static")
  })

  it("default (desktop) variant does not include mobile sticky classes", () => {
    const html = renderToStaticMarkup(<LiveMarquee />)
    expect(html).not.toContain("top-[calc(4rem+env(safe-area-inset-top))]")
    expect(html).not.toContain("sticky")
  })
})

describe("buildCombinedFeed dedupe", () => {
  it("removes duplicates when two items share the same dedupe key", () => {
    const g1 = feedGame({ id: "a", start_time: "2025-02-01T18:30:00Z" })
    const g2 = feedGame({ id: "b", start_time: "2025-02-01T18:32:00Z" })
    const result = buildCombinedFeed([g1, g2], [], [])
    expect(result).toHaveLength(1)
    expect(result[0]!.id).toBe("a")
  })
})
