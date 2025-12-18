"use client"

import { useMemo, useState } from "react"
import { motion } from "framer-motion"

import type { CoverageTicket, ParlayCoverageResponse } from "@/lib/api"

function formatInt(n: number) {
  try {
    return new Intl.NumberFormat("en-US").format(n)
  } catch {
    return String(n)
  }
}

function formatTicketForCopy(ticket: CoverageTicket) {
  const lines: string[] = []
  lines.push(`${ticket.analysis.num_legs}-leg ticket • AI ${ticket.analysis.combined_ai_probability.toFixed(2)}% • Odds ${ticket.analysis.parlay_odds}`)
  lines.push("")
  for (const leg of ticket.analysis.legs) {
    lines.push(`${leg.pick_display} (${leg.odds}) — ${leg.game}`)
  }
  return lines.join("\n")
}

function TicketCard({ title, ticket }: { title: string; ticket: CoverageTicket }) {
  const [expanded, setExpanded] = useState(false)
  const analysis = ticket.analysis

  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-4 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-white font-bold truncate">{title}</div>
          <div className="text-xs text-white/60">
            {analysis.num_legs} legs • AI {analysis.combined_ai_probability.toFixed(2)}% • Implied{" "}
            {analysis.combined_implied_probability.toFixed(2)}% • Odds {analysis.parlay_odds}
          </div>
          <div className="text-[11px] text-white/50">Upsets in this ticket: {ticket.num_upsets}</div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={async () => {
              try {
                await navigator.clipboard.writeText(formatTicketForCopy(ticket))
              } catch {
                // ignore
              }
            }}
            className="px-3 py-1.5 text-xs font-bold rounded bg-black/40 border border-white/10 text-white hover:bg-black/60"
          >
            Copy
          </button>
          <button
            onClick={() => setExpanded((v) => !v)}
            className="px-3 py-1.5 text-xs font-bold rounded bg-black/40 border border-white/10 text-white hover:bg-black/60"
          >
            {expanded ? "Hide" : "Show"}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="space-y-2">
          {analysis.legs.map((leg, idx) => (
            <div key={`${leg.game_id}-${idx}`} className="rounded-lg border border-white/10 bg-black/30 p-3">
              <div className="text-xs text-white/60 truncate">{leg.game}</div>
              <div className="text-white font-medium truncate">{leg.pick_display}</div>
              <div className="text-xs text-white/60">
                Odds {leg.odds} • AI {leg.ai_probability.toFixed(1)}% • Conf {leg.confidence.toFixed(0)}% • Edge{" "}
                <span className={leg.edge >= 0 ? "text-green-400" : "text-red-400"}>
                  {leg.edge >= 0 ? "+" : ""}
                  {leg.edge.toFixed(1)}%
                </span>
              </div>
            </div>
          ))}
          <div className="rounded-lg border border-white/10 bg-black/30 p-3">
            <div className="text-white/80 font-bold text-sm mb-1">Notes</div>
            <div className="text-xs text-white/70 whitespace-pre-line">{analysis.ai_risk_notes}</div>
          </div>
        </div>
      )}
    </div>
  )
}

export function CoveragePackModal({
  response,
  onClose,
}: {
  response: ParlayCoverageResponse
  onClose: () => void
}) {
  const byUpsetSorted = useMemo(() => {
    const entries = Object.entries(response.by_upset_count || {})
    entries.sort((a, b) => Number(a[0]) - Number(b[0]))
    return entries
  }, [response.by_upset_count])

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="w-full max-w-6xl max-h-[92vh] overflow-y-auto rounded-2xl border border-white/10 bg-black/70 p-4 sm:p-6 space-y-4"
      >
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white">Coverage Pack</h2>
            <p className="text-white/60 text-sm">
              {response.num_games} games • {formatInt(response.total_scenarios)} total scenarios (2^{response.num_games})
            </p>
          </div>
          <button onClick={onClose} className="text-white/60 hover:text-white text-2xl">
            ✕
          </button>
        </div>

        <details className="rounded-xl border border-white/10 bg-white/5 p-4">
          <summary className="cursor-pointer select-none text-white/80 font-bold text-sm">
            Upset counts breakdown (C(n,k))
          </summary>
          <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-2">
            {byUpsetSorted.map(([k, v]) => (
              <div key={k} className="flex items-center justify-between bg-black/30 border border-white/10 rounded px-2 py-1">
                <span className="text-xs text-white/60">{k} upsets</span>
                <span className="text-xs text-white/80">{formatInt(v)}</span>
              </div>
            ))}
          </div>
        </details>

        <div className="grid gap-4 lg:grid-cols-2">
          <div className="space-y-3">
            <h3 className="text-white font-bold">Scenario Tickets</h3>
            {response.scenario_tickets?.length ? (
              response.scenario_tickets.map((ticket, idx) => (
                <TicketCard key={`scenario-${idx}`} title={`Scenario #${idx + 1}`} ticket={ticket} />
              ))
            ) : (
              <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-white/60 text-sm">
                No scenario tickets requested.
              </div>
            )}
          </div>
          <div className="space-y-3">
            <h3 className="text-white font-bold">Round-Robin Tickets</h3>
            {response.round_robin_tickets?.length ? (
              response.round_robin_tickets.map((ticket, idx) => (
                <TicketCard key={`rr-${idx}`} title={`Round Robin #${idx + 1}`} ticket={ticket} />
              ))
            ) : (
              <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-white/60 text-sm">
                No round-robin tickets requested.
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}




