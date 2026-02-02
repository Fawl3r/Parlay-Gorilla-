/**
 * Copy-only UX layer: getCopyForReason and getActionIdForReason.
 * Beginner Mode always returns DEFAULT; unknown reason returns fallback; known reason maps correctly.
 */

import { describe, expect, it } from "vitest"
import {
  getCopyForReason,
  getActionIdForReason,
  UX_REASON_COPY_BEGINNER,
  UX_REASON_FALLBACK,
  UX_REASON_COPY,
} from "@/lib/parlay/uxLanguageMap"

describe("getCopyForReason", () => {
  it("Beginner Mode always returns BEGINNER.DEFAULT", () => {
    const result = getCopyForReason("NO_ODDS", true)
    expect(result).toEqual(UX_REASON_COPY_BEGINNER.DEFAULT)
    expect(result.title).toBe("Not enough games yet")
    expect(result.body).toContain("fixes itself")
    expect(result.action).toBe("Use fewer picks")
  })

  it("Beginner Mode returns DEFAULT for any reason", () => {
    expect(getCopyForReason("OUTSIDE_WEEK", true)).toEqual(UX_REASON_COPY_BEGINNER.DEFAULT)
    expect(getCopyForReason(null, true)).toEqual(UX_REASON_COPY_BEGINNER.DEFAULT)
    expect(getCopyForReason("UNKNOWN_REASON", true)).toEqual(UX_REASON_COPY_BEGINNER.DEFAULT)
  })

  it("Unknown reason returns DEFAULT (standard mode)", () => {
    const result = getCopyForReason("UNKNOWN_CODE", false)
    expect(result).toEqual(UX_REASON_FALLBACK)
    expect(result.title).toBe("Not enough good games yet")
  })

  it("Null reason returns DEFAULT (standard mode)", () => {
    const result = getCopyForReason(null, false)
    expect(result).toEqual(UX_REASON_FALLBACK)
  })

  it("Known reason maps correctly in Standard Mode", () => {
    expect(getCopyForReason("NO_ODDS", false)).toEqual(UX_REASON_COPY.NO_ODDS)
    expect(getCopyForReason("NO_ODDS", false).title).toBe("Games aren't ready yet")
    expect(getCopyForReason("NO_ODDS", false).action).toBe("Use win-only picks")

    expect(getCopyForReason("OUTSIDE_WEEK", false)).toEqual(UX_REASON_COPY.OUTSIDE_WEEK)
    expect(getCopyForReason("OUTSIDE_WEEK", false).action).toBe("Include all upcoming games")

    expect(getCopyForReason("PLAYER_PROPS_DISABLED", false)).toEqual(UX_REASON_COPY.PLAYER_PROPS_DISABLED)
    expect(getCopyForReason("PLAYER_PROPS_DISABLED", false).action).toBe("Include player picks")
  })
})

describe("getActionIdForReason", () => {
  it("Beginner Mode always returns lower_legs", () => {
    expect(getActionIdForReason("NO_ODDS", true)).toBe("lower_legs")
    expect(getActionIdForReason("OUTSIDE_WEEK", true)).toBe("lower_legs")
    expect(getActionIdForReason(null, true)).toBe("lower_legs")
  })

  it("Standard Mode maps NO_ODDS to ml_only", () => {
    expect(getActionIdForReason("NO_ODDS", false)).toBe("ml_only")
  })

  it("Standard Mode maps OUTSIDE_WEEK and STATUS_NOT_UPCOMING to all_upcoming", () => {
    expect(getActionIdForReason("OUTSIDE_WEEK", false)).toBe("all_upcoming")
    expect(getActionIdForReason("STATUS_NOT_UPCOMING", false)).toBe("all_upcoming")
  })

  it("Standard Mode maps PLAYER_PROPS_DISABLED to enable_props", () => {
    expect(getActionIdForReason("PLAYER_PROPS_DISABLED", false)).toBe("enable_props")
  })

  it("Standard Mode maps unknown reason to lower_legs", () => {
    expect(getActionIdForReason(null, false)).toBe("lower_legs")
    expect(getActionIdForReason("UNKNOWN", false)).toBe("lower_legs")
  })
})
