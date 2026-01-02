import React from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it, vi } from "vitest"

vi.mock("next/link", () => {
  return {
    default: ({ href, children, ...props }: any) => React.createElement("a", { href, ...props }, children),
  }
})

import { SavedParlayRow } from "@/components/analytics/SavedParlayRow"

describe("SavedParlayRow (SSR smoke)", () => {
  it("renders an expandable picks section for AI saved parlays", () => {
    const html = renderToStaticMarkup(
      <SavedParlayRow
        item={{
          id: "p1",
          user_id: "u1",
          parlay_type: "ai_generated",
          title: "My AI Parlay",
          legs: [
            {
              sport: "NFL",
              game: "Steelers @ Ravens",
              market_type: "h2h",
              outcome: "away",
              odds: "+150",
              confidence: 73,
            },
          ],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          version: 1,
          content_hash: "hash",
          inscription_status: "none",
        }}
        onRetry={async () => {}}
      />
    )

    expect(html).toContain("View picks (1)")
    expect(html).toContain("Steelers @ Ravens")
    expect(html).toContain("Moneyline")
  })
})


