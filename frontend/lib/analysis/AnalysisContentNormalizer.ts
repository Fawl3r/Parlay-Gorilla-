import type {
  BestBet,
  GameAnalysisContent,
  GameAnalysisResponse,
  MatchupEdges,
  ModelWinProbability,
  SameGameParlay,
  SameGameParlays,
  SpreadPick,
  TotalPick,
  TrendAnalysis,
} from "@/lib/api"

export class AnalysisContentNormalizer {
  static normalizeResponse(input: unknown): GameAnalysisResponse {
    const raw = this._asObject(input)
    const nowIso = new Date().toISOString()

    const normalized: any = {
      id: String(raw.id ?? ""),
      slug: String(raw.slug ?? ""),
      league: String(raw.league ?? raw.sport ?? "NFL"),
      matchup: String(raw.matchup ?? raw.slug ?? "Unknown Matchup"),
      game_id: String(raw.game_id ?? raw.gameId ?? ""),
      game_time: String(
        raw.game_time ??
          raw.gameTime ??
          raw.game_date ??
          raw.gameDate ??
          raw.generated_at ??
          raw.generatedAt ??
          nowIso
      ),
      analysis_content: this.normalizeContent(raw.analysis_content ?? raw.analysisContent, raw),
      seo_metadata: this._asOptionalObject(raw.seo_metadata ?? raw.seoMetadata),
      generated_at: String(raw.generated_at ?? raw.generatedAt ?? nowIso),
      expires_at: raw.expires_at ?? raw.expiresAt ?? null,
      version: this._asFiniteNumber(raw.version, 1),
    }

    return normalized as GameAnalysisResponse
  }

  static normalizeContent(input: unknown, analysis?: unknown): GameAnalysisContent {
    const raw = this._asObject(input)
    const analysisObj = this._asObject(analysis)

    const matchup = this._asNonEmptyString(analysisObj.matchup) ?? "this matchup"

    const openingSummary =
      this._asNonEmptyString(raw.opening_summary) ??
      this._asNonEmptyString(raw.openingSummary) ??
      `Analysis is being prepared for ${matchup}. Please refresh in a moment.`

    return {
      headline: this._asNonEmptyString(raw.headline) ?? this._asNonEmptyString(raw.title) ?? undefined,
      subheadline: this._asNonEmptyString(raw.subheadline) ?? this._asNonEmptyString(raw.subtitle) ?? undefined,
      opening_summary: openingSummary,
      offensive_matchup_edges: this._normalizeMatchupEdges(raw.offensive_matchup_edges),
      defensive_matchup_edges: this._normalizeMatchupEdges(raw.defensive_matchup_edges),
      key_stats: this._normalizeStringList(raw.key_stats),
      ats_trends: this._normalizeTrendAnalysis(raw.ats_trends),
      totals_trends: this._normalizeTrendAnalysis(raw.totals_trends),
      weather_considerations: this._asString(raw.weather_considerations, ""),
      weather_data: this._asOptionalObject(raw.weather_data) as any,
      model_win_probability: this._normalizeWinProbability(raw.model_win_probability),
      ai_spread_pick: this._normalizeSpreadPick(raw.ai_spread_pick),
      ai_total_pick: this._normalizeTotalPick(raw.ai_total_pick),
      best_bets: this._normalizeBestBets(raw.best_bets),
      same_game_parlays: this._normalizeSameGameParlays(raw.same_game_parlays),
      ui_quick_take: this._asOptionalObject(raw.ui_quick_take ?? raw.uiQuickTake) as any,
      ui_key_drivers: this._asOptionalObject(raw.ui_key_drivers ?? raw.uiKeyDrivers) as any,
      ui_bet_options: Array.isArray(raw.ui_bet_options ?? raw.uiBetOptions)
        ? ((raw.ui_bet_options ?? raw.uiBetOptions) as any)
        : undefined,
      ui_matchup_cards: Array.isArray(raw.ui_matchup_cards ?? raw.uiMatchupCards)
        ? ((raw.ui_matchup_cards ?? raw.uiMatchupCards) as any)
        : undefined,
      ui_trends: Array.isArray(raw.ui_trends ?? raw.uiTrends)
        ? this._normalizeStringList(raw.ui_trends ?? raw.uiTrends)
        : undefined,
      full_article: this._asString(raw.full_article, ""),
      outcome_paths: this._asOptionalObject(raw.outcome_paths ?? raw.outcomePaths),
      confidence_breakdown: this._asOptionalObject(raw.confidence_breakdown ?? raw.confidenceBreakdown),
      market_disagreement: this._asOptionalObject(raw.market_disagreement ?? raw.marketDisagreement),
      portfolio_guidance: this._asOptionalObject(raw.portfolio_guidance ?? raw.portfolioGuidance),
      prop_recommendations: this._asOptionalObject(raw.prop_recommendations ?? raw.propRecommendations),
      delta_summary: this._asOptionalObject(raw.delta_summary ?? raw.deltaSummary),
      seo_structured_data: raw.seo_structured_data ?? raw.seoStructuredData,
      generation: this._asOptionalObject(raw.generation),
      ugie_v2: this._asOptionalObject(raw.ugie_v2 ?? raw.ugieV2),
    } as GameAnalysisContent
  }

