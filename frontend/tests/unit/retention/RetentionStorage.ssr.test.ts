import { describe, expect, it } from "vitest"
import {
  recordVisit,
  getProgression,
  getStreak,
  getLastResearchAsOf,
  hasViewedSlug,
  getMarketSnapshotEntries,
} from "@/lib/retention/RetentionStorage"

/**
 * SSR safety: RetentionStorage functions must not throw when window is undefined.
 * In Node (vitest default environment) window is undefined.
 */
describe("RetentionStorage SSR safety", () => {
  it("recordVisit does not throw when window is undefined", () => {
    expect(() => recordVisit()).not.toThrow()
  })

  it("getProgression returns default when window is undefined", () => {
    const p = getProgression()
    expect(p).toBeDefined()
    expect(p.analysesViewedCount).toBe(0)
    expect(p.sportsExplored).toEqual([])
    expect(p.level).toBe(1)
    expect(p.label).toBe("Explorer")
  })

  it("getStreak returns default when window is undefined", () => {
    const s = getStreak()
    expect(s).toBeDefined()
    expect(s.currentStreak).toBe(0)
  })

  it("getLastResearchAsOf returns null when window is undefined", () => {
    expect(getLastResearchAsOf()).toBeNull()
  })

  it("hasViewedSlug returns false when window is undefined", () => {
    expect(hasViewedSlug("nfl/some-slug")).toBe(false)
  })

  it("getMarketSnapshotEntries returns empty array when window is undefined", () => {
    expect(getMarketSnapshotEntries()).toEqual([])
  })
})
