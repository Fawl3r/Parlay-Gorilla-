"use client"

import { cn } from "@/lib/utils"

export type ProbabilityMeterProps = {
  teamA: string
  teamB: string
  probabilityA: number
  probabilityB: number
  className?: string
}

function toPct(value: number): number {
  if (!Number.isFinite(value)) return 0
  return Math.max(0, Math.min(100, Math.round(value)))
}

export function ProbabilityMeter({ teamA, teamB, probabilityA, probabilityB, className }: ProbabilityMeterProps) {
  const a = toPct(probabilityA)
  const b = toPct(probabilityB)

  return (
    <section className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm p-5", className)}>
      <div className="text-sm font-extrabold text-white">Win Probability</div>
      <div className="mt-4 space-y-3">
        <div>
          <div className="flex items-center justify-between text-xs text-white/60">
            <div className="font-semibold text-white/80 truncate">{teamA}</div>
            <div className="shrink-0">{a}%</div>
          </div>
          <div className="mt-2 h-3 rounded-full bg-white/10 overflow-hidden">
            <div className="h-full bg-emerald-500 transition-all duration-500" style={{ width: `${a}%` }} />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between text-xs text-white/60">
            <div className="font-semibold text-white/80 truncate">{teamB}</div>
            <div className="shrink-0">{b}%</div>
          </div>
          <div className="mt-2 h-3 rounded-full bg-white/10 overflow-hidden">
            <div className="h-full bg-cyan-500 transition-all duration-500" style={{ width: `${b}%` }} />
          </div>
        </div>
      </div>

      <div className="mt-4 text-xs text-white/60">
        <span className="font-semibold text-white/75">How sure the AI is:</span>{" "}
        <span title="How sure the AI is about the outcome. Higher means fewer surprises are expected.">
          based on confidence and matchup stability.
        </span>
      </div>
    </section>
  )
}


