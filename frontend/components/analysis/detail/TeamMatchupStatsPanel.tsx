"use client"

import { cn } from "@/lib/utils"
import type { AnalysisEnrichment } from "@/lib/api/types/analysis"
import { BarChart3, ChevronDown } from "lucide-react"

export type TeamMatchupStatsPanelProps = {
  enrichment: AnalysisEnrichment | null | undefined
  className?: string
}

export function TeamMatchupStatsPanel({ enrichment, className }: TeamMatchupStatsPanelProps) {
  if (!enrichment?.home_team || !enrichment?.away_team) return null
  const hasStandings = enrichment.data_quality?.has_standings
  const home = enrichment.home_team
  const away = enrichment.away_team
  const hasData = hasStandings || home.record || away.record || home.standings_rank != null || away.standings_rank != null
  if (!hasData) return null

  const content = (
    <div className="grid grid-cols-2 gap-4 text-sm">
      <div className="rounded-xl border border-white/10 bg-white/5 p-4">
        <div className="font-semibold text-white/90 truncate" title={away.name}>{away.name}</div>
        {away.record != null && <div className="text-white/70 mt-1">Record: {away.record}</div>}
        {away.standings_rank != null && <div className="text-white/70">Rank: #{away.standings_rank}</div>}
        {away.recent_form?.length ? (
          <div className="mt-2 flex gap-0.5">
            {away.recent_form.slice(0, 5).map((r, i) => (
              <span key={i} className={cn("text-xs font-medium", r === "W" ? "text-emerald-400" : "text-red-400")}>{r}</span>
            ))}
          </div>
        ) : null}
      </div>
      <div className="rounded-xl border border-white/10 bg-white/5 p-4">
        <div className="font-semibold text-white/90 truncate" title={home.name}>{home.name}</div>
        {home.record != null && <div className="text-white/70 mt-1">Record: {home.record}</div>}
        {home.standings_rank != null && <div className="text-white/70">Rank: #{home.standings_rank}</div>}
        {home.recent_form?.length ? (
          <div className="mt-2 flex gap-0.5">
            {home.recent_form.slice(0, 5).map((r, i) => (
              <span key={i} className={cn("text-xs font-medium", r === "W" ? "text-emerald-400" : "text-red-400")}>{r}</span>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  )

  return (
    <section className={cn("rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm overflow-hidden", className)}>
      <details className="group" open={undefined}>
        <summary className="flex cursor-pointer list-none items-center gap-2 p-4 text-sm font-semibold text-white/90 hover:bg-white/5 md:py-3">
          <BarChart3 className="h-5 w-5 text-white/70" />
          <span>Team matchup stats</span>
          <span className="ml-auto text-xs text-white/50">{enrichment.league} · {enrichment.season}</span>
          <ChevronDown className="h-4 w-4 text-white/50 transition group-open:rotate-180" />
        </summary>
        <div className="border-t border-white/10 px-4 pb-4 pt-2">
          {content}
          {enrichment.data_quality?.notes?.length ? (
            <p className="mt-3 text-xs text-white/50">Limited stats available. {enrichment.data_quality.notes.join(" ")}</p>
          ) : null}
        </div>
      </details>
    </section>
  )
}
