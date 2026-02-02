"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import type { KeyPlayer } from "@/lib/api"
import type { KeyPlayersViewModel } from "@/lib/analysis/detail/AnalysisDetailViewModel"

const DEFAULT_VISIBLE = 3
const MAX_VISIBLE = 5

const MONTH_UTC = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

/** Format ISO timestamp to "Jan 15, 2025 12:00 UTC" (stable for tests). */
function formatLastRefreshedUtc(iso: string): string | null {
  const d = new Date(iso)
  if (!Number.isFinite(d.getTime())) return null
  const mon = MONTH_UTC[d.getUTCMonth()]
  const day = d.getUTCDate()
  const year = d.getUTCFullYear()
  const h = String(d.getUTCHours()).padStart(2, "0")
  const m = String(d.getUTCMinutes()).padStart(2, "0")
  return `${mon} ${day}, ${year} ${h}:${m} UTC`
}

export type UgieKeyPlayersProps = {
  keyPlayers: KeyPlayersViewModel
  homeTeamName?: string
  awayTeamName?: string
  className?: string
}

function PlayerRow({ player }: { player: KeyPlayer }) {
  return (
    <div className="rounded-xl border border-white/10 bg-black/25 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-semibold text-white">{player.name}</span>
        <span className="rounded-full bg-white/15 px-2 py-0.5 text-xs text-white/90">
          {player.role}
        </span>
        <span
          className={cn(
            "rounded-full px-2 py-0.5 text-xs font-medium",
            player.impact === "High"
              ? "bg-amber-500/20 text-amber-300"
              : "bg-white/10 text-white/80"
          )}
        >
          {player.impact}
        </span>
      </div>
      {player.why ? (
        <p className="mt-2 text-sm leading-5 text-white/85">{player.why}</p>
      ) : null}
      {player.metrics && player.metrics.length > 0 ? (
        <div className="mt-2 flex flex-wrap gap-2">
          {player.metrics.map((m, i) => (
            <span
              key={i}
              className="rounded bg-white/10 px-2 py-0.5 text-xs text-white/80"
            >
              {m.label}: {m.value}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  )
}

function TeamCard({
  title,
  players,
  defaultVisible,
  maxVisible,
}: {
  title: string
  players: KeyPlayer[]
  defaultVisible: number
  maxVisible: number
}) {
  const [showMore, setShowMore] = useState(false)
  const visible = showMore ? maxVisible : defaultVisible
  const slice = players.slice(0, visible)
  const hasMore = players.length > visible

  if (players.length === 0) return null

  return (
    <div className="rounded-2xl border border-white/10 bg-black/25 p-4">
      <div className="text-sm font-extrabold text-white">{title}</div>
      <div className="mt-3 space-y-2">
        {slice.map((p, idx) => (
          <PlayerRow key={`${p.name}-${idx}`} player={p} />
        ))}
      </div>
      {hasMore && (
        <button
          type="button"
          onClick={() => setShowMore(true)}
          className="mt-3 text-sm font-medium text-white/70 hover:text-white"
        >
          Show more
        </button>
      )}
    </div>
  )
}

export function UgieKeyPlayers({
  keyPlayers,
  homeTeamName = "Home",
  awayTeamName = "Away",
  className,
}: UgieKeyPlayersProps) {
  const subtitle =
    keyPlayers.updatedAt
      ? "Verified current rosters • Updated for this matchup"
      : "Verified current rosters • Updated for this matchup"

  const verifiedTooltip = "Names are restricted to current rosters for this matchup."

  if (keyPlayers.status === "unavailable") {
    return (
      <section
        className={cn(
          "rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm p-5",
          className
        )}
      >
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-extrabold text-white">
            Key Players to Watch
          </span>
          <span
            className="rounded-full bg-white/10 px-2 py-0.5 text-xs font-medium text-white/80"
            title={verifiedTooltip}
          >
            Roster unavailable
          </span>
        </div>
        <p className="mt-3 text-sm text-white/70">
          Roster-verified key players are temporarily unavailable for this
          matchup.
        </p>
        <p className="mt-2 text-xs text-white/60">
          Try again closer to game time — rosters update throughout the week.
        </p>
      </section>
    )
  }

  return (
    <section
      className={cn(
        "rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm p-5",
        className
      )}
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-extrabold text-white">
          Key Players to Watch
        </span>
        <span
          className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 px-2 py-0.5 text-xs font-medium text-emerald-300"
          title={verifiedTooltip}
        >
          <span aria-hidden>✓</span>
          Verified
        </span>
        {keyPlayers.status === "limited" ? (
          <span className="rounded-full bg-amber-500/20 px-2 py-0.5 text-xs font-medium text-amber-300">
            Limited data
          </span>
        ) : null}
      </div>
      <p className="mt-1 text-xs text-white/60">{subtitle}</p>
      {keyPlayers.updatedAt && formatLastRefreshedUtc(keyPlayers.updatedAt) ? (
        <p className="mt-0.5 text-xs text-white/50">
          Last refreshed: {formatLastRefreshedUtc(keyPlayers.updatedAt)}
        </p>
      ) : null}
      {keyPlayers.limitedNote ? (
        <p className="mt-2 text-xs text-white/70">{keyPlayers.limitedNote}</p>
      ) : null}
      {keyPlayers.showRosterVerifiedNote ? (
        <p className="mt-1 text-xs text-white/50">Roster-verified</p>
      ) : null}
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <TeamCard
          title={homeTeamName}
          players={keyPlayers.homePlayers}
          defaultVisible={DEFAULT_VISIBLE}
          maxVisible={MAX_VISIBLE}
        />
        <TeamCard
          title={awayTeamName}
          players={keyPlayers.awayPlayers}
          defaultVisible={DEFAULT_VISIBLE}
          maxVisible={MAX_VISIBLE}
        />
      </div>
    </section>
  )
}
