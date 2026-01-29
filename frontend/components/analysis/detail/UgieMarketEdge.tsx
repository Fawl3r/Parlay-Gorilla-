"use client"

import { cn } from "@/lib/utils"

export type UgieMarketEdgeProps = {
  marketEdge: {
    whySummary: string
    signals: { key: string; value: unknown }[]
    marketSnapshot: Record<string, unknown>
  } | null
  className?: string
}

function formatSignal(s: { key: string; value: unknown }): string {
  const key = String(s?.key ?? "").trim().replace(/_/g, " ")
  const v = s?.value
  if (v == null) return key
  if (typeof v === "string") return `${key}: ${v}`
  if (typeof v === "number") return `${key}: ${v}`
  if (typeof v === "boolean") return `${key}: ${v ? "Yes" : "No"}`
  return key
}

function snapshotEntries(snapshot: Record<string, unknown>): [string, string][] {
  const out: [string, string][] = []
  for (const [k, v] of Object.entries(snapshot)) {
    const key = String(k).trim().replace(/_/g, " ")
    if (!key) continue
    const val = v == null ? "" : typeof v === "object" ? JSON.stringify(v) : String(v)
    out.push([key, val])
  }
  return out.slice(0, 12)
}

export function UgieMarketEdge({ marketEdge, className }: UgieMarketEdgeProps) {
  if (!marketEdge) return null

  const why = String(marketEdge.whySummary ?? "").trim()
  const signals = (marketEdge.signals ?? []).filter((s) => s?.key).slice(0, 8)
  const chips = snapshotEntries(marketEdge.marketSnapshot ?? {})

  if (!why && signals.length === 0 && chips.length === 0) return null

  return (
    <section className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm p-5", className)}>
      <div className="text-sm font-extrabold text-white">Market Edge</div>
      {why ? (
        <div className="mt-3 rounded-xl border border-white/10 bg-black/25 p-3">
          <div className="text-[11px] uppercase tracking-wide text-white/50">Summary</div>
          <div className="mt-1 text-sm leading-6 text-white/85 whitespace-pre-wrap">{why}</div>
        </div>
      ) : null}
      {signals.length > 0 ? (
        <div className="mt-3">
          <div className="text-[11px] uppercase tracking-wide text-white/50">Signals</div>
          <div className="mt-2 space-y-2">
            {signals.map((s, idx) => (
              <div key={idx} className="flex items-start gap-2 text-sm text-white/85">
                <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-violet-400 shrink-0" aria-hidden="true" />
                <div className="leading-6">{formatSignal(s)}</div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
      {chips.length > 0 ? (
        <div className="mt-3">
          <div className="text-[11px] uppercase tracking-wide text-white/50">Market snapshot</div>
          <div className="mt-2 flex flex-wrap gap-2">
            {chips.map(([key, val]) => (
              <span
                key={key}
                className="rounded-lg border border-white/15 bg-white/5 px-2 py-1 text-xs text-white/80"
              >
                {key}: {val}
              </span>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  )
}
