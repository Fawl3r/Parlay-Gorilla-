import { describe, expect, it } from "vitest"

import { BetConfidenceRanker } from "@/lib/analysis/BetConfidenceRanker"

describe("BetConfidenceRanker", () => {
  it("ranks items by confidence descending", () => {
    const ranker = new BetConfidenceRanker<{ id: string; confidence?: number }>()
    const ranked = ranker.rank([
      { id: "a", confidence: 10 },
      { id: "b", confidence: 80 },
      { id: "c", confidence: 50 },
    ])
    expect(ranked.map((x) => x.id)).toEqual(["b", "c", "a"])
  })

  it("treats missing/invalid confidence as 0", () => {
    const ranker = new BetConfidenceRanker<{ id: string; confidence?: any }>()
    const ranked = ranker.rank([{ id: "a", confidence: "bad" }, { id: "b", confidence: 1 }])
    expect(ranked.map((x) => x.id)).toEqual(["b", "a"])
  })

  it("returns the top item or null", () => {
    const ranker = new BetConfidenceRanker<{ id: string; confidence?: number }>()
    expect(ranker.top([])).toBeNull()
    expect(ranker.top([{ id: "x", confidence: 12 }])?.id).toBe("x")
  })
})


