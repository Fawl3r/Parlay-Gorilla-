export type UsageCoachInputs = {
  ai: {
    used: number
    limit: number
    remaining: number
    periodStartIso?: string | null
    periodEndIso?: string | null
  }
  custom: {
    used: number
    limit: number
    remaining: number
  }
  credits: {
    balance: number
    costPerAiParlay: number
  }
}

export class UsageCoachInsightManager {
  public getSingleInsight(inputs: UsageCoachInputs): string {
    const ai = this._normalizeLimit(inputs.ai)
    const custom = this._normalizeLimit(inputs.custom)

    const aiPct = this._percentUsed(ai.used, ai.limit)
    const customPct = this._percentUsed(custom.used, custom.limit)

    // 1) High-signal: approaching a limit.
    if (aiPct >= 86 || customPct >= 86) {
      return this._approachingLimitInsight({ ai, custom })
    }

    // 2) Predictive pacing (only when we can compute a reasonable projection).
    const projection = this._projectAiRemaining({
      used: ai.used,
      limit: ai.limit,
      periodStartIso: inputs.ai.periodStartIso,
      periodEndIso: inputs.ai.periodEndIso,
    })
    if (projection !== null) {
      return `At your current pace, you’ll have ~${projection} AI parlays left this cycle.`
    }

    // 3) Behavioral: selective Custom AI usage (only if user has meaningful activity).
    const totalActions = Math.max(0, ai.used) + Math.max(0, custom.used)
    const customShare = totalActions > 0 ? Math.round((Math.max(0, custom.used) / totalActions) * 100) : 0
    if (totalActions >= 10 && custom.used > 0 && customShare <= 25) {
      return "You’ve been using Custom AI selectively — that’s typically the most effective approach."
    }

    // 4) Default: reassuring, no-pressure.
    return "You’re pacing well — no risk of hitting limits this cycle."
  }

  public estimateAiRunsFromCredits(creditsBalance: number, costPerAiParlay: number): number {
    const cost = Math.max(1, Math.floor(costPerAiParlay || 1))
    return Math.max(0, Math.floor((creditsBalance || 0) / cost))
  }

  private _approachingLimitInsight({
    ai,
    custom,
  }: {
    ai: { used: number; limit: number; remaining: number }
    custom: { used: number; limit: number; remaining: number }
  }): string {
    const aiLine =
      ai.limit > 0 ? `${Math.max(0, ai.remaining)} AI parlays left` : "AI parlay usage is unlimited on your plan"
    const customLine =
      custom.limit > 0 ? `${Math.max(0, custom.remaining)} Custom AI left` : "Custom AI is not included on your plan"
    return `Heads up: you’re getting close — ${aiLine}, ${customLine}.`
  }

  private _projectAiRemaining({
    used,
    limit,
    periodStartIso,
    periodEndIso,
  }: {
    used: number
    limit: number
    periodStartIso?: string | null
    periodEndIso?: string | null
  }): number | null {
    if (!(limit > 0) || !(used > 0)) return null
    if (!periodStartIso || !periodEndIso) return null

    const start = this._safeDate(periodStartIso)
    const end = this._safeDate(periodEndIso)
    if (!start || !end) return null
    if (end.getTime() <= start.getTime()) return null

    const now = Date.now()
    const elapsedMs = Math.max(0, Math.min(now - start.getTime(), end.getTime() - start.getTime()))
    const totalMs = end.getTime() - start.getTime()

    // Avoid noisy projections early in a cycle.
    const elapsedDays = elapsedMs / (1000 * 60 * 60 * 24)
    const totalDays = totalMs / (1000 * 60 * 60 * 24)
    if (elapsedDays < 2 || totalDays < 7) return null

    const perDay = used / elapsedDays
    const projectedTotal = perDay * totalDays
    const projectedRemaining = Math.max(0, Math.round(limit - projectedTotal))
    return projectedRemaining
  }

  private _normalizeLimit<T extends { used: number; limit: number; remaining: number }>(x: T): T {
    const limit = Number.isFinite(x.limit) ? x.limit : 0
    const used = Number.isFinite(x.used) ? x.used : 0
    const remaining = Number.isFinite(x.remaining) ? x.remaining : Math.max(0, limit - used)
    return { ...x, limit, used, remaining }
  }

  private _percentUsed(used: number, limit: number): number {
    if (!(limit > 0)) return 0
    return Math.max(0, Math.min(100, (Math.max(0, used) / limit) * 100))
  }

  private _safeDate(iso: string): Date | null {
    const d = new Date(iso)
    return Number.isFinite(d.getTime()) ? d : null
  }
}


