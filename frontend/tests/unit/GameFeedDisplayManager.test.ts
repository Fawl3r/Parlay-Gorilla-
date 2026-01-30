import { describe, expect, it } from "vitest"

import {
  getWindowType,
  getCategoryLabel,
  getLeagueLabel,
  formatStartsIn,
  formatLocalTime,
  formatUpcomingMeta,
  formatUpdatedAgo,
  normalizeStatus,
} from "@/lib/games/GameFeedDisplayManager"

describe("GameFeedDisplayManager", () => {
  describe("getWindowType", () => {
    it("maps FT, COMPLETED, FINAL/OT, AET, PEN to final", () => {
      expect(getWindowType("FT")).toBe("final")
      expect(getWindowType("ft")).toBe("final")
      expect(getWindowType("COMPLETED")).toBe("final")
      expect(getWindowType("Completed")).toBe("final")
      expect(getWindowType("FINAL/OT")).toBe("final")
      expect(getWindowType("AET")).toBe("final")
      expect(getWindowType("PEN")).toBe("final")
      expect(getWindowType("FINAL")).toBe("final")
    })

    it("maps IN PROGRESS, Q1, 1H, HT to live", () => {
      expect(getWindowType("IN PROGRESS")).toBe("live")
      expect(getWindowType("IN_PROGRESS")).toBe("live")
      expect(getWindowType("Q1")).toBe("live")
      expect(getWindowType("Q2")).toBe("live")
      expect(getWindowType("1H")).toBe("live")
      expect(getWindowType("2H")).toBe("live")
      expect(getWindowType("HT")).toBe("live")
      expect(getWindowType("LIVE")).toBe("live")
    })

    it("maps unknown or scheduled status to upcoming", () => {
      expect(getWindowType("")).toBe("upcoming")
      expect(getWindowType("Scheduled")).toBe("upcoming")
      expect(getWindowType("UPCOMING")).toBe("upcoming")
    })
  })

  describe("normalizeStatus", () => {
    it("uppercases and trims and normalizes spaces", () => {
      expect(normalizeStatus("  live  ")).toBe("LIVE")
      expect(normalizeStatus("in progress")).toBe("IN PROGRESS")
    })
  })

  describe("getCategoryLabel / getLeagueLabel", () => {
    it("derives Football/NFL from nfl", () => {
      expect(getCategoryLabel("nfl")).toBe("Football")
      expect(getLeagueLabel("nfl")).toBe("NFL")
    })

    it("derives Basketball/NBA from nba", () => {
      expect(getCategoryLabel("nba")).toBe("Basketball")
      expect(getLeagueLabel("nba")).toBe("NBA")
    })

    it("derives Baseball/MLB from mlb", () => {
      expect(getCategoryLabel("mlb")).toBe("Baseball")
      expect(getLeagueLabel("mlb")).toBe("MLB")
    })

    it("derives Hockey/NHL from nhl", () => {
      expect(getCategoryLabel("nhl")).toBe("Hockey")
      expect(getLeagueLabel("nhl")).toBe("NHL")
    })

    it("derives Soccer/EPL from epl", () => {
      expect(getCategoryLabel("epl")).toBe("Soccer")
      expect(getLeagueLabel("epl")).toBe("EPL")
    })

    it("returns Other for unknown league", () => {
      expect(getCategoryLabel("unknown")).toBe("Other")
      expect(getLeagueLabel("unknown")).toBe("UNKNOWN")
    })
  })

  describe("formatStartsIn", () => {
    it("formats hours and minutes", () => {
      expect(formatStartsIn(2 * 60 * 60 * 1000)).toBe("Starts in 2h")
      expect(formatStartsIn(2 * 60 * 60 * 1000 + 30 * 60 * 1000)).toBe("Starts in 2h 30m")
      expect(formatStartsIn(45 * 60 * 1000)).toBe("Starts in 45m")
    })

    it("returns Starting for zero or negative ms", () => {
      expect(formatStartsIn(0)).toBe("Starting")
      expect(formatStartsIn(-1000)).toBe("Starting")
    })
  })

  describe("formatLocalTime", () => {
    it("formats date as local time (e.g. 7:15 PM)", () => {
      const d = new Date("2025-01-15T19:15:00Z")
      const str = formatLocalTime(d)
      expect(str).toMatch(/\d{1,2}:\d{2}\s*(AM|PM)/)
    })
  })

  describe("formatUpcomingMeta", () => {
    it("returns Starts in Xh Ym when within 6h", () => {
      const now = new Date("2025-01-15T12:00:00Z")
      const start = new Date("2025-01-15T14:00:00Z") // 2h later
      const result = formatUpcomingMeta(start.toISOString(), now)
      expect(result).toMatch(/Starts in 2h/)
    })

    it("returns local time when start is beyond 6h", () => {
      const now = new Date("2025-01-15T12:00:00Z")
      const start = new Date("2025-01-15T22:00:00Z") // 10h later
      const result = formatUpcomingMeta(start.toISOString(), now)
      expect(result).toMatch(/\d{1,2}:\d{2}\s*(AM|PM)/)
    })
  })

  describe("formatUpdatedAgo", () => {
    it("returns Updated Xs ago for under 60s", () => {
      const now = new Date("2025-01-15T12:00:30Z")
      const then = new Date("2025-01-15T12:00:14Z")
      expect(formatUpdatedAgo(then, now)).toBe("Updated 16s ago")
    })

    it("returns Updated Xm ago for 60s or more", () => {
      const now = new Date("2025-01-15T12:05:00Z")
      const then = new Date("2025-01-15T12:00:00Z")
      expect(formatUpdatedAgo(then, now)).toBe("Updated 5m ago")
    })

    it("accepts number timestamp", () => {
      const now = new Date("2025-01-15T12:00:30Z")
      const then = new Date("2025-01-15T12:00:14Z").getTime()
      expect(formatUpdatedAgo(then, now)).toBe("Updated 16s ago")
    })
  })
})
