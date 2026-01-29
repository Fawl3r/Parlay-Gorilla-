import type { GameAnalysisResponse } from "@/lib/api"
import { parseMatchup } from "@/lib/team-assets"

import { CopySanitizer } from "./CopySanitizer"
import { RiskClassifier, type ConfidenceLevel, type RiskLevel } from "./RiskClassifier"
import { SportAdaptationRegistry, type MarketType } from "./SportAdaptationRegistry"
import type { AnalysisDetailViewModel } from "./AnalysisDetailViewModel"
import { buildUgieModulesViewModel } from "./ugie/UgieV2ModulesBuilder"

export type { AnalysisDetailViewModel, AnalysisDetailPrefill, BetOptionKey } from "./AnalysisDetailViewModel"

function formatDateLabel(isoOrDateLike: string | Date): string {
  const d = typeof isoOrDateLike === "string" ? new Date(isoOrDateLike) : isoOrDateLike
  if (!Number.isFinite(d.getTime())) return ""
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}

function clampPct(value: number): number {
  if (!Number.isFinite(value)) return 0
  return Math.max(0, Math.min(100, Math.round(value)))
}

function clamp01(value: number): number {
  if (!Number.isFinite(value)) return 0
  return Math.max(0, Math.min(1, value))
}

function parseNflWeekFromSlug(slug: string): string | null {
  const match = String(slug || "").match(/week-(\d+|none)/i)
  if (!match) return null
  const raw = String(match[1] || "").toLowerCase()
  if (!raw || raw === "none") return null
  return raw
}

