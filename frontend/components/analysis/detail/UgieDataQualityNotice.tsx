"use client"

import { AlertTriangle } from "lucide-react"
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

export function UgieDataQualityNotice({ dataQualityNotice, className }: UgieDataQualityNoticeProps) {
  if (!dataQualityNotice) return null

  const { status, missing, missingMore, provider, stale } = dataQualityNotice
  const missingDisplay = missing.length > 0 ? missing.join(", ") + (missingMore > 0 ? ` +${missingMore} more` : "") : ""
  const staleDisplay = stale.length > 0 ? stale.join(", ") : ""

  return (
    <section className={cn("rounded-2xl border border-amber-500/20 bg-amber-500/5 backdrop-blur-sm p-5", className)}>
      <div className="flex items-center gap-2 text-sm font-extrabold text-amber-200">
        <AlertTriangle className="h-4 w-4 shrink-0" />
        Data Quality Notice
      </div>
      <div className="mt-3 space-y-2 text-xs text-white/80">
        <div><span className="text-white/50">Status:</span> {status}</div>
        {missingDisplay ? <div><span className="text-white/50">Missing:</span> {missingDisplay}</div> : null}
        {provider ? <div><span className="text-white/50">Provider:</span> {provider}</div> : null}
        {staleDisplay ? <div><span className="text-white/50">Stale:</span> {staleDisplay}</div> : null}
      </div>
    </section>
  )
}
