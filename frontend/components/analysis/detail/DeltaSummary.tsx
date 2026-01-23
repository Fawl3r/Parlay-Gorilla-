"use client"

import { cn } from "@/lib/utils"
import { Clock, AlertCircle } from "lucide-react"

export type DeltaSummaryData = {
  has_changes: boolean
  line_changes?: {
    spread?: { old: number; new: number; direction: "up" | "down" }
    total?: { old: number; new: number; direction: "up" | "down" }
    moneyline?: { home_old: string; home_new: string }
  }
  injury_changes?: string[]
  pick_changes?: string[]
  summary: string
  updated_at?: string
}

export type DeltaSummaryProps = {
  deltaSummary?: DeltaSummaryData
  className?: string
}

export function DeltaSummary({ deltaSummary, className }: DeltaSummaryProps) {
  if (!deltaSummary || !deltaSummary.has_changes) return null

  return (
    <section className={cn("rounded-2xl border border-orange-500/30 bg-orange-500/10 backdrop-blur-sm p-5", className)}>
      <div className="flex items-center gap-2 mb-3">
        <Clock className="w-5 h-5 text-orange-500" />
        <div className="text-sm font-extrabold text-white">What Changed</div>
      </div>

      <p className="text-sm text-white/80 mb-4">{deltaSummary.summary}</p>

      {deltaSummary.line_changes && (
        <div className="space-y-2 mb-3">
          {deltaSummary.line_changes.spread && (
            <div className="text-xs text-white/70">
              <span className="font-semibold">Spread:</span> {deltaSummary.line_changes.spread.old} → {deltaSummary.line_changes.spread.new}
              {deltaSummary.line_changes.spread.direction === "up" && " (↑)"}
              {deltaSummary.line_changes.spread.direction === "down" && " (↓)"}
            </div>
          )}
          {deltaSummary.line_changes.total && (
            <div className="text-xs text-white/70">
              <span className="font-semibold">Total:</span> {deltaSummary.line_changes.total.old} → {deltaSummary.line_changes.total.new}
              {deltaSummary.line_changes.total.direction === "up" && " (↑)"}
              {deltaSummary.line_changes.total.direction === "down" && " (↓)"}
            </div>
          )}
          {deltaSummary.line_changes.moneyline && (
            <div className="text-xs text-white/70">
              <span className="font-semibold">Moneyline:</span> {deltaSummary.line_changes.moneyline.home_old} → {deltaSummary.line_changes.moneyline.home_new}
            </div>
          )}
        </div>
      )}

      {deltaSummary.injury_changes && deltaSummary.injury_changes.length > 0 && (
        <div className="mb-3">
          <div className="flex items-center gap-1 mb-1">
            <AlertCircle className="w-3 h-3 text-yellow-500" />
            <span className="text-xs font-semibold text-white">Injury Updates:</span>
          </div>
          <ul className="space-y-1">
            {deltaSummary.injury_changes.map((injury, idx) => (
              <li key={idx} className="text-xs text-white/70">• {injury}</li>
            ))}
          </ul>
        </div>
      )}

      {deltaSummary.pick_changes && deltaSummary.pick_changes.length > 0 && (
        <div>
          <span className="text-xs font-semibold text-white">Pick Changes:</span>
          <ul className="space-y-1 mt-1">
            {deltaSummary.pick_changes.map((change, idx) => (
              <li key={idx} className="text-xs text-white/70">• {change}</li>
            ))}
          </ul>
        </div>
      )}

      {deltaSummary.updated_at && (
        <div className="mt-3 text-xs text-white/50">
          Updated: {new Date(deltaSummary.updated_at).toLocaleString()}
        </div>
      )}
    </section>
  )
}
