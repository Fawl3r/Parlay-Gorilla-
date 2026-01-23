"use client"

import { cn } from "@/lib/utils"
import type { PropRecommendations } from "@/lib/api/types/analysis"
import { Target, TrendingUp } from "lucide-react"

export type PropsPanelProps = {
  propRecommendations?: PropRecommendations
  className?: string
}

export function PropsPanel({ propRecommendations, className }: PropsPanelProps) {
  if (!propRecommendations || !propRecommendations.top_props || propRecommendations.top_props.length === 0) {
    return null
  }

  return (
    <section className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm p-5", className)}>
      <div className="flex items-center gap-2 mb-4">
        <Target className="w-5 h-5 text-white/60" />
        <div className="text-sm font-extrabold text-white">Top Prop Recommendations</div>
      </div>

      {propRecommendations.notes && (
        <p className="text-xs text-white/60 mb-4">{propRecommendations.notes}</p>
      )}

      <div className="space-y-3">
        {propRecommendations.top_props.map((prop, idx) => (
          <div key={idx} className="rounded-lg border border-white/5 bg-white/5 p-4">
            <div className="flex items-start justify-between mb-2">
              <div>
                <div className="text-sm font-semibold text-white">{prop.player}</div>
                <div className="text-xs text-white/60">{prop.market}</div>
              </div>
              <div className="text-right">
                <div className="text-sm font-bold text-white">{prop.pick}</div>
                {prop.ev_score !== undefined && (
                  <div className="flex items-center gap-1 text-xs text-green-500 mt-1">
                    <TrendingUp className="w-3 h-3" />
                    <span>EV: {prop.ev_score > 0 ? "+" : ""}{prop.ev_score.toFixed(1)}%</span>
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-white/70">Confidence:</span>
              <span className="font-semibold text-white">{prop.confidence}%</span>
            </div>
            <p className="text-xs text-white/60 mb-2">{prop.why}</p>
            {prop.best_odds && (
              <div className="text-xs text-white/50">
                Best Odds: {prop.best_odds.book} {prop.best_odds.price}
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}
