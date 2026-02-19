"use client"

import { Check } from "lucide-react"
import { cn } from "@/lib/utils"

export type ValueReinforcementStripProps = {
  /** e.g. "Analysis updated recently" */
  analysisUpdated?: boolean
  /** e.g. "Model identified statistical edge" */
  modelEdge?: boolean
  /** e.g. "Research depth: High" */
  researchDepth?: "high" | "medium" | "low" | null
  className?: string
}

/**
 * Small value confirmations shown before an upgrade prompt.
 * Users must feel success before seeing upgrade.
 */
export function ValueReinforcementStrip({
  analysisUpdated,
  modelEdge,
  researchDepth,
  className,
}: ValueReinforcementStripProps) {
  const items: string[] = []
  if (analysisUpdated) items.push("Analysis updated recently")
  if (modelEdge) items.push("Model identified statistical edge")
  if (researchDepth === "high") items.push("Research depth: High")
  if (researchDepth === "medium") items.push("Research depth: Medium")

  if (items.length === 0) return null

  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-white/70",
        className
      )}
      role="list"
      aria-label="Value signals"
    >
      {items.map((label) => (
        <span key={label} className="inline-flex items-center gap-1.5" role="listitem">
          <Check className="h-3.5 w-3.5 text-emerald-500/90 shrink-0" aria-hidden />
          {label}
        </span>
      ))}
    </div>
  )
}
