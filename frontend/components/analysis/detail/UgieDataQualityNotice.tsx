"use client"

import { Info } from "lucide-react"
import { cn } from "@/lib/utils"

export type UgieDataQualityNoticeProps = {
  dataQualityNotice: {
    status: string
    missing: string[]
    missingMore: number
    provider: string
    stale: string[]
  } | null
  className?: string
}

function friendlyMissingLabel(item: string): string {
  const lower = item.toLowerCase()
  if (lower === "injuries" || lower === "injury") return "Injury and availability info"
  if (lower === "weather") return "Weather"
  if (lower === "lineup" || lower === "lineups") return "Lineup details"
  return item
}

export function UgieDataQualityNotice({ dataQualityNotice, className }: UgieDataQualityNoticeProps) {
  if (!dataQualityNotice) return null

  const { status, missing, missingMore, provider, stale } = dataQualityNotice
  const hasMissing = missing.length > 0 || missingMore > 0
  const missingFriendly =
    missing.length > 0
      ? missing.map(friendlyMissingLabel).join(", ") + (missingMore > 0 ? ` and ${missingMore} more` : "")
      : missingMore > 0
        ? `${missingMore} data type(s)`
        : ""
  const isFallback = provider.toLowerCase() === "fallback" || provider.toLowerCase() === "secondary"
  const hasStale = stale.length > 0

  return (
    <section className={cn("rounded-2xl border border-amber-500/20 bg-amber-500/5 backdrop-blur-sm p-5", className)}>
      <div className="flex items-center gap-2 text-sm font-semibold text-amber-200">
        <Info className="h-4 w-4 shrink-0" aria-hidden />
        About this analysis
      </div>
      <div className="mt-3 space-y-2 text-xs text-white/80">
        <p>
          We’re showing the analysis we can build from available data. You can still use it to inform your view of the
          game.
        </p>
        {hasMissing && (
          <p>
            <span className="text-white/90">Not available for this game:</span> {missingFriendly}.
            {missing.some((m) => m.toLowerCase().includes("injur")) && (
              <> Consider checking team or league sources for the latest lineup and injury news.</>
            )}
          </p>
        )}
        {isFallback && (
          <p className="text-white/70">
            Data is from an alternate source. We’ll show more detail when our primary data is available.
          </p>
        )}
        {!isFallback && provider && (
          <p className="text-white/70">Source: {provider}.</p>
        )}
        {hasStale && (
          <p className="text-white/70">Some stats may be from an earlier update.</p>
        )}
      </div>
    </section>
  )
}
