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
      isPremium: false,
    }),
  }
})

vi.mock("@/components/games/useGamesForSportDate", () => {
  return {
    useGamesForSportDate: () => ({
      games: [],
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

describe("UpcomingGamesTab (responsive sports selector)", () => {
  it("includes a mobile dropdown selector and hides the pill tabs on small screens", () => {
    const html = renderToStaticMarkup(<UpcomingGamesTab sport="nfl" onSportChange={() => {}} />)

    expect(html).toContain("sm:hidden")
    expect(html).toContain("hidden sm:flex")
    expect(html).toContain("Select sport")
  })
})





