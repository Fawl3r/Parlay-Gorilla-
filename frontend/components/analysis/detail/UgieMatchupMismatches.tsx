"use client"

import { cn } from "@/lib/utils"

export type UgieMatchupMismatchesProps = {
  matchupMismatches: { whySummary: string; topEdges: string[] } | null
  className?: string
}

export function UgieMatchupMismatches({ matchupMismatches, className }: UgieMatchupMismatchesProps) {
  if (!matchupMismatches) return null
  const why = String(matchupMismatches.whySummary ?? "").trim()
  const edges = (matchupMismatches.topEdges ?? []).filter((e) => String(e).trim()).slice(0, 10)
  if (!why && edges.length === 0) return null

  return (
    <section className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm p-5", className)}>
      <div className="text-sm font-extrabold text-white">Matchup Mismatches</div>
      {why ? (
        <div className="mt-3 rounded-xl border border-white/10 bg-black/25 p-3">
          <div className="text-[11px] uppercase tracking-wide text-white/50">Summary</div>
          <div className="mt-1 text-sm leading-6 text-white/85 whitespace-pre-wrap">{why}</div>
        </div>
      ) : null}
      {edges.length > 0 ? (
        <div className="mt-3">
          <div className="text-[11px] uppercase tracking-wide text-white/50">Key Edges</div>
          <div className="mt-2 space-y-2">
            {edges.map((e, idx) => (
              <div key={idx} className="flex items-start gap-2 text-sm text-white/85">
                <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-cyan-400 shrink-0" aria-hidden="true" />
                <div className="leading-6">{e}</div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  )
}
