import type { ConfidenceLevel, RiskLevel } from "./RiskClassifier"
import type { MarketType } from "./SportAdaptationRegistry"
import type { UgieModulesViewModel } from "./ugie/UgieV2ModulesBuilder"

export type BetOptionKey = "moneyline" | "spread" | "total"

export type AnalysisDetailPrefill = {
  sport: string
  gameId: string
  marketType: MarketType
  pick: string
  point?: number
}

export type AnalysisDetailViewModel = {
  header: {
    title: string
    subtitle?: string
    lastUpdatedLabel?: string
    awayTeam?: string
    homeTeam?: string
    separator?: "@" | "vs"
    sport?: string
  }
  quickTake: {
    sportIcon: string
    favoredTeam: string
    confidencePercent: number
    confidenceLevel: ConfidenceLevel
    riskLevel: RiskLevel
    recommendation: string
    whyText: string
  }
  keyDrivers: {
    positives: string[]
    risks: string[]
  }
  probability: {
    teamA: string
    teamB: string
    probabilityA: number
    probabilityB: number
  }
  betOptions: Array<{
    id: BetOptionKey
    label: string
    lean: string
    confidenceLevel: ConfidenceLevel
    riskLevel: RiskLevel
    explanation: string
    prefill?: AnalysisDetailPrefill
  }>
  matchupCards: Array<{
    title: string
    summary: string
    bulletInsights: string[]
  }>
  trends: string[]
  limitedDataNote?: string
  ugieModules?: UgieModulesViewModel
}
