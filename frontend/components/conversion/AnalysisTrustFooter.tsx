"use client"

import { Shield } from "lucide-react"
import { cn } from "@/lib/utils"

export type AnalysisTrustFooterProps = {
  /** Optional relative time string for team analytics (e.g. "3 min ago") */
  updatedLabel?: string
  /** Optional relative time string for analysis generation */
  generatedLabel?: string
  className?: string
}

/**
 * Data provenance and trust signals beneath analysis.
 * Authority layer: sources + timestamps only (no fabricated data).
 */
export function AnalysisTrustFooter({ updatedLabel, generatedLabel, className }: AnalysisTrustFooterProps) {
  return (
    <footer
      className={cn(
        "mt-8 pt-6 border-t border-white/10 text-xs text-white/50 space-y-2",
        className
      )}
    >
      <p className="font-medium text-white/60">Data Sources</p>
      <ul className="space-y-0.5 list-none">
        <li>Odds API (Markets)</li>
        <li>API-Sports (Team Analytics)</li>
        <li>Parlay Gorilla AI Models</li>
      </ul>
      <p className="inline-flex items-center justify-center gap-1.5 pt-1">
        <Shield className="h-3.5 w-3.5 text-white/40" aria-hidden />
        <span>AI research verified</span>
      </p>
      {updatedLabel && <p>Team analytics updated {updatedLabel}</p>}
      {generatedLabel && <p>Analysis generated {generatedLabel}</p>}
    </footer>
  )
}