  // ---------------------------------------------------------------------------
  // Normalizers (private)
  // ---------------------------------------------------------------------------

  private static _normalizeWinProbability(input: unknown): ModelWinProbability {
    const raw = this._asObject(input)
    const homeRaw = this._asFiniteNumber(raw.home_win_prob, NaN)
    const awayRaw = this._asFiniteNumber(raw.away_win_prob, NaN)

    let home = homeRaw
    let away = awayRaw

    if (!Number.isFinite(home) || !Number.isFinite(away)) {
      home = 0.52
      away = 0.48
    }

    // Clamp and normalize to sum ~1.
    home = this._clamp01(home)
    away = this._clamp01(away)

    if (home <= 0 || away <= 0 || home >= 1 || away >= 1) {
      home = 0.52
      away = 0.48
    }

    const total = home + away
    if (total > 0) {
      home = home / total
      away = away / total
    } else {
      home = 0.52
      away = 0.48
    }

    return {
      home_win_prob: home,
      away_win_prob: away,
      explanation:
        this._asNonEmptyString(raw.explanation) ??
        "Win probability currently unavailable (fallback home advantage applied).",
      ai_confidence: this._asFiniteNumber(raw.ai_confidence, 15),
      calculation_method: this._asNonEmptyString(raw.calculation_method) ?? "minimal_fallback",
      score_projection: this._asNonEmptyString(raw.score_projection) ?? undefined,
    }
  }

  private static _normalizeMatchupEdges(input: unknown): MatchupEdges {
    const raw = this._asObject(input)
    return {
      home_advantage: this._asString(raw.home_advantage, ""),
      away_advantage: this._asString(raw.away_advantage, ""),
      key_matchup: this._asString(raw.key_matchup, ""),
    }
  }

  private static _normalizeTrendAnalysis(input: unknown): TrendAnalysis {
    const raw = this._asObject(input)
    return {
      home_team_trend: this._asString(raw.home_team_trend, ""),
      away_team_trend: this._asString(raw.away_team_trend, ""),
      analysis: this._asString(raw.analysis, ""),
    }
  }

  private static _normalizeSpreadPick(input: unknown): SpreadPick {
    const raw = this._asObject(input)
    return {
      pick: this._asString(raw.pick, ""),
      confidence: this._asFiniteNumber(raw.confidence, 0),
      rationale: this._asString(raw.rationale, ""),
    }
  }

  private static _normalizeTotalPick(input: unknown): TotalPick {
    const raw = this._asObject(input)
    return {
      pick: this._asString(raw.pick, ""),
      confidence: this._asFiniteNumber(raw.confidence, 0),
      rationale: this._asString(raw.rationale, ""),
    }
  }

  private static _normalizeBestBets(input: unknown): BestBet[] {
    if (!Array.isArray(input)) return []
    const out: BestBet[] = []
    for (const item of input) {
      const raw = this._asObject(item)
      out.push({
        bet_type: this._asString(raw.bet_type, ""),
        pick: this._asString(raw.pick, ""),
        confidence: this._asFiniteNumber(raw.confidence, 0),
        rationale: this._asString(raw.rationale, ""),
      })
    }
    return out
  }

  private static _normalizeSameGameParlays(input: unknown): SameGameParlays {
    const raw = this._asObject(input)
    return {
      safe_3_leg: this._normalizeSameGameParlay(raw.safe_3_leg),
      balanced_6_leg: this._normalizeSameGameParlay(raw.balanced_6_leg),
      degen_10_20_leg: this._normalizeSameGameParlay(raw.degen_10_20_leg),
    }
  }

  private static _normalizeSameGameParlay(input: unknown): SameGameParlay {
    const raw = this._asObject(input)
    return {
      legs: Array.isArray(raw.legs) ? raw.legs : [],
      hit_probability: this._asFiniteNumber(raw.hit_probability, 0),
      confidence: this._asFiniteNumber(raw.confidence, 0),
    }
  }

  private static _normalizeStringList(input: unknown): string[] {
    if (!Array.isArray(input)) return []
    const out: string[] = []
    for (const item of input) {
      if (typeof item === "string" && item.trim()) out.push(item)
    }
    return out
  }

  private static _clamp01(value: number): number {
    if (!Number.isFinite(value)) return 0
    return Math.max(0, Math.min(1, value))
  }

  private static _asFiniteNumber(value: unknown, fallback: number): number {
    try {
      const n = typeof value === "number" ? value : Number(value)
      return Number.isFinite(n) ? n : fallback
    } catch {
      return fallback
    }
  }

  private static _asString(value: unknown, fallback: string): string {
    return typeof value === "string" ? value : fallback
  }

  private static _asNonEmptyString(value: unknown): string | null {
    if (typeof value !== "string") return null
    const trimmed = value.trim()
    return trimmed ? trimmed : null
  }

  private static _asObject(value: unknown): Record<string, any> {
    if (value && typeof value === "object") return value as Record<string, any>
    return {}
  }

  private static _asOptionalObject(value: unknown): Record<string, any> | undefined {
    if (value && typeof value === "object") return value as Record<string, any>
    return undefined
  }
}




