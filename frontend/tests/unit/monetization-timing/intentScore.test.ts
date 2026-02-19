import { describe, expect, it } from "vitest"
import { computeIntentScore, getIntentLevel, getIntentState } from "@/lib/monetization-timing/intentScore"
import { INTENT_LEVEL_THRESHOLDS } from "@/lib/monetization-timing/constants"
import type { IntentCounters } from "@/lib/monetization-timing/intentStorage"

const empty: IntentCounters = {
  analyses_viewed_count: 0,
  analyses_viewed_today: 0,
  sports_explored_count: 0,
  builder_interactions: 0,
  return_visits: 0,
  consecutive_days_active: 0,
  blurred_content_views: 0,
}

describe("monetization-timing intent score", () => {
  it("returns 0 for empty counters", () => {
    expect(computeIntentScore(empty)).toBe(0)
    expect(getIntentLevel(0)).toBe("exploring")
  })

  it("maps score to levels: exploring → engaged → powerUser → highIntent", () => {
    expect(getIntentLevel(INTENT_LEVEL_THRESHOLDS.exploring.min)).toBe("exploring")
    expect(getIntentLevel(10)).toBe("exploring")
    expect(getIntentLevel(11)).toBe("engaged")
    expect(getIntentLevel(25)).toBe("engaged")
    expect(getIntentLevel(26)).toBe("powerUser")
    expect(getIntentLevel(45)).toBe("powerUser")
    expect(getIntentLevel(46)).toBe("highIntent")
    expect(getIntentLevel(100)).toBe("highIntent")
  })

  it("adds points for analysis views, builder, return visits, blurred views, multi-sport, streak", () => {
    const c: IntentCounters = {
      ...empty,
      analyses_viewed_count: 5,
      builder_interactions: 2,
      return_visits: 1,
      blurred_content_views: 1,
      sports_explored_count: 2,
      consecutive_days_active: 1,
    }
    const score = computeIntentScore(c)
    // 5*2 + 2*3 + 1*5 + 1*2 + 4 (multi-sport) + 1*3 (streak) = 10+6+5+2+4+3 = 30
    expect(score).toBeGreaterThanOrEqual(26)
    expect(score).toBeLessThanOrEqual(45)
    expect(getIntentLevel(score)).toBe("powerUser")
  })

  it("getIntentState returns score and level", () => {
    const c: IntentCounters = { ...empty, analyses_viewed_count: 10, return_visits: 2 }
    const state = getIntentState(c)
    expect(state.score).toBeGreaterThan(0)
    expect(["exploring", "engaged", "powerUser", "highIntent"]).toContain(state.level)
  })
})
