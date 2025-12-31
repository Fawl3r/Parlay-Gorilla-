import { describe, expect, it } from "vitest"

import { generateSchemaGraph } from "@/lib/structured-data"

function buildSampleAnalysis(): any {
  return {
    id: "analysis_1",
    slug: "nfl/bills-vs-chiefs-week-10-2025",
    league: "NFL",
    matchup: "Buffalo Bills @ Kansas City Chiefs",
    game_id: "game_1",
    game_time: "2025-12-01T01:00:00.000Z",
    generated_at: "2025-11-30T12:00:00.000Z",
    expires_at: null,
    version: 1,
    seo_metadata: {
      title: "Buffalo Bills vs Kansas City Chiefs Prediction & Picks",
      description: "AI-powered betting analysis, win probabilities, and best bets.",
      keywords: "Bills vs Chiefs, prediction, picks",
    },
    analysis_content: {
      opening_summary: "Kansas City is favored due to efficiency edges and home-field advantage.",
      offensive_matchup_edges: {
        home_advantage: "Home offense advantage",
        away_advantage: "Away offense advantage",
        key_matchup: "Key matchup",
      },
      defensive_matchup_edges: {
        home_advantage: "Home defense advantage",
        away_advantage: "Away defense advantage",
        key_matchup: "Key defensive matchup",
      },
      key_stats: ["QB efficiency edge", "Red zone trend", "Turnover variance"],
      ats_trends: {
        home_team_trend: "Home ATS trend",
        away_team_trend: "Away ATS trend",
        analysis: "ATS analysis",
      },
      totals_trends: {
        home_team_trend: "Home totals trend",
        away_team_trend: "Away totals trend",
        analysis: "Totals analysis",
      },
      weather_considerations: "Weather looks neutral.",
      model_win_probability: {
        home_win_prob: 0.62,
        away_win_prob: 0.38,
        explanation: "Model uses team stats and market data.",
        ai_confidence: 72,
      },
      ai_spread_pick: {
        pick: "Chiefs -3",
        confidence: 68,
        rationale: "Matchup edges favor the home side.",
      },
      ai_total_pick: {
        pick: "Over 47.5",
        confidence: 60,
        rationale: "Expected pace supports points.",
      },
      best_bets: [
        {
          bet_type: "Moneyline",
          pick: "Chiefs ML",
          confidence: 70,
          rationale: "Higher win probability and home advantage.",
        },
      ],
      same_game_parlays: {
        safe_3_leg: { legs: [], hit_probability: 0.12, confidence: 55 },
        balanced_6_leg: { legs: [], hit_probability: 0.05, confidence: 40 },
        degen_10_20_leg: { legs: [], hit_probability: 0.01, confidence: 20 },
      },
      full_article: "Full article content",
    },
  }
}

describe("structured-data (JSON-LD)", () => {
  it("generates a schema graph containing Article, SportsEvent, and FAQPage", () => {
    const analysis = buildSampleAnalysis()
    const graph = generateSchemaGraph(analysis) as any

    expect(graph["@context"]).toBe("https://schema.org")
    expect(Array.isArray(graph["@graph"])).toBe(true)

    const types = (graph["@graph"] as any[]).map((node) => node?.["@type"]).filter(Boolean)
    expect(types).toContain("Article")
    expect(types).toContain("SportsEvent")
    expect(types).toContain("FAQPage")
  })

  it("uses a real logo URL and a canonical analysis URL in the Article node", () => {
    const analysis = buildSampleAnalysis()
    const graph = generateSchemaGraph(analysis) as any

    const article = (graph["@graph"] as any[]).find((node) => node?.["@type"] === "Article")
    expect(article).toBeTruthy()

    expect(String(article?.publisher?.logo?.url || "")).toContain("/images/newlogohead.png")
    expect(String(article?.mainEntityOfPage?.["@id"] || "")).toContain("/analysis/nfl/")
  })

  it("includes a 'Who will win' FAQ entry (featured snippet eligibility)", () => {
    const analysis = buildSampleAnalysis()
    const graph = generateSchemaGraph(analysis) as any

    const faq = (graph["@graph"] as any[]).find((node) => node?.["@type"] === "FAQPage")
    expect(faq).toBeTruthy()

    const first = (faq?.mainEntity || [])[0]
    expect(String(first?.name || "")).toMatch(/who will win/i)
    expect(String(first?.acceptedAnswer?.text || "")).toMatch(/projected to win/i)
  })
})


