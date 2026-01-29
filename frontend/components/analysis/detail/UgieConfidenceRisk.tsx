"use client"

import { cn } from "@/lib/utils"

export type UgieConfidenceRiskProps = {
  confidenceRisk: {
    confidencePercent: number
    riskLevel: string
    dataQualityStatus: string
    disclaimer?: string
  }
  className?: string
}

const RISK_COLORS: Record<string, string> = {
  low: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  medium: "bg-amber-500/20 text-amber-300 border-amber-500/30",
  high: "bg-red-500/20 text-red-300 border-red-500/30",
}

function riskBadgeClass(level: string): string {
  const key = String(level ?? "medium").toLowerCase()
  return RISK_COLORS[key] ?? RISK_COLORS.medium
}

function qualityBadgeClass(status: string): string {
  const s = String(status ?? "").toLowerCase()
  if (s === "good") return "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
  if (s === "partial") return "bg-amber-500/20 text-amber-300 border-amber-500/30"
  return "bg-red-500/20 text-red-300 border-red-500/30"
}

export function UgieConfidenceRisk({ confidenceRisk, className }: UgieConfidenceRiskProps) {
  const { confidencePercent, riskLevel, dataQualityStatus, disclaimer } = confidenceRisk

  return (
    <section className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm p-5", className)}>
      <div className="text-sm font-extrabold text-white">Confidence & Risk</div>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="rounded-lg border border-white/15 bg-white/5 px-3 py-1.5 text-sm font-semibold text-white/90">
          {Math.round(confidencePercent)}% confidence
        </span>
        <span
          className={cn(
            "rounded-lg border px-3 py-1.5 text-xs font-medium capitalize",
            riskBadgeClass(riskLevel)
          )}
        >
          Risk: {riskLevel}
        </span>
        <span
          className={cn(
            "rounded-lg border px-3 py-1.5 text-xs font-medium capitalize",
            qualityBadgeClass(dataQualityStatus)
          )}
        >
          Data: {dataQualityStatus}
        </span>
      </div>
      {disclaimer ? (
        <p className="mt-3 text-xs text-white/60 italic">{disclaimer}</p>
      ) : null}
    </section>
  )
}