export class AnalysisDetailViewModelBuilder {
  build(params: { analysis: GameAnalysisResponse; sport: string }): AnalysisDetailViewModel {
    const { analysis, sport } = params
    const adaptation = SportAdaptationRegistry.resolve(sport || analysis.league)

    const content: any = analysis.analysis_content || {}
    const uiQuickTake: any = content.ui_quick_take
    const uiKeyDrivers: any = content.ui_key_drivers
    const uiBetOptions: any = content.ui_bet_options
    const uiMatchupCards: any = content.ui_matchup_cards
    const uiTrends: any = content.ui_trends

    const matchup = String(analysis.matchup || "").trim()
    const teams = parseMatchup(matchup)
    const awayTeam = String(teams.awayTeam || "").trim()
    const homeTeam = String(teams.homeTeam || "").trim()
    const separator: "@" | "vs" = matchup.includes("@") ? "@" : "vs"

    const probs = content.model_win_probability || {}
    const homeProb = clamp01(Number(probs.home_win_prob))
    const awayProb = clamp01(Number(probs.away_win_prob))
    const derivedFavoredTeam = homeProb >= awayProb ? (homeTeam || "Home") : (awayTeam || "Away")
    const uiFavoredTeam = String(uiQuickTake?.favored_team || "").trim()
    const favoredTeam = uiFavoredTeam || derivedFavoredTeam

    const derivedFavoredProb = Math.max(homeProb, awayProb)
    const uiFavoredProb = clamp01(Number(uiQuickTake?.confidence_percent) / 100.0)
    const favoredProb = Number.isFinite(Number(uiQuickTake?.confidence_percent)) ? uiFavoredProb : derivedFavoredProb

    const aiConfidencePercent = clampPct(Number(probs.ai_confidence ?? 50))
    const derivedConfidenceLevel = RiskClassifier.confidenceLevelFromPercent(aiConfidencePercent)

    const limitedData =
      String(content.opening_summary || "").toLowerCase().includes("limited") ||
      String(probs.calculation_method || "").toLowerCase().includes("fallback") ||
      String(probs.explanation || "").toLowerCase().includes("unavailable") ||
      Boolean(String(uiQuickTake?.limited_data_note || "").trim())

    const derivedRiskLevel = RiskClassifier.riskLevelFromSignals({
      aiConfidencePercent,
      homeWinProb: homeProb,
      awayWinProb: awayProb,
      limitedData,
    })

    const confidenceLevel = (["Low", "Medium", "High"] as const).includes(String(uiQuickTake?.confidence_level || "") as any)
      ? (String(uiQuickTake?.confidence_level) as ConfidenceLevel)
      : derivedConfidenceLevel

    const riskLevel = (["Low", "Medium", "High"] as const).includes(String(uiQuickTake?.risk_level || "") as any)
      ? (String(uiQuickTake?.risk_level) as RiskLevel)
      : derivedRiskLevel

    const week = adaptation.sportSlug === "nfl" ? parseNflWeekFromSlug(analysis.slug) : null
    const title = awayTeam && homeTeam ? `${awayTeam} vs ${homeTeam}` : matchup || "Game Analysis"

    const subtitleParts: string[] = []
    if (analysis.league) subtitleParts.push(String(analysis.league))
    if (week) subtitleParts.push(`Week ${week}`)
    const dateLabel = formatDateLabel(analysis.game_time || analysis.generated_at)
    if (dateLabel) subtitleParts.push(dateLabel)
    const subtitle = subtitleParts.length ? subtitleParts.join(" • ") : undefined

    const lastUpdatedLabel = analysis.generated_at ? `Data updated: ${formatDateLabel(analysis.generated_at)}` : undefined

    const derivedRecommendation = this._buildRecommendation({
      favoredTeam,
      spreadPick: content.ai_spread_pick,
      totalPick: content.ai_total_pick,
      bestBets: content.best_bets,
    })

    const derivedWhyText = this._buildWhyText({
      openingSummary: content.opening_summary,
    })

    const derivedDrivers = this._buildKeyDrivers({
      keyStats: content.key_stats,
      openingSummary: content.opening_summary,
      riskLevel,
    })

    let betOptions = this._buildBetOptions({
      adaptationSport: adaptation.sportSlug,
      gameId: analysis.game_id,
      homeTeam,
      awayTeam,
      homeProb,
      awayProb,
      aiConfidencePercent,
      riskLevel,
      spreadPick: content.ai_spread_pick,
      totalPick: content.ai_total_pick,
      tabConfig: adaptation.betTabs,
    })

    if (Array.isArray(uiBetOptions)) {
      betOptions = this._overlayBetOptionsFromUi(betOptions, uiBetOptions)
    }

    let matchupCards = this._buildMatchupCards({
      awayTeam,
      homeTeam,
      units: adaptation.units,
      offensiveEdges: content.offensive_matchup_edges,
      defensiveEdges: content.defensive_matchup_edges,
    })

    if (Array.isArray(uiMatchupCards)) {
      matchupCards = uiMatchupCards
        .map((c: any) => ({
          title: String(c?.title || "").trim(),
          summary: CopySanitizer.sanitizeMainCopy(String(c?.summary || "")),
          bulletInsights: Array.isArray(c?.bullets) ? c.bullets.map((b: any) => CopySanitizer.sanitizeMainCopy(String(b || ""))).filter(Boolean) : [],
        }))
        .filter((c: any) => c.title || c.summary || (c.bulletInsights?.length || 0) > 0)
    }

    const trends = Array.isArray(uiTrends)
      ? uiTrends.map((t: any) => CopySanitizer.sanitizeMainCopy(String(t || ""))).filter(Boolean).slice(0, 4)
      : this._buildTrends({
      ats: content.ats_trends,
      totals: content.totals_trends,
      weather: content.weather_considerations,
    })

    const limitedDataNote = String(uiQuickTake?.limited_data_note || "").trim()
      ? String(uiQuickTake?.limited_data_note || "").trim()
      : limitedData
        ? "This matchup has limited historical data. The AI adjusted confidence accordingly."
        : undefined

    return {
      header: {
        title,
        subtitle,
        lastUpdatedLabel,
        awayTeam: awayTeam || undefined,
        homeTeam: homeTeam || undefined,
        separator,
        sport: adaptation.sportSlug,
      },
      quickTake: {
        sportIcon: adaptation.sportIcon,
        favoredTeam,
        confidencePercent: Number.isFinite(Number(uiQuickTake?.confidence_percent))
          ? clampPct(Number(uiQuickTake?.confidence_percent))
          : clampPct(favoredProb * 100),
        confidenceLevel,
        riskLevel,
        recommendation: String(uiQuickTake?.recommendation || "").trim() || derivedRecommendation,
        whyText: String(uiQuickTake?.why || "").trim() || derivedWhyText,
      },
      keyDrivers: {
        positives: Array.isArray(uiKeyDrivers?.positives)
          ? uiKeyDrivers.positives.map((x: any) => CopySanitizer.sanitizeMainCopy(String(x || ""))).filter(Boolean).slice(0, 2)
          : derivedDrivers.positives,
        risks: Array.isArray(uiKeyDrivers?.risks)
          ? uiKeyDrivers.risks.map((x: any) => CopySanitizer.sanitizeMainCopy(String(x || ""))).filter(Boolean).slice(0, 1)
          : derivedDrivers.risks,
      },
      probability: {
        teamA: favoredTeam,
        teamB: favoredTeam === homeTeam ? awayTeam || "Opponent" : homeTeam || "Opponent",
        probabilityA: clampPct(favoredProb * 100),
        probabilityB: clampPct((1 - favoredProb) * 100),
      },
      betOptions,
      matchupCards,
      trends,
      limitedDataNote,
      ugieModules,
    }
  }

