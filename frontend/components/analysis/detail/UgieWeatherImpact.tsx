"use client"

import { ChevronDown, ChevronUp } from "lucide-react"
import { useState } from "react"
import { cn } from "@/lib/utils"

export type UgieWeatherImpactProps = {
  weather: {
    why: string
    modifiers: { efficiency: number; volatility: number; confidence: number }
    rulesFired: string[]
    isMissingWarning?: boolean
  } | null
  className?: string
}

export function UgieWeatherImpact({ weather, className }: UgieWeatherImpactProps) {
  const [rulesOpen, setRulesOpen] = useState(false)
  if (!weather) return null

  const { why, modifiers, rulesFired, isMissingWarning } = weather
  const hasRules = (rulesFired?.length ?? 0) > 0

  return (
    <section className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm p-5", className)}>
      <div className="text-sm font-extrabold text-white">Weather Impact</div>
      {isMissingWarning ? (
        <p className="mt-3 text-sm text-white/70">Weather data missing — confidence slightly reduced.</p>
      ) : (
        <>
          {why ? <p className="mt-3 text-sm text-white/75">{why}</p> : null}
          <div className="mt-3 flex flex-wrap gap-2">
            <span className="rounded-lg border border-white/15 bg-white/5 px-2 py-1 text-xs text-white/80">
              Efficiency: {Number(modifiers.efficiency).toFixed(2)}
            </span>
            <span className="rounded-lg border border-white/15 bg-white/5 px-2 py-1 text-xs text-white/80">
              Volatility: {Number(modifiers.volatility).toFixed(2)}
            </span>
            <span className="rounded-lg border border-white/15 bg-white/5 px-2 py-1 text-xs text-white/80">
              Confidence: {Number(modifiers.confidence).toFixed(2)}
            </span>
          </div>
          {hasRules ? (
            <div className="mt-3">
              <button
                type="button"
                onClick={() => setRulesOpen(!rulesOpen)}
                className="flex items-center gap-1 text-xs text-white/60 hover:text-white/80"
              >
                {rulesOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                Rules fired ({rulesFired.length})
              </button>
              {rulesOpen ? (
                <ul className="mt-1 list-inside list-disc text-xs text-white/60">
                  {rulesFired.map((r, idx) => (
                    <li key={idx}>{r.replace(/_/g, " ")}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}
        </>
      )}
    </section>
  )
}
