"use client"

import { cn } from "@/lib/utils"

import { TeamMatchupVisual } from "./TeamMatchupVisual"

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
          {awayTeam && homeTeam ? (
            <TeamMatchupVisual awayTeam={awayTeam} homeTeam={homeTeam} separator={separator} sport={sport} />
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


