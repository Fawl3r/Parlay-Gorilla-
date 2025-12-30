export type ConfidenceLevel = "Low" | "Medium" | "High"
export type RiskLevel = "Low" | "Medium" | "High"

export class RiskClassifier {
  static confidenceLevelFromPercent(percent: number): ConfidenceLevel {
    const pct = this._clampPct(percent)
    if (pct >= 70) return "High"
    if (pct >= 50) return "Medium"
    return "Low"
  }

  static riskLevelFromSignals(params: {
    aiConfidencePercent: number
    homeWinProb: number
    awayWinProb: number
    limitedData: boolean
  }): RiskLevel {
    const ai = this._clampPct(params.aiConfidencePercent)
    const gap = this._clampPct(Math.abs((params.homeWinProb - params.awayWinProb) * 100))
    const closeness = 100 - gap // close games tend to be higher risk

    // Weighted: AI confidence matters most, closeness adds additional risk.
    let score = (100 - ai) * 0.7 + closeness * 0.3

    if (params.limitedData) score = Math.max(score, 55) // never “Low” when data is limited

    if (score >= 70) return "High"
    if (score >= 45) return "Medium"
    return "Low"
  }

  private static _clampPct(value: number): number {
    if (!Number.isFinite(value)) return 0
    return Math.max(0, Math.min(100, value))
  }
}