  private _overlayBetOptionsFromUi(
    base: AnalysisDetailViewModel["betOptions"],
    uiOptions: any[]
  ): AnalysisDetailViewModel["betOptions"] {
    const byId = new Map<string, any>()
    for (const raw of uiOptions) {
      const id = String(raw?.id || "").trim().toLowerCase()
      if (!id) continue
      byId.set(id, raw)
    }

    return base.map((b) => {
      const raw = byId.get(String(b.id).toLowerCase())
      if (!raw) return b
      const confidenceLevel = (["Low", "Medium", "High"] as const).includes(String(raw?.confidence_level || "") as any)
        ? (String(raw?.confidence_level) as ConfidenceLevel)
        : b.confidenceLevel
      const riskLevel = (["Low", "Medium", "High"] as const).includes(String(raw?.risk_level || "") as any)
        ? (String(raw?.risk_level) as RiskLevel)
        : b.riskLevel
      return {
        ...b,
        label: String(raw?.label || "").trim() || b.label,
        lean: CopySanitizer.sanitizeMainCopy(String(raw?.lean || "")) || b.lean,
        confidenceLevel,
        riskLevel,
        explanation: CopySanitizer.sanitizeMainCopy(String(raw?.explanation || "")) || b.explanation,
      }
    })
  }

  private _buildRecommendation(params: {
    favoredTeam: string
    spreadPick: any
    totalPick: any
    bestBets: any
  }): string {
    const favoredTeam = String(params.favoredTeam || "").trim()

    const bestBets = Array.isArray(params.bestBets) ? params.bestBets : []
    const ml = bestBets.find((b: any) => String(b?.bet_type || "").toLowerCase() === "moneyline")
    const mlPick = String(ml?.pick || "").trim()

    const spreadPick = String(params.spreadPick?.pick || "").trim()

    // One recommendation only (spec rule).
    if (mlPick) return CopySanitizer.sanitizeMainCopy(mlPick)
    if (spreadPick) return CopySanitizer.sanitizeMainCopy(spreadPick)
    return favoredTeam ? `${favoredTeam} ML` : "No clear recommendation yet."
  }

  private _buildWhyText(params: { openingSummary: any }): string {
    const summary = CopySanitizer.sanitizeMainCopy(String(params.openingSummary || ""))
    // Spec: 1–2 sentences, plain English.
    return CopySanitizer.toSingleSentence(summary, 240)
  }

  private _buildKeyDrivers(params: {
    keyStats: any
    openingSummary: any
    riskLevel: RiskLevel
  }): { positives: string[]; risks: string[] } {
    const keyStats = Array.isArray(params.keyStats) ? params.keyStats : []
    const cleaned = keyStats
      .map((s: any) => CopySanitizer.stripPercentages(CopySanitizer.sanitizeMainCopy(String(s || ""))))
      .map((s) => s.replace(/^\W+/, "").trim())
      .filter(Boolean)

    const positives = cleaned.slice(0, 2)

    const riskFromSummary = String(params.openingSummary || "")
      .split(/(?<=[.!?])\s+/)
      .find((s) => /risk|volatile|inconsistent|injur|unknown/i.test(s))

    const risks: string[] = []
    if (riskFromSummary) risks.push(CopySanitizer.toSingleSentence(CopySanitizer.sanitizeMainCopy(riskFromSummary), 120))
    if (!risks.length) {
      risks.push(params.riskLevel === "High" ? "This game has higher volatility than average." : "There are a few ways this can go sideways.")
    }

    return { positives, risks: risks.slice(0, 1) }
  }

