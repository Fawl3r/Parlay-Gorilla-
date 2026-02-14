import { describe, expect, it } from "vitest"
import { normalizeGameStatus, getDisplayStatusPill } from "@/components/games/gameStatusUtils"

describe("gameStatusUtils", () => {
  const future = new Date(Date.now() + 86400000).toISOString()
  const past = new Date(Date.now() - 86400000).toISOString()
  const now = new Date()

  describe("normalizeGameStatus", () => {
    it("maps scheduled => UPCOMING", () => {
      expect(normalizeGameStatus("scheduled", future, now)).toBe("UPCOMING")
      expect(normalizeGameStatus("Scheduled", future, now)).toBe("UPCOMING")
    })

    it("maps pre / not_started => UPCOMING", () => {
      expect(normalizeGameStatus("pre", future, now)).toBe("UPCOMING")
      expect(normalizeGameStatus("not_started", future, now)).toBe("UPCOMING")
    })

    it("maps live / inprogress => LIVE", () => {
      expect(normalizeGameStatus("live", past, now)).toBe("LIVE")
      expect(normalizeGameStatus("inprogress", past, now)).toBe("LIVE")
      expect(normalizeGameStatus("in_progress", past, now)).toBe("LIVE")
      expect(normalizeGameStatus("halftime", past, now)).toBe("LIVE")
    })

    it("maps final / completed / finished => FINAL", () => {
      expect(normalizeGameStatus("final", past, now)).toBe("FINAL")
      expect(normalizeGameStatus("completed", past, now)).toBe("FINAL")
      expect(normalizeGameStatus("finished", past, now)).toBe("FINAL")
      expect(normalizeGameStatus("closed", past, now)).toBe("FINAL")
      expect(normalizeGameStatus("complete", past, now)).toBe("FINAL")
    })

    it("unknown status falls back to time-based: future => UPCOMING", () => {
      expect(normalizeGameStatus("unknown", future, now)).toBe("UPCOMING")
    })

    it("unknown status falls back to time-based: past => LIVE", () => {
      expect(normalizeGameStatus("unknown", past, now)).toBe("LIVE")
    })

    it("handles ISO Z timestamps", () => {
      expect(normalizeGameStatus("scheduled", "2026-03-01T19:00:00Z", new Date("2026-02-01"))).toBe("UPCOMING")
      expect(normalizeGameStatus("finished", "2026-01-01T19:00:00Z", new Date("2026-02-01"))).toBe("FINAL")
    })
  })

  describe("getDisplayStatusPill", () => {
    it("returns Scheduled for UPCOMING", () => {
      expect(getDisplayStatusPill("UPCOMING")).toBe("Scheduled")
    })
    it("returns Live for LIVE", () => {
      expect(getDisplayStatusPill("LIVE")).toBe("Live")
    })
    it("returns Final for FINAL", () => {
      expect(getDisplayStatusPill("FINAL")).toBe("Final")
    })
  })
})
