"use client"

import { cn } from "@/lib/utils"

export type InjuryEntry = { name?: string; status?: string; type?: string; desc?: string; reported_at?: string | null }

export type UgieAvailabilityImpactProps = {
  availability: { signals: { key: string; value: unknown }[]; whySummary: string } | null
  injuriesStatus?: "ready" | "stale" | "missing" | "unavailable"
  injuriesReason?: string | null
  injuriesByTeam?: { home: InjuryEntry[]; away: InjuryEntry[] }
  injuriesLastUpdatedAt?: string | null
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

const UNABLE_TO_ASSESS = "Unable to assess injury impact"

function isPlaceholderNoData(why: string, signals: { key: string; value: unknown }[]): boolean {
  if (!why.includes(UNABLE_TO_ASSESS)) return false
  if (signals.length === 0) return true
  const allZero = signals.every((s) => s?.value === 0 || s?.value === "0")
  return allZero
}

export function UgieAvailabilityImpact({
  availability,
  injuriesStatus,
  injuriesReason,
  injuriesByTeam,
  injuriesLastUpdatedAt,
  className,
}: UgieAvailabilityImpactProps) {
  const hasEntries = injuriesByTeam && (injuriesByTeam.home?.length > 0 || injuriesByTeam.away?.length > 0)
  const noUpdates = injuriesStatus === "ready" && injuriesReason === "no_updates"
  const unavailable = injuriesStatus === "unavailable"

  if (unavailable && !availability) {
    return (
      <section className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm p-5", className)}>
        <div className="text-sm font-extrabold text-white">Availability Impact</div>
        <div className="mt-3 rounded-xl border border-white/10 bg-black/25 p-3">
          <div className="text-sm leading-6 text-white/85">Injuries unavailable</div>
        </div>
      </section>
    )
  }

  if (noUpdates && !hasEntries) {
    return (
      <section className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm p-5", className)}>
        <div className="text-sm font-extrabold text-white">Availability Impact</div>
        <div className="mt-3 rounded-xl border border-white/10 bg-black/25 p-3">
          <div className="text-sm leading-6 text-white/85">
            No injuries reported for either team yet.
          </div>
        </div>
      </section>
    )
  }

  if (!availability && !hasEntries) return null
  const why = availability ? String(availability.whySummary ?? "").trim() : ""
  const signals = (availability?.signals ?? []).filter((s) => s?.key).slice(0, 10)
  if (!why && signals.length === 0 && !hasEntries) return null

  const showGracefulMessage = availability ? isPlaceholderNoData(why, signals) && !hasEntries : false

  return (
    <section className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm p-5", className)}>
      <div className="text-sm font-extrabold text-white">Availability Impact</div>
      {injuriesLastUpdatedAt && (
        <div className="mt-1 text-[11px] text-white/50">Last updated {injuriesLastUpdatedAt.slice(0, 10)}</div>
      )}
      {hasEntries ? (
        <div className="mt-3 space-y-3">
          {injuriesByTeam!.home?.length > 0 ? (
            <div className="rounded-xl border border-white/10 bg-black/25 p-3">
              <div className="text-[11px] uppercase tracking-wide text-white/50">Home</div>
              <ul className="mt-2 space-y-1 text-sm text-white/85">
                {injuriesByTeam!.home.map((e, i) => (
                  <li key={i}>{e.name ?? "—"} — {e.status ?? "out"}{e.desc ? ` (${e.desc})` : ""}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {injuriesByTeam!.away?.length > 0 ? (
            <div className="rounded-xl border border-white/10 bg-black/25 p-3">
              <div className="text-[11px] uppercase tracking-wide text-white/50">Away</div>
              <ul className="mt-2 space-y-1 text-sm text-white/85">
                {injuriesByTeam!.away.map((e, i) => (
                  <li key={i}>{e.name ?? "—"} — {e.status ?? "out"}{e.desc ? ` (${e.desc})` : ""}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
      {showGracefulMessage ? (
        <div className="mt-3 rounded-xl border border-white/10 bg-black/25 p-3">
          <div className="text-sm leading-6 text-white/85">
            Injury updates haven&apos;t posted for this matchup yet. Check back closer to game time.
          </div>
        </div>
      ) : (
        <>
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
                    <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-amber-400 shrink-0" aria-hidden="true" />
                    <div className="leading-6">{formatSignal(s)}</div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </>
      )}
    </section>
  )
}
