"use client"

import { cn } from "@/lib/utils"

import { TeamMatchupVisual } from "./TeamMatchupVisual"

function stripTrailingContext(team: string): string {
  const raw = String(team || "").trim()
  if (!raw) return ""
  // Best-effort: remove common suffixes like " - Week 1" / "(Preview)" / " • NFL".
  return raw
    .split(" • ")[0]
    .split(" - ")[0]
    .split("|")[0]
    .split("(")[0]
    .trim()
}

function tryParseTeamsFromTitle(title: string): { awayTeam: string; homeTeam: string; separator: "@" | "vs" } | null {
  const raw = String(title || "").trim()
  if (!raw) return null

  const atIdx = raw.indexOf("@")
  if (atIdx > 0) {
    const away = stripTrailingContext(raw.slice(0, atIdx))
    const home = stripTrailingContext(raw.slice(atIdx + 1))
    if (away && home) return { awayTeam: away, homeTeam: home, separator: "@" }
  }

  const vsMatch = raw.match(/(.+?)\s+vs\.?\s+(.+)/i)
  if (vsMatch) {
    const away = stripTrailingContext(vsMatch[1])
    const home = stripTrailingContext(vsMatch[2])
    if (away && home) return { awayTeam: away, homeTeam: home, separator: "vs" }
  }

  return null
}

export type HeaderGameMatchupProps = {
  title: string
  subtitle?: string
  lastUpdatedLabel?: string
  awayTeam?: string
  homeTeam?: string
  separator?: "@" | "vs"
  sport?: string
  className?: string
}

export function HeaderGameMatchup({
  title,
  subtitle,
  lastUpdatedLabel,
  awayTeam,
  homeTeam,
  separator,
  sport,
  className,
}: HeaderGameMatchupProps) {
  const fallback = (!awayTeam || !homeTeam) ? tryParseTeamsFromTitle(title) : null
  const effectiveAway = awayTeam || fallback?.awayTeam
  const effectiveHome = homeTeam || fallback?.homeTeam
  const effectiveSeparator = separator || fallback?.separator

  return (
    <div
      className={cn(
        "rounded-2xl border border-white/10 bg-black/40 backdrop-blur-sm",
        "px-4 py-3",
        className
      )}
      aria-label="Matchup header"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          {effectiveAway && effectiveHome ? (
            <TeamMatchupVisual awayTeam={effectiveAway} homeTeam={effectiveHome} separator={effectiveSeparator} sport={sport} />
          ) : (
            <div className="text-base font-extrabold text-white truncate">{title}</div>
          )}
          {subtitle ? <div className="text-xs text-white/60 truncate">{subtitle}</div> : null}
        </div>
        {lastUpdatedLabel ? (
          <div className="shrink-0 text-[11px] text-white/50 text-right leading-snug">{lastUpdatedLabel}</div>
        ) : null}
      </div>
    </div>
  )
}


