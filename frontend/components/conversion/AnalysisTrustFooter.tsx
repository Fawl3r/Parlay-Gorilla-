"use client"

import { Shield } from "lucide-react"
import { cn } from "@/lib/utils"

const STALE_THRESHOLD_MS = 24 * 60 * 60 * 1000 // 24h

export type AnalysisTrustFooterProps = {
  /** Optional relative time string for team analytics (e.g. "3 min ago") */
  updatedLabel?: string
  /** Optional relative time string for analysis generation */
  generatedLabel?: string
  /** ISO timestamp of generation; when older than 24h we show an update note */
  generatedAtIso?: string
  className?: string
}

/**
 * Data provenance and trust signals beneath analysis.
 * Authority layer: sources + timestamps only (no fabricated data).
 */
export function AnalysisTrustFooter({
  updatedLabel,
  generatedLabel,
  generatedAtIso,
  className,
}: AnalysisTrustFooterProps) {
  const isOld =
    typeof generatedAtIso === "string" &&
    Number.isFinite(Date.parse(generatedAtIso)) &&
    Date.now() - new Date(generatedAtIso).getTime() > STALE_THRESHOLD_MS

  return (
    <footer
      className={cn(
        "mt-8 pt-6 border-t border-white/10 text-xs text-white/50 space-y-2",
        className
      )}
    >
      <p>Parlay Gorilla AI Models</p>
      <p className="inline-flex items-center gap-1.5">
        <Shield className="h-3.5 w-3.5 text-white/40" aria-hidden />
        <span>AI research verified</span>
      </p>
      {updatedLabel && <p>Team analytics updated {updatedLabel}</p>}
      {generatedLabel && <p>Analysis generated {generatedLabel}</p>}
      {isOld && (
        <p className="text-white/40 italic">We update analyses periodically. Refresh the page to see the latest when it’s ready.</p>
      )}
    </footer>
  )
}