  private _buildBetOptions(params: {
    adaptationSport: string
    gameId: string
    homeTeam: string
    awayTeam: string
    homeProb: number
    awayProb: number
    aiConfidencePercent: number
    riskLevel: RiskLevel
    spreadPick: any
    totalPick: any
    tabConfig: Array<{ marketType: MarketType; label: string }>
  }): AnalysisDetailViewModel["betOptions"] {
    const out: AnalysisDetailViewModel["betOptions"] = []

    const favoredTeam = params.homeProb >= params.awayProb ? params.homeTeam : params.awayTeam
    const moneylineLean = favoredTeam ? `${favoredTeam} ML` : "No lean"
    const spreadLean = String(params.spreadPick?.pick || "").trim()
    const totalLean = String(params.totalPick?.pick || "").trim()

    const confLevel = RiskClassifier.confidenceLevelFromPercent(params.aiConfidencePercent)

    const parseFirstNumber = (text: string): number | undefined => {
      const match = String(text || "").match(/[+-]?\d+(?:\.\d+)?/)
      if (!match) return undefined
      const n = Number(match[0])
      return Number.isFinite(n) ? n : undefined
    }

    const normalize = (s: string) => String(s || "").toLowerCase()

    for (const tab of params.tabConfig) {
      if (tab.marketType === "h2h") {
        out.push({
          id: "moneyline",
          label: tab.label,
          lean: CopySanitizer.sanitizeMainCopy(moneylineLean),
          confidenceLevel: confLevel,
          riskLevel: params.riskLevel,
          explanation: "Back the side the AI expects to win most often.",
          prefill: favoredTeam
            ? {
                sport: params.adaptationSport,
                gameId: params.gameId,
                marketType: "h2h",
                pick: favoredTeam,
              }
            : undefined,
        })
      } else if (tab.marketType === "spreads") {
        if (!spreadLean) continue
        const spreadPoint = parseFirstNumber(spreadLean)
        const lower = normalize(spreadLean)
        const pickValue =
          lower.includes("home") || lower.includes(normalize(params.homeTeam))
            ? "home"
            : lower.includes("away") || lower.includes(normalize(params.awayTeam))
              ? "away"
              : params.homeProb >= params.awayProb
                ? "home"
                : "away"
        out.push({
          id: "spread",
          label: tab.label,
          lean: CopySanitizer.sanitizeMainCopy(spreadLean),
          confidenceLevel: RiskClassifier.confidenceLevelFromPercent(Number(params.spreadPick?.confidence ?? params.aiConfidencePercent)),
          riskLevel: params.riskLevel,
          explanation: CopySanitizer.toSingleSentence(CopySanitizer.sanitizeMainCopy(String(params.spreadPick?.rationale || "")), 140) || "The spread side that best matches the matchup edge.",
          prefill: {
            sport: params.adaptationSport,
            gameId: params.gameId,
            marketType: "spreads",
            pick: pickValue,
            point: spreadPoint,
          },
        })
      } else if (tab.marketType === "totals") {
        if (!totalLean) continue
        const totalPoint = parseFirstNumber(totalLean)
        const lower = normalize(totalLean)
        const pickValue = lower.includes("under") ? "under" : "over"
        out.push({
          id: "total",
          label: tab.label,
          lean: CopySanitizer.sanitizeMainCopy(totalLean),
          confidenceLevel: RiskClassifier.confidenceLevelFromPercent(Number(params.totalPick?.confidence ?? params.aiConfidencePercent)),
          riskLevel: params.riskLevel,
          explanation: CopySanitizer.toSingleSentence(CopySanitizer.sanitizeMainCopy(String(params.totalPick?.rationale || "")), 140) || "The total side that best matches the expected game script.",
          prefill: {
            sport: params.adaptationSport,
            gameId: params.gameId,
            marketType: "totals",
            pick: pickValue,
            point: totalPoint,
          },
        })
      }
    }

    return out
  }

  private _buildMatchupCards(params: {
    awayTeam: string
    homeTeam: string
    units: { offense: string; defense: string }
    offensiveEdges: any
    defensiveEdges: any
  }): AnalysisDetailViewModel["matchupCards"] {
    const awayTeam = String(params.awayTeam || "").trim()
    const homeTeam = String(params.homeTeam || "").trim()

    const off = params.offensiveEdges || {}
    const def = params.defensiveEdges || {}

    const card1 = {
      title: awayTeam && homeTeam ? `${awayTeam} ${params.units.offense} vs ${homeTeam} ${params.units.defense}` : "Matchup Breakdown",
      summary: CopySanitizer.sanitizeMainCopy(String(off.away_advantage || "")) || CopySanitizer.sanitizeMainCopy(String(off.key_matchup || "")),
      bulletInsights: [
        CopySanitizer.sanitizeMainCopy(String(off.key_matchup || "")),
        CopySanitizer.sanitizeMainCopy(String(def.away_advantage || "")),
      ].filter(Boolean),
    }

    const card2 = {
      title: awayTeam && homeTeam ? `${homeTeam} ${params.units.offense} vs ${awayTeam} ${params.units.defense}` : "Matchup Breakdown",
      summary: CopySanitizer.sanitizeMainCopy(String(off.home_advantage || "")) || CopySanitizer.sanitizeMainCopy(String(def.key_matchup || "")),
      bulletInsights: [
        CopySanitizer.sanitizeMainCopy(String(def.key_matchup || "")),
        CopySanitizer.sanitizeMainCopy(String(def.home_advantage || "")),
      ].filter(Boolean),
    }

    return [card1, card2].filter((c) => c.summary || c.bulletInsights.length > 0)
  }

  private _buildTrends(params: { ats: any; totals: any; weather: any }): string[] {
    const out: string[] = []

    const ats = CopySanitizer.sanitizeMainCopy(String(params.ats?.analysis || ""))
    const totals = CopySanitizer.sanitizeMainCopy(String(params.totals?.analysis || ""))
    const weather = CopySanitizer.sanitizeMainCopy(String(params.weather || ""))

    if (ats) out.push(CopySanitizer.toSingleSentence(ats, 140))
    if (totals) out.push(CopySanitizer.toSingleSentence(totals, 140))
    if (weather) out.push(CopySanitizer.toSingleSentence(weather, 140))

    return out.slice(0, 4)
  }
}


