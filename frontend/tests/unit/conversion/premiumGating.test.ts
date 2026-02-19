import { describe, expect, it } from "vitest"
import {
  isPremiumUser,
  isAuthResolved,
  shouldShowUpgradeSurface,
} from "@/lib/conversion/premiumGating"

describe("premiumGating", () => {
  it("isPremiumUser returns true only when isPremium is true", () => {
    expect(isPremiumUser(true)).toBe(true)
    expect(isPremiumUser(false)).toBe(false)
  })

  it("isAuthResolved returns true only when loading is false", () => {
    expect(isAuthResolved(false)).toBe(true)
    expect(isAuthResolved(true)).toBe(false)
  })

  it("shouldShowUpgradeSurface is false for premium user", () => {
    expect(shouldShowUpgradeSurface({ isPremium: true, loading: false })).toBe(false)
    expect(shouldShowUpgradeSurface({ isPremium: true, loading: true })).toBe(false)
  })

  it("shouldShowUpgradeSurface is false when auth not resolved", () => {
    expect(shouldShowUpgradeSurface({ isPremium: false, loading: true })).toBe(false)
  })

  it("shouldShowUpgradeSurface is true only when not premium and resolved", () => {
    expect(shouldShowUpgradeSurface({ isPremium: false, loading: false })).toBe(true)
  })
})
