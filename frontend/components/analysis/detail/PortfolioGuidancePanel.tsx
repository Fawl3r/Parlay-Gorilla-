"use client"

import { cn } from "@/lib/utils"
import type { PortfolioGuidance } from "@/lib/api/types/analysis"
import { Shield, AlertTriangle, Zap } from "lucide-react"

/** User-friendly labels for internal pick keys shown in Portfolio Guidance. */
const PICK_KEY_LABELS: Record<string, string> = {
  ai_spread_pick: "Spread pick",
  ai_total_pick: "Total pick",
  safe_3_leg_sgp: "3-leg same-game parlay",
  balanced_6_leg_sgp: "6-leg same-game parlay",
}

function pickKeyToLabel(key: string): string {
  return PICK_KEY_LABELS[key] ?? key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
}

export type PortfolioGuidancePanelProps = {
  portfolioGuidance?: PortfolioGuidance
  className?: string
}

export function PortfolioGuidancePanel({
  portfolioGuidance,
  className,
}: PortfolioGuidancePanelProps) {
  if (!portfolioGuidance) return null

  const riskBuckets = [
    {
      level: "low_risk",
      label: "Low Risk",
      icon: Shield,
      color: "text-green-500",
      bg: "bg-green-500/20",
      picks: portfolioGuidance.low_risk,
    },
    {
      level: "medium_risk",
      label: "Medium Risk",
      icon: AlertTriangle,
      color: "text-yellow-500",
      bg: "bg-yellow-500/20",
      picks: portfolioGuidance.medium_risk,
    },
    {
      level: "high_risk",
      label: "High Risk",
      icon: Zap,
      color: "text-red-500",
      bg: "bg-red-500/20",
      picks: portfolioGuidance.high_risk,
    },
  ]

  return (
    <section className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm p-5", className)}>
      <div className="text-sm font-extrabold text-white mb-4">Portfolio Guidance</div>

      {portfolioGuidance.exposure_note && (
        <p className="text-xs text-white/60 mb-4">{portfolioGuidance.exposure_note}</p>
      )}

      <div className="space-y-4">
        {riskBuckets.map((bucket) => {
          const Icon = bucket.icon
          if (!bucket.picks || bucket.picks.length === 0) return null

          return (
            <div key={bucket.level} className="rounded-lg border border-white/5 bg-white/5 p-4">
              <div className="flex items-center gap-2 mb-2">
                <Icon className={cn("w-4 h-4", bucket.color)} />
                <span className={cn("text-sm font-semibold", bucket.color)}>{bucket.label}</span>
              </div>
              <ul className="space-y-1">
                {bucket.picks.map((pick, idx) => (
                  <li key={idx} className="text-xs text-white/70 flex items-start gap-2">
                    <span className="text-white/40 mt-0.5">•</span>
                    <span>{pickKeyToLabel(pick)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )
        })}
      </div>
    </section>
  )
}
