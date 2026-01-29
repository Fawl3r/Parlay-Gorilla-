"use client"

import { cn } from "@/lib/utils"

export type UgieAvailabilityImpactProps = {
  availability: { signals: { key: string; value: unknown }[]; whySummary: string } | null
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

export function UgieAvailabilityImpact({ availability, className }: UgieAvailabilityImpactProps) {
  if (!availability) return null
  const why = String(availability.whySummary ?? "").trim()
  const signals = (availability.signals ?? []).filter((s) => s?.key).slice(0, 10)
  if (!why && signals.length === 0) return null

  return (
    <section className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm p-5", className)}>
      <div className="text-sm font-extrabold text-white">Availability Impact</div>
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
    </section>
  )
}
