import { describe, expect, it, vi, beforeEach, afterEach } from "vitest"
import { emitIntentEvent } from "@/lib/monetization-timing/intentEvents"

describe("emitIntentEvent production behavior", () => {
  const originalEnv = process.env.NODE_ENV
  let consoleSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    consoleSpy = vi.spyOn(console, "debug").mockImplementation(() => {})
  })

  afterEach(() => {
    consoleSpy.mockRestore()
    process.env.NODE_ENV = originalEnv
  })

  it("does not log in production (NODE_ENV=production)", () => {
    process.env.NODE_ENV = "production"
    emitIntentEvent("analysis_viewed")
    expect(consoleSpy).not.toHaveBeenCalled()
  })

  it("does not log in production even with detail", () => {
    process.env.NODE_ENV = "production"
    emitIntentEvent("upgrade_prompt_shown", { surface: "powerUser" })
    expect(consoleSpy).not.toHaveBeenCalled()
  })
})
