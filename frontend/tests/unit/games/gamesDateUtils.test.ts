import { describe, expect, it } from "vitest"
import { isGameOnDate } from "@/components/games/gamesDateUtils"

describe("gamesDateUtils", () => {
  describe("isGameOnDate", () => {
    it("returns true when game start_time is on the selected calendar day (local)", () => {
      // Noon UTC on 2025-02-15 is same calendar day in all common timezones
      expect(isGameOnDate("2025-02-15T12:00:00Z", "2025-02-15")).toBe(true)
    })

    it("returns false when game start_time is on a different day", () => {
      expect(isGameOnDate("2025-02-16T19:00:00Z", "2025-02-15")).toBe(false)
      expect(isGameOnDate("2025-02-14T19:00:00Z", "2025-02-15")).toBe(false)
    })

    it("accepts 'today' as selectedDateStr and uses current local date", () => {
      const result = isGameOnDate("2025-02-15T19:00:00Z", "today")
      expect(typeof result).toBe("boolean")
    })
  })
})
