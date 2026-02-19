"use client"

import { cn } from "@/lib/utils"
import type { AnalysisEnrichment } from "@/lib/api/types/analysis"
import { BarChart3, ChevronDown, AlertCircle, Info } from "lucide-react"

export type MatchupIntelligencePanelProps = {
  /** Enrichment payload from API; null = unavailable */
  enrichment: AnalysisEnrichment | null | undefined
  /** Optional reason when enrichment is missing (e.g. "Missing league ID" / "Rate limit") */
  unavailableReason?: string
  className?: string
}

const STAT_LABELS: Record<string, string> = {
  points_for: "PF",
  points_against: "PA",
  wins: "W",
  losses: "L",
  fg_pct: "FG%",
  three_pct: "3P%",
  ft_pct: "FT%",
  rebounds: "REB",
  assists: "AST",
  turnovers: "TO",
}

/** Prefer preformatted string from backend; otherwise format number consistently. */
function formatStatValue(val: number | string | null | undefined): string {
  if (val == null) return "—"
  if (typeof val === "number") {
    if (Number.isInteger(val)) return String(val)
    return val.toFixed(1)
  }
  return String(val) // preformatted from backend (e.g. "47.2%")
}

/** Relative time for "Last updated" (e.g. "2 hours ago"). */
function formatRelativeTime(isoString: string | null | undefined): string {
  if (!isoString) return ""
  try {
    const date = new Date(isoString)
    const now = new Date()
    const sec = Math.floor((now.getTime() - date.getTime()) / 1000)
    if (sec < 60) return "just now"
    if (sec < 3600) return `${Math.floor(sec / 60)} min ago`
    if (sec < 86400) return `${Math.floor(sec / 3600)} hours ago`
    if (sec < 604800) return `${Math.floor(sec / 86400)} days ago`
    return date.toLocaleDateString()
  } catch {
    return ""
  }
}

