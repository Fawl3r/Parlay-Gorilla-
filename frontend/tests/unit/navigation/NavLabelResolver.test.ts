import { describe, expect, it } from "vitest"

import { NavLabelResolver } from "@/lib/navigation/NavLabelResolver"

describe("NavLabelResolver", () => {
  it("resolves mobile titles for key routes", () => {
    const resolver = new NavLabelResolver()

    expect(resolver.getTitle("/")).toBe("Home")
    expect(resolver.getTitle("/app")).toBe("Home")
    expect(resolver.getTitle("/build")).toBe("Build")
    expect(resolver.getTitle("/analysis")).toBe("Games")
    expect(resolver.getTitle("/analysis/nfl/some-slug")).toBe("Games")
    expect(resolver.getTitle("/analytics")).toBe("Insights")
    expect(resolver.getTitle("/profile")).toBe("Account")
    expect(resolver.getTitle("/billing")).toBe("Plan & Billing")
    expect(resolver.getTitle("/usage")).toBe("Usage & Performance")
  })

  it("shows back only on non-root destinations", () => {
    const resolver = new NavLabelResolver()

    expect(resolver.shouldShowBack("/")).toBe(false)
    expect(resolver.shouldShowBack("/app")).toBe(false)
    expect(resolver.shouldShowBack("/build")).toBe(false)
    expect(resolver.shouldShowBack("/analysis")).toBe(false)
    expect(resolver.shouldShowBack("/analytics")).toBe(false)
    expect(resolver.shouldShowBack("/profile")).toBe(false)

    expect(resolver.shouldShowBack("/analysis/nfl/some-slug")).toBe(true)
    expect(resolver.shouldShowBack("/profile/setup")).toBe(true)
    expect(resolver.shouldShowBack("/pricing")).toBe(true)
  })
})


