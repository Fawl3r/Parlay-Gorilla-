export type UsageGaugeStatus = "good" | "warning" | "critical" | "neutral"

export type UsageGaugeColors = {
  ring: string
  glow: string
  badge: string
}

export class UsageGaugeStatusManager {
  public getPercentUsed(used: number, limit: number | null | undefined): number | null {
    if (limit === null || limit === undefined) return null
    if (!(limit > 0)) return null
    const safeUsed = Number.isFinite(used) ? Math.max(0, used) : 0
    const pct = (safeUsed / limit) * 100
    return Math.max(0, Math.min(100, pct))
  }

  public getStatus(percentUsed: number | null): UsageGaugeStatus {
    if (percentUsed === null) return "neutral"
    if (percentUsed <= 60) return "good"
    if (percentUsed <= 85) return "warning"
    return "critical"
  }

  public getColors(status: UsageGaugeStatus): UsageGaugeColors {
    switch (status) {
      case "good":
        return { ring: "stroke-emerald-400", glow: "text-emerald-300", badge: "text-emerald-300" }
      case "warning":
        return { ring: "stroke-amber-300", glow: "text-amber-200", badge: "text-amber-200" }
      case "critical":
        return { ring: "stroke-rose-400", glow: "text-rose-300", badge: "text-rose-300" }
      default:
        return { ring: "stroke-white/20", glow: "text-white/70", badge: "text-white/70" }
    }
  }
}




