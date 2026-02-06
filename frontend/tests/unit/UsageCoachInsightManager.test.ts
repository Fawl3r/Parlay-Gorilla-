import { afterEach, describe, expect, it, vi } from "vitest"

import { UsageCoachInsightManager } from "@/lib/usage/UsageCoachInsightManager"

describe("UsageCoachInsightManager", () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("emits a gentle heads-up when near a limit", () => {
    const mgr = new UsageCoachInsightManager()
    const msg = mgr.getSingleInsight({
      ai: { used: 90, limit: 100, remaining: 10 },
      custom: { used: 1, limit: 25, remaining: 24 },
      credits: { balance: 0, costPerAiParlay: 3 },
    })
    expect(msg).toContain("Heads up")
    expect(msg).toContain("Gorilla Parlays (AI) left this period")
  })

  it("emits a pacing projection when period bounds are available", () => {
    vi.spyOn(Date, "now").mockReturnValue(Date.parse("2025-01-11T00:00:00.000Z"))

    const mgr = new UsageCoachInsightManager()
    const msg = mgr.getSingleInsight({
      ai: {
        used: 20,
        limit: 100,
        remaining: 80,
        periodStartIso: "2025-01-01T00:00:00.000Z",
        periodEndIso: "2025-01-31T00:00:00.000Z",
      },
      custom: { used: 0, limit: 25, remaining: 25 },
      credits: { balance: 0, costPerAiParlay: 3 },
    })
    expect(msg).toBe("At your current pace, you’ll have ~40 AI parlays left this cycle.")
  })

  it("emits a selective Gorilla Parlay Builder insight when usage share is low", () => {
    const mgr = new UsageCoachInsightManager()
    const msg = mgr.getSingleInsight({
      ai: { used: 20, limit: 100, remaining: 80 },
      custom: { used: 2, limit: 25, remaining: 23 },
      credits: { balance: 0, costPerAiParlay: 3 },
    })
    expect(msg).toBe("You’ve been using Gorilla Parlay Builder selectively — that’s typically the most effective approach.")
  })

  it("defaults to a reassuring message when signals are low", () => {
    const mgr = new UsageCoachInsightManager()
    const msg = mgr.getSingleInsight({
      ai: { used: 0, limit: 100, remaining: 100 },
      custom: { used: 0, limit: 25, remaining: 25 },
      credits: { balance: 10, costPerAiParlay: 3 },
    })
    expect(msg).toBe("You’re pacing well — no risk of hitting limits this cycle.")
  })

  it("estimates AI runs from credits", () => {
    const mgr = new UsageCoachInsightManager()
    expect(mgr.estimateAiRunsFromCredits(10, 3)).toBe(3)
    expect(mgr.estimateAiRunsFromCredits(0, 3)).toBe(0)
  })
})





