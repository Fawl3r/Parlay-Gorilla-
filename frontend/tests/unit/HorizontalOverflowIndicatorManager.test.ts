import { describe, expect, it } from "vitest"

import { HorizontalOverflowIndicatorManager } from "@/lib/ui/HorizontalOverflowIndicatorManager"

describe("HorizontalOverflowIndicatorManager", () => {
  it("returns no indicators when content does not overflow", () => {
    expect(
      HorizontalOverflowIndicatorManager.compute({
        scrollLeft: 0,
        clientWidth: 320,
        scrollWidth: 320,
      })
    ).toEqual({ canScrollLeft: false, canScrollRight: false })
  })

  it("shows right indicator when at start and content overflows", () => {
    expect(
      HorizontalOverflowIndicatorManager.compute({
        scrollLeft: 0,
        clientWidth: 320,
        scrollWidth: 600,
      })
    ).toEqual({ canScrollLeft: false, canScrollRight: true })
  })

  it("shows left indicator when scrolled away from start", () => {
    expect(
      HorizontalOverflowIndicatorManager.compute({
        scrollLeft: 80,
        clientWidth: 320,
        scrollWidth: 600,
      })
    ).toEqual({ canScrollLeft: true, canScrollRight: true })
  })

  it("hides right indicator when at end", () => {
    expect(
      HorizontalOverflowIndicatorManager.compute({
        scrollLeft: 280,
        clientWidth: 320,
        scrollWidth: 600,
        thresholdPx: 0,
      })
    ).toEqual({ canScrollLeft: true, canScrollRight: false })
  })
})


