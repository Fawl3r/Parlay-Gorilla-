"use client"

import { cn } from "@/lib/utils"
import { TeamBadge } from "@/components/TeamBadge"

export type TeamMatchupVisualProps = {
  awayTeam: string
  homeTeam: string
  separator?: "@" | "vs"
  sport?: string
  className?: string
}

function resolveSeparatorLabel(raw?: string): "@" | "vs" {
  return raw === "@" ? "@" : "vs"
}

function TeamWithBadge({
  teamName,
  sport,
}: {
  teamName: string
  sport?: string
}) {
  return (
    <div className="flex items-center gap-2 min-w-0">
      {/* Force dark text colors inside TeamBadge (it uses dark:* variants for the name). */}
      <div className="dark shrink-0">
        <TeamBadge teamName={teamName} sport={sport} size="sm" />
      </div>
      <div className="text-sm font-extrabold text-white truncate">{teamName}</div>
    </div>
  )
}

export function TeamMatchupVisual({ awayTeam, homeTeam, separator, sport, className }: TeamMatchupVisualProps) {
  const sep = resolveSeparatorLabel(separator)

  if (!awayTeam || !homeTeam) return null

  return (
    <div
      className={cn("flex items-center gap-2 flex-wrap", className)}
      data-testid="matchup-teams"
      aria-label="Teams"
    >
      <TeamWithBadge teamName={awayTeam} sport={sport} />
      <span className="text-[11px] font-black uppercase tracking-widest text-white/50 px-1">{sep}</span>
      <TeamWithBadge teamName={homeTeam} sport={sport} />
    </div>
  )
}


