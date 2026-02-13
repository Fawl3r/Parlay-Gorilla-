"use client"

import { useEffect, useState } from "react"
import { AlertCircle } from "lucide-react"
import { api } from "@/lib/api"
import type { SafetySnapshotResponse } from "@/lib/api/types/system"
import { cn } from "@/lib/utils"

export function SafetyModeBanner() {
  const [snapshot, setSnapshot] = useState<SafetySnapshotResponse | null>(null)

  useEffect(() => {
    let cancelled = false
    api
      .getSafetySnapshot()
      .then((data) => {
        if (!cancelled && (data.state === "YELLOW" || data.state === "RED")) {
          setSnapshot(data)
        }
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [])

  if (!snapshot || snapshot.state === "GREEN") return null

  const isRed = snapshot.state === "RED"
  return (
    <div
      role="status"
      className={cn(
        "flex items-center gap-2 rounded-lg border px-3 py-2 text-sm",
        isRed
          ? "border-amber-500/50 bg-amber-500/10 text-amber-800 dark:text-amber-200"
          : "border-amber-400/40 bg-amber-400/5 text-amber-700 dark:text-amber-300"
      )}
    >
      <AlertCircle className="h-4 w-4 shrink-0" />
      <span>
        {isRed ? "Generation paused" : "Limited data mode"}
        {snapshot.reasons?.length ? ` — try again soon.` : ""}
      </span>
    </div>
  )
}
