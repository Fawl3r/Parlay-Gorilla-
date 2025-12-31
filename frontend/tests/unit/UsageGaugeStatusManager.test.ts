import { describe, expect, it } from "vitest"

import { UsageGaugeStatusManager } from "@/lib/usage/UsageGaugeStatusManager"

describe("UsageGaugeStatusManager", () => {
  it("maps percent thresholds to statuses", () => {
    const mgr = new UsageGaugeStatusManager()
    expect(mgr.getStatus(null)).toBe("neutral")
    expect(mgr.getStatus(0)).toBe("good")
    expect(mgr.getStatus(60)).toBe("good")
    expect(mgr.getStatus(61)).toBe("warning")
    expect(mgr.getStatus(85)).toBe("warning")
    expect(mgr.getStatus(86)).toBe("critical")
    expect(mgr.getStatus(100)).toBe("critical")
  })

  it("computes percent used with clamping and null handling", () => {
    const mgr = new UsageGaugeStatusManager()
    expect(mgr.getPercentUsed(0, null)).toBeNull()
    expect(mgr.getPercentUsed(0, undefined)).toBeNull()
    expect(mgr.getPercentUsed(0, 0)).toBeNull()
    expect(mgr.getPercentUsed(5, -1)).toBeNull()

    expect(mgr.getPercentUsed(0, 10)).toBe(0)
    expect(mgr.getPercentUsed(5, 10)).toBe(50)
    expect(mgr.getPercentUsed(10, 10)).toBe(100)
    expect(mgr.getPercentUsed(15, 10)).toBe(100)
  })
})


