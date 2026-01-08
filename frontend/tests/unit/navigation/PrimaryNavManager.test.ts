import { describe, expect, it } from "vitest"

import { PrimaryNavManager } from "@/lib/navigation/PrimaryNavManager"

describe("PrimaryNavManager", () => {
  it("returns public destinations in a stable order when logged out", () => {
    const mgr = new PrimaryNavManager()
    const items = mgr.getItems({ isAuthed: false })

    expect(items).toHaveLength(6)
    expect(items.map((i) => i.label)).toEqual([
      "Home",
      "Game Analytics",
      "Pricing",
      "PG-101",
      "Development News",
      "Affiliates",
    ])
  })

  it("returns exactly 4 app-focused destinations in a stable order when logged in", () => {
    const mgr = new PrimaryNavManager()
    const items = mgr.getItems({ isAuthed: true })

    expect(items).toHaveLength(4)
    expect(items.map((i) => i.label)).toEqual(["Home", "AI Picks", "Games", "Insights"])
  })

  it("sets Home href based on auth state", () => {
    const mgr = new PrimaryNavManager()
    expect(mgr.getItems({ isAuthed: false })[0]?.href).toBe("/")
    expect(mgr.getItems({ isAuthed: true })[0]?.href).toBe("/")
  })

  it("resolves active destination for common routes", () => {
    const mgr = new PrimaryNavManager()

    expect(mgr.resolveActiveId("/")).toBe("home")
    expect(mgr.resolveActiveId("/app")).toBe("build")

    expect(mgr.resolveActiveId("/build")).toBe("build")
    expect(mgr.resolveActiveId("/parlays/same-game")).toBe("build")
    expect(mgr.resolveActiveId("/parlays/round-robin")).toBe("build")
    expect(mgr.resolveActiveId("/parlays/teasers")).toBe("build")

    expect(mgr.resolveActiveId("/analysis")).toBe("games")
    expect(mgr.resolveActiveId("/analysis/nfl/some-slug")).toBe("games")
    expect(mgr.resolveActiveId("/games/nfl/2025-01-01")).toBe("games")

    expect(mgr.resolveActiveId("/analytics")).toBe("insights")
    expect(mgr.resolveActiveId("/tools/upset-finder")).toBe("insights")
    expect(mgr.resolveActiveId("/social")).toBe("insights")
    expect(mgr.resolveActiveId("/parlays/history")).toBe("insights")

    expect(mgr.resolveActiveId("/profile")).toBe(null)
    expect(mgr.resolveActiveId("/billing")).toBe(null)
  })
})


