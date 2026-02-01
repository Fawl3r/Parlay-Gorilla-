import React from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it, vi } from "vitest"

vi.mock("next/link", () => {
  return {
    default: ({ href, children, ...props }: any) => React.createElement("a", { href, ...props }, children),
  }
})

vi.mock("framer-motion", () => {
  return {
    motion: {
      div: ({ children, ...props }: any) => React.createElement("div", props, children),
    },
  }
})

import { GameRow } from "@/components/games/GameRow"

describe("GameRow win probability display", () => {
  it("renders — (not 50%) when h2h odds are missing", () => {
    const html = renderToStaticMarkup(
      <GameRow
        sport="nhl"
        game={{
          id: "g1",
          external_game_id: "espn:nhl:1",
          sport: "NHL",
          home_team: "Detroit Red Wings",
          away_team: "Colorado Avalanche",
          start_time: new Date().toISOString(),
          status: "scheduled",
          markets: [],
        }}
        index={0}
        canViewWinProb={false}
        selectedMarket={"all"}
        parlayLegs={new Set()}
        onToggleParlayLeg={() => undefined}
        showMarkets={true}
      />
    )

    expect(html).toContain("—")
    expect(html).not.toContain("50%")
  })

  it("renders real percentages when h2h odds are present", () => {
    const html = renderToStaticMarkup(
      <GameRow
        sport="nhl"
        game={{
          id: "g2",
          external_game_id: "odds:nhl:2",
          sport: "NHL",
          home_team: "Detroit Red Wings",
          away_team: "Colorado Avalanche",
          start_time: new Date().toISOString(),
          status: "scheduled",
          markets: [
            {
              id: "m1",
              market_type: "h2h",
              book: "fanduel",
              odds: [
                {
                  id: "o-away",
                  outcome: "away",
                  price: "-150",
                  decimal_price: 1.67,
                  implied_prob: 0.4,
                  created_at: new Date().toISOString(),
                },
                {
                  id: "o-home",
                  outcome: "home",
                  price: "+120",
                  decimal_price: 2.2,
                  implied_prob: 0.6,
                  created_at: new Date().toISOString(),
                },
              ],
            },
          ],
        }}
        index={0}
        canViewWinProb={true}
        selectedMarket={"all"}
        parlayLegs={new Set()}
        onToggleParlayLeg={() => undefined}
        showMarkets={true}
      />
    )

    expect(html).toContain("61%")
    expect(html).toContain("39%")
    expect(html).not.toContain("—")
  })
})

