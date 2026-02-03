"use client"

import type { DerivedTicket, UpsetPossibilities } from "@/lib/api"
import { ClientPortal } from "@/components/ui/ClientPortal"

function formatInt(n: number) {
  try {
    return new Intl.NumberFormat("en-US").format(n)
  } catch {
    return String(n)
  }
}

export function HedgePackModal({
  tickets,
  upsetPossibilities,
  onClose,
  onApplyTicket,
}: {
  tickets: DerivedTicket[]
  upsetPossibilities: UpsetPossibilities | null
  onClose: () => void
  onApplyTicket?: (ticket: DerivedTicket) => void
}) {
  return (
    <ClientPortal>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="absolute inset-0 bg-black/70" aria-hidden onClick={onClose} />
        <div className="relative w-full max-w-lg max-h-[90vh] overflow-auto rounded-2xl border border-white/10 bg-gray-900 shadow-2xl">
          <div className="sticky top-0 z-10 flex items-center justify-between border-b border-white/10 bg-gray-900/95 px-4 py-3 backdrop-blur">
            <h2 className="text-lg font-bold text-white">Coverage Pack (Hedge tickets)</h2>
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg px-3 py-1.5 text-sm font-medium text-white/80 hover:bg-white/10"
            >
              Close
            </button>
          </div>
          <div className="p-4 space-y-4">
            {upsetPossibilities && (
              <div className="rounded-xl border border-white/10 bg-white/5 p-3">
                <div className="text-sm font-semibold text-white/90">
                  With {upsetPossibilities.n} picks, {formatInt(upsetPossibilities.total)} possible flip combinations
                </div>
                <details className="mt-2 text-xs text-white/60">
                  <summary className="cursor-pointer">Breakdown by # of upsets</summary>
                  <div className="mt-2 grid grid-cols-2 gap-2">
                    {upsetPossibilities.breakdown.map(({ k, count }) => (
                      <div key={k} className="flex justify-between rounded bg-black/20 px-2 py-1">
                        <span>{k} upset{k !== 1 ? "s" : ""}</span>
                        <span>{formatInt(count)}</span>
                      </div>
                    ))}
                  </div>
                </details>
              </div>
            )}
            {tickets.map((ticket) => (
              <div key={ticket.ticket_id} className="rounded-xl border border-white/10 bg-white/5 p-4 space-y-2">
                <div className="text-white font-semibold">{ticket.label}</div>
                {ticket.notes && <p className="text-xs text-white/60">{ticket.notes}</p>}
                <div className="text-[11px] text-white/50">
                  {ticket.flip_count} pick{ticket.flip_count !== 1 ? "s" : ""} flipped • {ticket.picks.length} total
                </div>
                {onApplyTicket && (
                  <button
                    type="button"
                    onClick={() => onApplyTicket(ticket)}
                    className="mt-2 rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-500"
                  >
                    Apply to slip
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </ClientPortal>
  )
}
