import { describe, expect, it } from "vitest"

import { UpsetFinderEmptyStateModelBuilder } from "@/app/tools/upset-finder/_components/UpsetFinderEmptyStateModelBuilder"

describe("UpsetFinderEmptyStateModelBuilder", () => {
  it("renders locked state with unlock action", () => {
    const builder = new UpsetFinderEmptyStateModelBuilder()
    const model = builder.build({
      access: { can_view_candidates: false, reason: "premium_required" },
      meta: { games_scanned: 10, games_with_odds: 5, missing_odds: 5 },
      candidatesCount: 0,
      days: 7,
      minEdgePct: 3,
    })

    expect(model.title).toContain("Unlock")
    expect(model.actions.map((a) => a.id)).toContain("unlock")
  })

  it("renders no_upcoming_games when games_scanned == 0", () => {
    const builder = new UpsetFinderEmptyStateModelBuilder()
    const model = builder.build({
      access: { can_view_candidates: true, reason: null },
      meta: { games_scanned: 0, games_with_odds: 0, missing_odds: 0 },
      candidatesCount: 0,
      days: 7,
      minEdgePct: 3,
    })

    expect(model.title).toContain("No upcoming games")
    expect(model.actions.map((a) => a.id)).toContain("set_days_14")
  })

  it("renders no_odds when games_scanned > 0 and games_with_odds == 0", () => {
    const builder = new UpsetFinderEmptyStateModelBuilder()
    const model = builder.build({
      access: { can_view_candidates: true, reason: null },
      meta: { games_scanned: 12, games_with_odds: 0, missing_odds: 12 },
      candidatesCount: 0,
      days: 7,
      minEdgePct: 3,
    })

    expect(model.title).toContain("Odds")
    expect(model.actions.map((a) => a.id)).toContain("set_sport_all")
  })

  it("renders threshold state when odds exist but candidates are empty", () => {
    const builder = new UpsetFinderEmptyStateModelBuilder()
    const model = builder.build({
      access: { can_view_candidates: true, reason: null },
      meta: { games_scanned: 20, games_with_odds: 10, missing_odds: 10 },
      candidatesCount: 0,
      days: 7,
      minEdgePct: 4,
    })

    expect(model.title).toContain("No edges at 4%")
    const ids = model.actions.map((a) => a.id)
    expect(ids).toContain("set_min_edge_2")
    expect(ids).toContain("set_min_edge_1")
    expect(ids).toContain("set_days_14")
  })
})