export function MatchupIntelligencePanel({
  enrichment,
  unavailableReason,
  className,
}: MatchupIntelligencePanelProps) {
  const hasData =
    enrichment?.home_team &&
    enrichment?.away_team &&
    (enrichment.data_quality?.has_standings ||
      enrichment.data_quality?.has_team_stats ||
      enrichment.data_quality?.has_form ||
      enrichment.data_quality?.has_injuries ||
      enrichment.home_team.record ||
      enrichment.away_team.record ||
      (enrichment.home_team.recent_form?.length ?? 0) > 0 ||
      (enrichment.away_team.recent_form?.length ?? 0) > 0)

  const content = !hasData ? (
    <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 p-4 text-sm text-white/70">
      <AlertCircle className="h-5 w-5 shrink-0 text-amber-500" />
      <div>
        <p className="font-medium text-white/90">Matchup data unavailable</p>
        <p className="mt-0.5 text-xs">
          {unavailableReason ||
            "League ID not configured or provider temporarily unavailable. Odds and analysis are still available."}
        </p>
      </div>
    </div>
  ) : (
    <div className="space-y-4">
      {/* TEAM PERFORMANCE */}
      <div>
        <p className="pg-label text-white/65 mb-2">Team Performance</p>
        <div className="grid grid-cols-2 gap-4 text-sm">
        <div className="glass-analytics rounded-xl p-4 pg-card-hover">
          <div className="font-semibold text-white/90 truncate" title={enrichment!.away_team.name}>
            {enrichment!.away_team.name}
          </div>
          {(enrichment!.away_team.record != null || enrichment!.away_team.standings_rank != null) && (
            <div className="mt-1 flex flex-wrap gap-x-3 text-white/70">
              {enrichment!.away_team.record != null && <span>Record: {enrichment!.away_team.record}</span>}
              {enrichment!.away_team.standings_rank != null && <span>Rank: #{enrichment!.away_team.standings_rank}</span>}
            </div>
          )}
          {enrichment!.away_team.recent_form?.length ? (
            <div className="mt-2 flex items-center gap-1.5">
              <span className="text-xs text-white/50">Form:</span>
              <div className="flex gap-0.5">
                {enrichment!.away_team.recent_form.slice(0, 5).map((r, i) => (
                  <span
                    key={i}
                    className={cn("text-xs font-medium", r === "W" ? "text-emerald-400" : "text-red-400")}
                  >
                    {r}
                  </span>
                ))}
              </div>
            </div>
          ) : null}
          {enrichment!.away_team.injuries_summary?.length ? (
            <div className="mt-2 flex flex-wrap gap-x-2 text-xs text-white/60">
              {enrichment!.away_team.injuries_summary.map((s, i) => (
                <span key={i}>
                  {s.status}: {s.count}
                </span>
              ))}
            </div>
          ) : null}
        </div>
        <div className="glass-analytics rounded-xl p-4 pg-card-hover">
          <div className="font-semibold text-white/90 truncate" title={enrichment!.home_team.name}>
            {enrichment!.home_team.name}
          </div>
          {(enrichment!.home_team.record != null || enrichment!.home_team.standings_rank != null) && (
            <div className="mt-1 flex flex-wrap gap-x-3 text-white/70">
              {enrichment!.home_team.record != null && <span>Record: {enrichment!.home_team.record}</span>}
              {enrichment!.home_team.standings_rank != null && <span>Rank: #{enrichment!.home_team.standings_rank}</span>}
            </div>
          )}
          {enrichment!.home_team.recent_form?.length ? (
            <div className="mt-2 flex items-center gap-1.5">
              <span className="text-xs text-white/50">Form:</span>
              <div className="flex gap-0.5">
                {enrichment!.home_team.recent_form.slice(0, 5).map((r, i) => (
                  <span
                    key={i}
                    className={cn("text-xs font-medium", r === "W" ? "text-emerald-400" : "text-red-400")}
                  >
                    {r}
                  </span>
                ))}
              </div>
            </div>
          ) : null}
          {enrichment!.home_team.injuries_summary?.length ? (
            <div className="mt-2 flex flex-wrap gap-x-2 text-xs text-white/60">
              {enrichment!.home_team.injuries_summary.map((s, i) => (
                <span key={i}>
                  {s.status}: {s.count}
                </span>
              ))}
            </div>
          ) : null}
        </div>
        </div>
      </div>

      {/* RECENT FORM TREND — shown inline in team cards above; section label if we have form */}
      {((enrichment!.home_team.recent_form?.length ?? 0) > 0 || (enrichment!.away_team.recent_form?.length ?? 0) > 0) && (
        <div>
          <p className="pg-label text-white/65 mb-1">Recent Form Trend</p>
          <p className="text-xs text-white/50">Last 5 results (W/L) per team above.</p>
        </div>
      )}

      {/* KEY STAT EDGES */}
      {(() => {
        const keyStatsRows =
          enrichment!.key_team_stats?.filter(
            (row) => row.home_value != null || row.away_value != null
          ) ?? []
        const hasDerivedStats =
          (enrichment!.home_team.team_stats && Object.keys(enrichment!.home_team.team_stats).length > 0) ||
          (enrichment!.away_team.team_stats && Object.keys(enrichment!.away_team.team_stats).length > 0)
        const showStatsTable = keyStatsRows.length > 0 || hasDerivedStats

        /** Parse numeric value for comparison (higher is better for most stats; lower for e.g. TO, PA). */
        const toNum = (v: number | string | null | undefined): number | null => {
          if (v == null) return null
          if (typeof v === "number" && !Number.isNaN(v)) return v
          const s = String(v).replace(/%/g, "")
          const n = parseFloat(s)
          return Number.isNaN(n) ? null : n
        }
        /** Stats where lower value is better (advantage = negative delta). */
        const lowerIsBetter = new Set(["points_against", "turnovers", "to", "pa", "era", "ra", "goals_against", "ga"])
        const isLowerBetter = (key: string) => lowerIsBetter.has(key.toLowerCase())

        return showStatsTable ? (
          <div>
            <p className="pg-label text-white/65 mb-2">Key Stat Edges</p>
            <div className="overflow-x-auto rounded-xl glass-analytics">
            <table className="w-full min-w-[200px] text-sm">
              <thead>
                <tr className="border-b border-white/10 text-left text-white/70">
                  <th className="p-2 font-medium">Stat</th>
                  <th className="p-2 font-medium text-right">{enrichment!.away_team.name.slice(0, 12)}</th>
                  <th className="p-2 font-medium text-right">{enrichment!.home_team.name.slice(0, 12)}</th>
                </tr>
              </thead>
              <tbody>
                {keyStatsRows.length > 0
                  ? keyStatsRows.map((row) => {
                      const aNum = toNum(row.away_value)
                      const hNum = toNum(row.home_value)
                      const threshold = 0.1
                      let awayStronger = false
                      let homeStronger = false
                      if (aNum != null && hNum != null) {
                        const diff = aNum - hNum
                        const lowerBetter = isLowerBetter(row.key)
                        if (lowerBetter) {
                          awayStronger = diff < -threshold
                          homeStronger = diff > threshold
                        } else {
                          awayStronger = diff > threshold
                          homeStronger = diff < -threshold
                        }
                      }
                      return (
                      <tr key={row.key} className="border-b border-white/5">
                        <td className="p-2 text-white/70">{row.label}</td>
                        <td className={cn("p-2 text-right", awayStronger && "text-emerald-400 font-semibold")}>
                          {row.away_value != null ? formatStatValue(row.away_value) : "—"}
                        </td>
                        <td className={cn("p-2 text-right", homeStronger && "text-emerald-400 font-semibold")}>
                          {row.home_value != null ? formatStatValue(row.home_value) : "—"}
                        </td>
                      </tr>
                    )})
                  : Array.from(
                    new Set([
                      ...Object.keys(enrichment!.away_team.team_stats || {}),
                      ...Object.keys(enrichment!.home_team.team_stats || {}),
                    ])
                  ).map((key) => (
                    <tr key={key} className="border-b border-white/5">
                      <td className="p-2 text-white/70">{STAT_LABELS[key] || key}</td>
                      <td className="p-2 text-right text-white/90">
                        {enrichment!.away_team.team_stats?.[key] != null
                          ? formatStatValue(enrichment!.away_team.team_stats[key])
                          : "—"}
                      </td>
                      <td className="p-2 text-right text-white/90">
                        {enrichment!.home_team.team_stats?.[key] != null
                          ? formatStatValue(enrichment!.home_team.team_stats[key])
                          : "—"}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
            </div>
            {/* Micro insight: largest stat edge (client-side, no AI call) */}
            {keyStatsRows.length > 0 && (() => {
              type Edge = { team: string; stat: string; delta: number; label: string }
              let best: Edge | null = null
              for (const row of keyStatsRows) {
                const aNum = toNum(row.away_value)
                const hNum = toNum(row.home_value)
                if (aNum == null || hNum == null) continue
                const lowerBetter = isLowerBetter(row.key)
                const diff = aNum - hNum
                const advantage = lowerBetter ? -diff : diff
                const absAdv = Math.abs(advantage)
                if (absAdv >= (best ? Math.abs(best.delta) : 0)) {
                  const team = advantage > 0 ? enrichment!.away_team.name : enrichment!.home_team.name
                  best = { team, stat: row.label, delta: advantage, label: row.label }
                }
              }
              if (!best || Math.abs(best.delta) < 0.5) return null
              const plusX = typeof best.delta === "number" && best.delta % 1 !== 0
                ? best.delta.toFixed(1) : Math.round(best.delta)
              return (
                <p className="mt-3 text-xs text-white/70 border-l-2 border-emerald-500/50 pl-3">
                  <span className="pg-label text-white/55">AI Insight:</span>{" "}
                  {best.team} holds a +{plusX} advantage in {best.stat}.
                </p>
              )
            })()}
          </div>
        ) : enrichment!.data_quality?.has_team_stats === false ? (
          <p className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-white/60">
            Team stats unavailable for this matchup.
          </p>
        ) : null
      })()}

      {/* INJURY IMPACT */}
      {((enrichment!.home_team.injuries_summary?.length ?? 0) > 0 || (enrichment!.away_team.injuries_summary?.length ?? 0) > 0) && (
        <div>
          <p className="pg-label text-white/65 mb-1">Injury Impact</p>
          <p className="text-xs text-white/50">Counts by status in team cards above.</p>
        </div>
      )}

      {/* Last updated + optional per-source timestamps */}
      {(enrichment!.as_of || (enrichment!.data_quality?.source_timestamps && Object.keys(enrichment!.data_quality.source_timestamps).length > 0)) && (
        <div className="text-xs text-white/50 space-y-0.5">
          {enrichment!.as_of && (
            <p>Last updated {formatRelativeTime(enrichment!.as_of)}</p>
          )}
          {enrichment!.data_quality?.source_timestamps && Object.keys(enrichment!.data_quality.source_timestamps).length > 0 && (
            <div className="flex flex-wrap gap-x-3 gap-y-0.5">
              {Object.entries(enrichment!.data_quality.source_timestamps).map(([source, ts]) =>
                ts ? (
                  <span key={source}>{source}: {formatRelativeTime(ts)}</span>
                ) : null
              )}
            </div>
          )}
        </div>
      )}

      {/* Limited data badge: when notes present or any has_* is false */}
      {(() => {
        const dq = enrichment!.data_quality
        const hasNotes = (dq?.notes?.length ?? 0) > 0
        const anyMissing = dq && (
          dq.has_standings === false ||
          dq.has_team_stats === false ||
          dq.has_form === false ||
          dq.has_injuries === false
        )
        const showBadge = hasNotes || anyMissing
        const tooltipLines = [...(dq?.notes ?? [])]
        if (anyMissing) {
          const missing: string[] = []
          if (dq.has_standings === false) missing.push("Standings")
          if (dq.has_team_stats === false) missing.push("Team stats")
          if (dq.has_form === false) missing.push("Form")
          if (dq.has_injuries === false) missing.push("Injuries")
          if (missing.length) tooltipLines.unshift(`Missing: ${missing.join(", ")}`)
        }
        if (!showBadge) return null
        return (
          <div className="flex items-center gap-2">
            <span
              className="inline-flex items-center gap-1 rounded-md bg-white/10 px-2 py-0.5 text-xs text-white/70"
              title={tooltipLines.join("\n")}
            >
              <Info className="h-3.5 w-3.5 shrink-0" />
              Limited data
            </span>
          </div>
        )
      })()}
    </div>
  )

  return (
    <section className={cn("rounded-2xl glass-analytics overflow-hidden pg-card-hover", className)}>
      <details className="group" open={undefined}>
        <summary className="flex cursor-pointer list-none items-center gap-2 p-4 text-sm font-semibold text-white/90 hover:bg-white/5 md:py-3">
          <BarChart3 className="h-5 w-5 shrink-0 text-white/70" />
          <span>Matchup intelligence</span>
          {hasData && enrichment?.league && (
            <span className="ml-auto text-xs text-white/50">
              {enrichment.league} · {enrichment.season}
            </span>
          )}
          <ChevronDown className="h-4 w-4 shrink-0 text-white/50 transition group-open:rotate-180" />
        </summary>
        <div className="border-t border-white/10 px-4 pb-4 pt-2">{content}</div>
      </details>
    </section>
  )
}
