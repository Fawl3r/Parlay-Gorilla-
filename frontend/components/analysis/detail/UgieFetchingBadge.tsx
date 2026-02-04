"use client"

import { cn } from "@/lib/utils"
import { Loader2 } from "lucide-react"

export type UgieFetchingBadgeProps = {
  /** loading = spinner + "Fetching…"; info = no spinner, "Limited …" */
  variant: "loading" | "info"
  label: string
  className?: string
}

/**
 * Badge when roster or injury data is not ready (loading) or weak/placeholder (info).
 * loading = truly waiting → spinner + "Fetching roster…" / "Fetching injury data…"
 * info = we tried but signals are stale → "Limited roster data" / "Limited injury data" (no spinner)
 */
export function UgieFetchingBadge({ variant, label, className }: UgieFetchingBadgeProps) {
  return (
    <section
      className={cn(
        "rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm px-5 py-3 flex items-center gap-2",
        className
      )}
      aria-live="polite"
    >
      {variant === "loading" ? (
        <Loader2 className="h-4 w-4 shrink-0 animate-spin text-white/50" aria-hidden />
      ) : null}
      <span className="text-sm text-white/70">{label}</span>
    </section>
  )
}
