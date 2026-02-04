/**
 * Regression tests: Game Analysis Detail module gating.
 * - keyPlayers: only defined when ugie_v2.key_players.status is ready/limited AND players non-empty.
 * - availability: null when why_summary is placeholder ("Unable to assess...") and no real signals.
 */

import { describe, expect, it } from "vitest"

import { AnalysisDetailViewModelBuilder } from "@/lib/analysis/detail/AnalysisDetailViewModelBuilder"
import { buildUgieModulesViewModel } from "@/lib/analysis/detail/ugie/UgieV2ModulesBuilder"

function minimalAnalysis(overrides: {
  analysis_content?: Record<string, unknown>
} = {}) {
  return {
    id: "a1",
    slug: "nfl-week-1",
    league: "NFL",
    matchup: "Away @ Home",
    game_id: "g1",
    game_time: new Date().toISOString(),
    generated_at: new Date().toISOString(),
    version: 1,
    analysis_content: {
      ui_quick_take: {},
      ui_key_drivers: { positives: [], risks: [] },
      ui_bet_options: [],
      model_win_probability: { home_win_prob: 0.55, away_win_prob: 0.45 },
      ...overrides.analysis_content,
    },
  }
}

describe("AnalysisDetailViewModelBuilder — keyPlayers gating", () => {
  const builder = new AnalysisDetailViewModelBuilder()

  it("sets keyPlayers undefined when key_players.status is not ready/limited", () => {
    const analysis = minimalAnalysis({
      analysis_content: {
        ugie_v2: {
          pillars: {},
          key_players: {
            status: "unavailable",
            reason: "roster_missing_or_empty",
            players: [],
            allowlist_source: "roster_current_matchup_teams",
          },
        },
      },
    }) as any
    const vm = builder.build({ analysis, sport: "nfl" })
    expect(vm.keyPlayers).toBeUndefined()
  })

  it("sets keyPlayers undefined when key_players.players is empty", () => {
    const analysis = minimalAnalysis({
      analysis_content: {
        ugie_v2: {
          pillars: {},
          key_players: {
            status: "ready",
            reason: "",
            players: [],
            allowlist_source: "roster_current_matchup_teams",
          },
        },
      },
    }) as any
    const vm = builder.build({ analysis, sport: "nfl" })
    expect(vm.keyPlayers).toBeUndefined()
  })

  it("sets keyPlayers when status is ready and players non-empty", () => {
    const analysis = minimalAnalysis({
      analysis_content: {
        ugie_v2: {
          pillars: {},
          key_players: {
            status: "ready",
            reason: "",
            players: [
              { name: "Player A", team: "home", role: "QB", impact: "High", why: "Key.", confidence: 0.8 },
            ],
            allowlist_source: "roster_current_matchup_teams",
          },
        },
      },
    }) as any
    const vm = builder.build({ analysis, sport: "nfl" })
    expect(vm.keyPlayers).toBeDefined()
    expect(vm.keyPlayers?.homePlayers.length).toBe(1)
  })

  it("sets keyPlayers when status is limited and players non-empty", () => {
    const analysis = minimalAnalysis({
      analysis_content: {
        ugie_v2: {
          pillars: {},
          key_players: {
            status: "limited",
            reason: "roster_only_no_stats",
            players: [
              { name: "Player B", team: "away", role: "WR", impact: "Medium", why: "Usage.", confidence: 0.65 },
            ],
            allowlist_source: "roster_current_matchup_teams",
          },
        },
      },
    }) as any
    const vm = builder.build({ analysis, sport: "nfl" })
    expect(vm.keyPlayers).toBeDefined()
    expect(vm.keyPlayers?.awayPlayers.length).toBe(1)
  })
})

describe("UgieV2ModulesBuilder — availability gating", () => {
  it("sets availability null when why_summary is placeholder and no signals", () => {
    const ugie = {
      pillars: {
        availability: {
          score: 0.5,
          confidence: 0.5,
          signals: [],
          why_summary: "Unable to assess injury impact.",
          top_edges: [],
        },
        efficiency: { score: 0.5, confidence: 0.5, signals: [], why_summary: "", top_edges: [] },
        matchup_fit: { score: 0.5, confidence: 0.5, signals: [], why_summary: "", top_edges: [] },
        script_stability: { score: 0.5, confidence: 0.5, signals: [], why_summary: "", top_edges: [] },
        market_alignment: { score: 0.5, confidence: 0.5, signals: [], why_summary: "", top_edges: [] },
      },
      confidence_score: 0.5,
      risk_level: "Medium",
      data_quality: { status: "Partial", missing: [], stale: [], provider: "" },
      recommended_action: "",
      market_snapshot: {},
    } as any
    const vm = buildUgieModulesViewModel({ ugie, sport: "nfl" })
    expect(vm.availability).toBeNull()
  })

  it("sets availability when pillar has real signals", () => {
    const ugie = {
      pillars: {
        availability: {
          score: 0.5,
          confidence: 0.8,
          signals: [
            { key: "home_injury_impact", value: 0.3, weight: 0.5, direction: "home", explain: "Key out." },
          ],
          why_summary: "Home side impacted by injury.",
          top_edges: [],
        },
        efficiency: { score: 0.5, confidence: 0.5, signals: [], why_summary: "", top_edges: [] },
        matchup_fit: { score: 0.5, confidence: 0.5, signals: [], why_summary: "", top_edges: [] },
        script_stability: { score: 0.5, confidence: 0.5, signals: [], why_summary: "", top_edges: [] },
        market_alignment: { score: 0.5, confidence: 0.5, signals: [], why_summary: "", top_edges: [] },
      },
      confidence_score: 0.5,
      risk_level: "Medium",
      data_quality: { status: "Good", missing: [], stale: [], provider: "" },
      recommended_action: "",
      market_snapshot: {},
    } as any
    const vm = buildUgieModulesViewModel({ ugie, sport: "nfl" })
    expect(vm.availability).not.toBeNull()
    expect(vm.availability!.signals).toHaveLength(1)
  })

  it("exposes rosterStatus and injuriesStatus from data_quality for Fetching badges", () => {
    const ugie = {
      pillars: {
        availability: { score: 0.5, confidence: 0.5, signals: [], why_summary: "", top_edges: [] },
        efficiency: { score: 0.5, confidence: 0.5, signals: [], why_summary: "", top_edges: [] },
        matchup_fit: { score: 0.5, confidence: 0.5, signals: [], why_summary: "", top_edges: [] },
        script_stability: { score: 0.5, confidence: 0.5, signals: [], why_summary: "", top_edges: [] },
        market_alignment: { score: 0.5, confidence: 0.5, signals: [], why_summary: "", top_edges: [] },
      },
      confidence_score: 0.5,
      risk_level: "Medium",
      data_quality: {
        status: "Partial",
        missing: [],
        stale: [],
        provider: "",
        roster: "missing",
        injuries: "stale",
      },
      recommended_action: "",
      market_snapshot: {},
    } as any
    const vm = buildUgieModulesViewModel({ ugie, sport: "nfl" })
    expect(vm.rosterStatus).toBe("missing")
    expect(vm.injuriesStatus).toBe("stale")
  })
})
