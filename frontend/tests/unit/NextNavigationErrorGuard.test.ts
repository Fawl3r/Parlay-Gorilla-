import { describe, expect, it } from "vitest"

import { NextNavigationErrorGuard } from "@/lib/errors/NextNavigationErrorGuard"

describe("NextNavigationErrorGuard", () => {
  it("detects redirect errors from message", () => {
    const error = new Error("NEXT_REDIRECT")

    expect(NextNavigationErrorGuard.shouldRethrow(error)).toBe(true)
  })

  it("detects redirect errors from digest", () => {
    const error = { digest: "NEXT_REDIRECT;replace;/analysis/nfl/tbd-vs-tbd-week-20-2026" }

    expect(NextNavigationErrorGuard.shouldRethrow(error)).toBe(true)
  })

  it("detects not found errors", () => {
    const error = { digest: "NEXT_NOT_FOUND;root" }

    expect(NextNavigationErrorGuard.shouldRethrow(error)).toBe(true)
  })

  it("ignores non-navigation errors", () => {
    const error = new Error("Boom")

    expect(NextNavigationErrorGuard.shouldRethrow(error)).toBe(false)
  })
})

