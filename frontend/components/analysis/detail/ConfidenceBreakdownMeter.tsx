"use client"

import { cn } from "@/lib/utils"
import type { ConfidenceBreakdown } from "@/lib/api/types/analysis"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"

export type ConfidenceBreakdownMeterProps = {
  confidenceBreakdown?: ConfidenceBreakdown
  className?: string
}

export function ConfidenceBreakdownMeter({
  confidenceBreakdown,
  className,
}: ConfidenceBreakdownMeterProps) {
  if (!confidenceBreakdown) return null

  const components = [
    { label: "Market Agreement", value: confidenceBreakdown.market_agreement, max: 30, color: "bg-blue-500" },
    { label: "Statistical Edge", value: confidenceBreakdown.statistical_edge, max: 30, color: "bg-green-500" },
    { label: "Situational Edge", value: confidenceBreakdown.situational_edge, max: 20, color: "bg-yellow-500" },
    { label: "Performance Metrics", value: confidenceBreakdown.data_quality, max: 20, color: "bg-purple-500" },
  ]

  const trend = confidenceBreakdown.trend as { direction?: "up" | "down"; change?: number; previous?: number } | undefined

  return (
    <section className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm p-5", className)}>
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm font-extrabold text-white">Model Confidence Breakdown</div>
        <div className="text-lg font-bold text-white">{Math.round(confidenceBreakdown.confidence_total)}%</div>
      </div>

      {confidenceBreakdown.explanation && (
        <p className="text-xs text-white/60 mb-4">{confidenceBreakdown.explanation}</p>
      )}

      {trend && (
        <div className="mb-4 flex items-center gap-2 text-xs">
          {trend.direction === "up" && <TrendingUp className="w-4 h-4 text-green-500" />}
          {trend.direction === "down" && <TrendingDown className="w-4 h-4 text-red-500" />}
          {!trend.direction && <Minus className="w-4 h-4 text-white/60" />}
          <span className="text-white/70">
            {trend.direction === "up" ? "Up" : trend.direction === "down" ? "Down" : "No change"}{" "}
            {trend.change !== undefined && `${Math.abs(trend.change).toFixed(1)}%`} from previous analysis
            {trend.previous !== undefined && ` (was ${trend.previous.toFixed(0)}%)`}
          </span>
        </div>
      )}

      <div className="space-y-3">
        {components.map((comp) => {
          const pct = comp.max > 0 ? Math.round((comp.value / comp.max) * 100) : 0
          return (
            <div key={comp.label}>
              <div className="flex items-center justify-between text-xs text-white/60 mb-1">
                <span className="font-semibold text-white/80">{comp.label}</span>
                <span>{comp.value.toFixed(1)} / {comp.max}</span>
              </div>
              <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                <div
                  className={cn("h-full transition-all duration-500", comp.color)}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
