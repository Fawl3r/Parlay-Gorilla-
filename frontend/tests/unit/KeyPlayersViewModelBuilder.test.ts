import { describe, expect, it } from "vitest"

import { buildKeyPlayersViewModel } from "@/lib/analysis/detail/keyPlayers/KeyPlayersViewModelBuilder"

describe("buildKeyPlayersViewModel", () => {
  it("groups players by home and away", () => {
    const vm = buildKeyPlayersViewModel({
      keyPlayers: {
        status: "limited",
        reason: "roster_only_no_stats",
        players: [
          {
            name: "Home QB",
            team: "home",
            role: "QB",
            impact: "High",
            why: "Passing efficiency is central.",
            confidence: 0.7,
          },
          {
            name: "Away WR",
            team: "away",
            role: "WR",
            impact: "Medium",
            why: "Usage and red-zone role.",
            confidence: 0.65,
          },
        ],
        allowlist_source: "roster_current_matchup_teams",
      },
    })
    expect(vm.status).toBe("limited")
    expect(vm.homePlayers).toHaveLength(1)
    expect(vm.homePlayers[0].name).toBe("Home QB")
    expect(vm.awayPlayers).toHaveLength(1)
    expect(vm.awayPlayers[0].name).toBe("Away WR")
    expect(vm.verifiedLabel).toBe("Verified current rosters")
    expect(vm.limitedNote).toBeDefined()
    expect(vm.showRosterVerifiedNote).toBe(false)
  })

  it("unavailable status has empty home and away players", () => {
    const vm = buildKeyPlayersViewModel({
      keyPlayers: {
        status: "unavailable",
        reason: "roster_missing_or_empty",
        players: [],
        allowlist_source: "roster_current_matchup_teams",
      },
    })
    expect(vm.status).toBe("unavailable")
    expect(vm.homePlayers).toHaveLength(0)
    expect(vm.awayPlayers).toHaveLength(0)
    expect(vm.limitedNote).toBeUndefined()
  })

  it("showRosterVerifiedNote is true when redactionCount > 0", () => {
    const vm = buildKeyPlayersViewModel({
      keyPlayers: {
        status: "available",
        players: [],
        allowlist_source: "roster_current_matchup_teams",
      },
      redactionCount: 2,
    })
    expect(vm.showRosterVerifiedNote).toBe(true)
  })

  it("passes through updatedAt when present", () => {
    const vm = buildKeyPlayersViewModel({
      keyPlayers: {
        status: "limited",
        players: [],
        allowlist_source: "roster_current_matchup_teams",
        updated_at: "2025-01-15T12:00:00Z",
      },
    })
    expect(vm.updatedAt).toBe("2025-01-15T12:00:00Z")
  })
})
