import React from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it, vi } from "vitest"

vi.mock("next/link", () => {
  return {
    default: ({ href, children, ...props }: any) =>
      React.createElement("a", { href, ...props }, children),
  }
})

vi.mock("framer-motion", () => {
  return {
    motion: {
      div: ({ children, ...props }: any) => React.createElement("div", props, children),
    },
  }
})
vi.mock("@/lib/pwa/PwaInstallContext", () => ({
  usePwaInstallNudge: () => ({ nudgeInstallCta: () => undefined }),
}))

import { UpsetFinderResults } from "@/app/tools/upset-finder/_components/UpsetFinderResults"

describe("UpsetFinderResults row (SSR)", () => {
  it("renders best line and verify odds chip", () => {
    const html = renderToStaticMarkup(
      <UpsetFinderResults
        candidates={[
          {
            game_id: "g1",
            start_time: new Date().toISOString(),
            league: "NBA",
            home_team: "Home",
            away_team: "Away",
            underdog_side: "home",
            underdog_team: "Home",
            underdog_ml: 140,
            implied_prob: 0.41,
            model_prob: 0.48,
            edge: 7.0,
            confidence: 0.6,
            reasons: [],
            books_count: 6,
            best_underdog_ml: 165,
            median_underdog_ml: 155,
            price_spread: 90,
            worst_underdog_ml: 140,
            flags: ["stale_odds_suspected", "low_books"],
            odds_quality: "thin",
          },
        ]}
        meta={{ games_scanned: 10, games_with_odds: 6, missing_odds: 4 }}
        access={{ can_view_candidates: true, reason: null }}
        sport="nba"
        days={7}
        minEdgePct={3}
        loading={false}
        error={null}
        onAction={() => undefined}
      />
    )

    expect(html).toContain("Best:")
    expect(html).toContain("+165")
    expect(html).toContain("(6 books)")
    expect(html).toContain("Verify odds")
  })

  it("does not crash when best_underdog_ml is missing", () => {
    const html = renderToStaticMarkup(
      <UpsetFinderResults
        candidates={[
          {
            game_id: "g2",
            start_time: new Date().toISOString(),
            league: "NBA",
            home_team: "Home",
            away_team: "Away",
            underdog_side: "home",
            underdog_team: "Home",
            underdog_ml: 140,
            implied_prob: 0.41,
            model_prob: 0.48,
            edge: 7.0,
            confidence: 0.6,
            reasons: [],
          } as any,
        ]}
        meta={{ games_scanned: 10, games_with_odds: 6, missing_odds: 4 }}
        access={{ can_view_candidates: true, reason: null }}
        sport="nba"
        days={7}
        minEdgePct={3}
        loading={false}
        error={null}
        onAction={() => undefined}
      />
    )

    expect(html).toContain("Away @ Home")
  })
})

