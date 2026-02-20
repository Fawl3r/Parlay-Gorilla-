import React from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it, vi } from "vitest"

vi.mock("next/link", () => ({
  default: ({ href, children, ...props }: any) => React.createElement("a", { href, ...props }, children),
}))

vi.mock("@/lib/auth-context", () => ({
  useAuth: () => ({ user: null }),
}))

vi.mock("@/lib/subscription-context", () => ({
  useSubscription: () => ({ isPremium: false }),
}))

vi.mock("@/lib/retention", () => ({
  recordVisit: () => {},
}))

vi.mock("@/lib/sports/useSportsAvailability", () => ({
  useSportsAvailability: () => ({
    sports: [],
    inSeasonSports: [],
    isLoading: true,
    error: null,
    isStale: false,
    isSportEnabled: () => false,
    getSportBadge: () => "",
    normalizeSlug: (s: string) => (s || "").toLowerCase().trim(),
  }),
}))

vi.mock("@/components/games/useGamesForSportDate", () => ({
  useGamesForSportDate: () => ({
    games: [],
    loading: true,
    refreshing: false,
    error: null,
    refresh: () => {},
    listMeta: null,
  }),
}))

vi.mock("@/components/Header", () => ({
  Header: () => React.createElement("header", null, "Header"),
}))
vi.mock("@/components/Footer", () => ({
  Footer: () => React.createElement("footer", null, "Footer"),
}))
vi.mock("@/components/billing/BalanceStrip", () => ({
  BalanceStrip: () => null,
}))
vi.mock("@/components/notifications/PushNotificationsToggle", () => ({
  PushNotificationsToggle: () => null,
}))

import GameAnalysisHubClient from "@/app/analysis/GameAnalysisHubClient"

describe("GameAnalysisHubClient explainer", () => {
  it("shows How game analysis works explainer when sports are loading", () => {
    const html = renderToStaticMarkup(<GameAnalysisHubClient />)
    expect(html).toContain("How game analysis works")
    expect(html).toContain("Loading available sports and matchups")
  })
})
