"use client"

import { ShieldAlert, Sparkles } from "lucide-react"

import { cn } from "@/lib/utils"
import { getEngineVersionString } from "@/lib/constants/appVersion"

export type ConfidenceLevel = "Low" | "Medium" | "High"
export type RiskLevel = "Low" | "Medium" | "High"

export type QuickTakeCardProps = {
  sportIcon?: string
  favoredTeam: string
  confidencePercent: number
  confidenceLevel: ConfidenceLevel
  riskLevel: RiskLevel
  recommendation: string
  whyText: string
  limitedDataNote?: string
  className?: string
}

function clampPct(value: number): number {
  if (!Number.isFinite(value)) return 0
  return Math.max(0, Math.min(100, Math.round(value)))
}

export function QuickTakeCard({
  sportIcon,
  favoredTeam,
  confidencePercent,
  confidenceLevel,
  riskLevel,
  recommendation,
  whyText,
  limitedDataNote,
  className,
}: QuickTakeCardProps) {
  const pct = clampPct(confidencePercent)
  const safeFavored = String(favoredTeam || "").trim() || "—"
  const safeRec = String(recommendation || "").trim() || "No clear recommendation yet."
  const safeWhy = String(whyText || "").trim()

  const limitedNote = String(limitedDataNote || "").trim()
  const limitedData = Boolean(limitedNote) || safeWhy.toLowerCase().includes("limited historical data")

  return (
    <section
      className={cn(
        "rounded-2xl border border-emerald-500/20",
        "bg-gradient-to-r from-emerald-500/10 to-cyan-500/10",
        "p-5",
        className
      )}
      aria-label="Quick take"
    >
      <div className="flex items-center gap-2 text-emerald-300 text-xs font-extrabold uppercase tracking-wide">
        <Sparkles className="h-4 w-4" />
        {sportIcon ? <span aria-hidden="true">{sportIcon}</span> : null}
        Quick Take
      </div>

      <div className="mt-4 space-y-3">
        <div className="text-sm text-white/80">
          <div className="font-semibold text-white">AI favors:</div>
          <div className="text-lg font-extrabold text-white">{safeFavored}</div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-xl border border-white/10 bg-black/25 p-3">
            <div className="text-[11px] uppercase tracking-wide text-white/50">How sure the AI is</div>
            <div className="mt-1 text-base font-extrabold text-white" title="How sure the AI is about this outcome.">
              {confidenceLevel} ({pct}%)
            </div>
          </div>
          <div className="rounded-xl border border-white/10 bg-black/25 p-3">
            <div className="text-[11px] uppercase tracking-wide text-white/50">Risk level</div>
            <div className="mt-1 text-base font-extrabold text-white">{riskLevel}</div>
          </div>
        </div>

        <div className="rounded-xl border border-white/10 bg-black/25 p-3">
          <div className="text-[11px] uppercase tracking-wide text-white/50">Recommended action</div>
          <div className="mt-1 text-sm font-semibold text-white">{safeRec}</div>
        </div>

        <div className="rounded-xl border border-white/10 bg-black/25 p-3">
          <div className="text-[11px] uppercase tracking-wide text-white/50">Why</div>
          {safeWhy ? (
            <div className="mt-1 text-sm leading-6 text-white/85 whitespace-pre-wrap">{safeWhy}</div>
          ) : (
            <div className="mt-1 text-sm leading-6 text-white/70">
              We don’t have enough data to explain the edge clearly yet.
            </div>
          )}

          {limitedData ? (
            <div className="mt-3 space-y-2">
              <div className="inline-flex items-center gap-2 text-xs text-amber-200/90">
                <ShieldAlert className="h-4 w-4" />
                {limitedNote || "This matchup has limited historical data. Confidence was adjusted accordingly."}
              </div>
              {limitedNote ? (
                <div className="text-xs text-white/50">
                  Analysis generated using {getEngineVersionString()} (deterministic core).
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    </section>
  )
}


