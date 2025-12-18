"use client"

import { Loader2, CheckCircle2, AlertTriangle } from "lucide-react"
import { cn } from "@/lib/utils"
import type { InscriptionStatus } from "@/lib/api"

export function InscriptionStatusPill({
  status,
}: {
  status: InscriptionStatus
}) {
  const base =
    "inline-flex items-center gap-1.5 rounded-full border px-2 py-1 text-xs font-semibold"

  if (status === "queued") {
    return (
      <span className={cn(base, "border-cyan-500/30 bg-cyan-500/10 text-cyan-300")}>
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        Queued
      </span>
    )
  }

  if (status === "confirmed") {
    return (
      <span className={cn(base, "border-emerald-500/30 bg-emerald-500/10 text-emerald-300")}>
        <CheckCircle2 className="h-3.5 w-3.5" />
        Confirmed
      </span>
    )
  }

  if (status === "failed") {
    return (
      <span className={cn(base, "border-amber-500/30 bg-amber-500/10 text-amber-200")}>
        <AlertTriangle className="h-3.5 w-3.5" />
        Failed
      </span>
    )
  }

  return (
    <span className={cn(base, "border-white/10 bg-white/[0.03] text-gray-300")}>None</span>
  )
}



