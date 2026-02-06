"use client"

import Link from "next/link"
import { Lock } from "lucide-react"

type Props = {
  title?: string
  ctaHref?: string
  className?: string
}

export function ConfidenceLockedCard({
  title = "AI Confidence",
  ctaHref = "/billing",
  className,
}: Props) {
  return (
    <div className={`rounded-2xl border border-white/10 bg-black/40 p-4 shadow-sm ${className ?? ""}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Lock className="h-4 w-4 text-white/70" />
          <h3 className="text-base font-semibold text-white">{title}</h3>
        </div>
        <span className="rounded-full bg-white/10 px-2 py-1 text-xs font-semibold text-white/70">
          Pro
        </span>
      </div>

      <p className="mt-2 text-sm text-white/70">
        Confidence combines market signals, matchup stability, and data quality. Unlock the full breakdown.
      </p>

      <div className="mt-3 flex items-center gap-3">
        <Link
          href={ctaHref}
          className="inline-flex items-center justify-center rounded-xl bg-emerald-500 px-4 py-2 text-sm font-bold text-black hover:bg-emerald-400 transition-colors"
        >
          Unlock Confidence →
        </Link>

        <span className="text-xs text-white/50">
          Keeps the free analysis public — upgrades add depth.
        </span>
      </div>
    </div>
  )
}
