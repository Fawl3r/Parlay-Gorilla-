import React from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it, vi } from "vitest"

vi.mock("next/link", () => {
  return {
    default: ({ href, children, ...props }: any) =>
      React.createElement("a", { href, ...props }, children),
  }
})

vi.mock("@/lib/auth-context", () => {
  return {
    useAuth: () => ({
      user: { id: "test-user" },
    }),
  }
})

vi.mock("@/lib/subscription-context", () => {
  return {
    useSubscription: () => ({
      isPremium: true,
    }),
  }
})

vi.mock("@/components/games/useGamesForSportDate", () => {
  return {
    useGamesForSportDate: () => ({
      games: [
        // Schedule-only (no odds) — should NOT render on dashboard.
        {
          id: "schedule-1",
          external_game_id: "espn:nba:1",
          sport: "NBA",
          home_team: "Schedule Home",
          away_team: "Schedule Away",
          start_time: "2026-02-20T18:00:00Z",
          status: "scheduled",
          markets: [],
        },
        // Odds-backed (h2h with >=2 odds) — should render.
        {
          id: "odds-1",
          external_game_id: "odds:nba:1",
          sport: "NBA",
          home_team: "Odds Home",
          away_team: "Odds Away",
          start_time: "2026-02-20T18:10:00Z",
          status: "scheduled",
          markets: [
            {
              id: "m1",
              market_type: "h2h",
              book: "fanduel",
              odds: [
                { id: "o1", outcome: "Odds Away", price: "+120", decimal_price: 2.2, implied_prob: 0.4, created_at: "" },
                { id: "o2", outcome: "Odds Home", price: "-150", decimal_price: 1.67, implied_prob: 0.6, created_at: "" },
              ],
            },
          ],
        },
      ],
      listMeta: null,
      suggestedDate: null,
      oddsPreferredKeys: new Set(),
      loading: false,
      refreshing: false,
      error: null,
      refresh: () => undefined,
    }),
  }
})

vi.mock("@/components/ui/select", () => {
  const Select = ({ children }: any) => React.createElement("div", { "data-mock": "Select" }, children)
  const SelectTrigger = ({ children, className }: any) =>
    React.createElement("button", { className, type: "button" }, children)
  const SelectValue = ({ placeholder }: any) => React.createElement("span", null, placeholder)
  const SelectContent = ({ children, className }: any) => React.createElement("div", { className }, children)
  const SelectItem = ({ children, value, className }: any) =>
    React.createElement("div", { className, "data-value": value }, children)
  return { Select, SelectTrigger, SelectValue, SelectContent, SelectItem }
})

import { UpcomingGamesTab } from "@/app/app/_components/tabs/UpcomingGamesTab"

describe("UpcomingGamesTab (odds-only dashboard list)", () => {
  it("renders only matchups that include usable odds (so Win Prob can render)", () => {
    const html = renderToStaticMarkup(<UpcomingGamesTab sport="nba" onSportChange={() => {}} />)

    expect(html).not.toContain("Schedule Away @ Schedule Home")
    expect(html).toContain("Odds Away @ Odds Home")
  })
})

