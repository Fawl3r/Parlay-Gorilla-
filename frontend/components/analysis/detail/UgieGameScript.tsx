"use client"

import { cn } from "@/lib/utils"

export type UgieGameScriptProps = {
  gameScript: {
    whySummary: string
    stabilityScore: number
    stabilityConfidence: number
  } | null
  className?: string
}

function toPct(value: number): number {
  if (!Number.isFinite(value)) return 0
  return Math.max(0, Math.min(100, Math.round(value * 100)))
}

export function UgieGameScript({ gameScript, className }: UgieGameScriptProps) {
  if (!gameScript) return null

  const why = String(gameScript.whySummary ?? "").trim()
  const stabilityPct = toPct(gameScript.stabilityScore)
  const confidencePct = toPct(gameScript.stabilityConfidence)

  return (
    <section className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm p-5", className)}>
      <div className="text-sm font-extrabold text-white">Game Script</div>
      {why ? (
        <div className="mt-3 rounded-xl border border-white/10 bg-black/25 p-3">
          <div className="text-[11px] uppercase tracking-wide text-white/50">Summary</div>
          <div className="mt-1 text-sm leading-6 text-white/85 whitespace-pre-wrap">{why}</div>
        </div>
      ) : null}
      <div className="mt-4 space-y-3">
        <div>
          <div className="flex items-center justify-between text-xs text-white/60">
            <span>Script stability</span>
            <span>{stabilityPct}%</span>
          </div>
          <div className="mt-2 h-3 rounded-full bg-white/10 overflow-hidden">
            <div
              className="h-full bg-emerald-500 transition-all duration-500"
              style={{ width: `${stabilityPct}%` }}
            />
          </div>
        </div>
        <div>
          <div className="flex items-center justify-between text-xs text-white/60">
            <span>Stability confidence</span>
            <span>{confidencePct}%</span>
          </div>
          <div className="mt-2 h-3 rounded-full bg-white/10 overflow-hidden">
            <div
              className="h-full bg-cyan-500 transition-all duration-500"
              style={{ width: `${confidencePct}%` }}
            />
          </div>
        </div>
      </div>
    </section>
  )
}
