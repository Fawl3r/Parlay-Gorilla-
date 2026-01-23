"use client"

import { cn } from "@/lib/utils"
import type { MarketDisagreement } from "@/lib/api/types/analysis"
import { AlertTriangle, CheckCircle, TrendingUp } from "lucide-react"

export type MarketDisagreementBadgeProps = {
  marketDisagreement?: MarketDisagreement
  className?: string
}

export function MarketDisagreementBadge({
  marketDisagreement,
  className,
}: MarketDisagreementBadgeProps) {
  if (!marketDisagreement) return null

  const flagConfig = {
    consensus: { icon: CheckCircle, color: "text-green-500", bg: "bg-green-500/20", label: "Consensus" },
    volatile: { icon: TrendingUp, color: "text-orange-500", bg: "bg-orange-500/20", label: "Volatile" },
    sharp_vs_public: { icon: AlertTriangle, color: "text-yellow-500", bg: "bg-yellow-500/20", label: "Sharp vs Public" },
  }

  const config = flagConfig[marketDisagreement.flag] || flagConfig.consensus
  const Icon = config.icon

  const varianceConfig = {
    low: { color: "text-green-500", label: "Low" },
    med: { color: "text-yellow-500", label: "Medium" },
    high: { color: "text-red-500", label: "High" },
  }

  return (
    <section className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm p-5", className)}>
      <div className="flex items-center gap-2 mb-3">
        <Icon className={cn("w-5 h-5", config.color)} />
        <div className="text-sm font-extrabold text-white">Market Disagreement</div>
        <span className={cn("text-xs px-2 py-0.5 rounded", config.bg, config.color)}>
          {config.label}
        </span>
      </div>

      {marketDisagreement.explanation && (
        <p className="text-xs text-white/60 mb-4">{marketDisagreement.explanation}</p>
      )}

      <div className="space-y-2 text-xs">
        <div className="flex items-center justify-between">
          <span className="text-white/70">Spread Variance:</span>
          <span className={cn("font-semibold", varianceConfig[marketDisagreement.spread_variance].color)}>
            {varianceConfig[marketDisagreement.spread_variance].label}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-white/70">Total Variance:</span>
          <span className={cn("font-semibold", varianceConfig[marketDisagreement.total_variance].color)}>
            {varianceConfig[marketDisagreement.total_variance].label}
          </span>
        </div>
      </div>

      {marketDisagreement.books_split_summary && (
        <p className="text-xs text-white/60 mt-3">{marketDisagreement.books_split_summary}</p>
      )}

      {marketDisagreement.sharp_indicator && (
        <div className={cn("mt-4 p-3 rounded-lg", config.bg)}>
          <div className="text-xs font-semibold text-white mb-1">Sharp Money Signals</div>
          {marketDisagreement.sharp_indicator.has_sharp_signals ? (
            <div className="space-y-1">
              {marketDisagreement.sharp_indicator.signals?.map((signal, idx) => (
                <div key={idx} className="text-xs text-white/80">• {signal}</div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-white/60">{marketDisagreement.sharp_indicator.summary}</div>
          )}
        </div>
      )}
    </section>
  )
}
