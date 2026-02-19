"use client"

import { cn } from "@/lib/utils"

export type SoftUpgradeEngagedProps = {
  className?: string
}

/**
 * Engaged level: subtle inline message. No CTA button.
 * "Unlock deeper AI intelligence."
 */
export function SoftUpgradeEngaged({ className }: SoftUpgradeEngagedProps) {
  return (
    <p
      className={cn(
        "text-sm text-white/70 italic",
        "rounded-lg border border-white/6 bg-[rgba(18,18,23,0.4)] backdrop-blur-sm px-3 py-2",
        className
      )}
    >
      Unlock deeper AI intelligence.
    </p>
  )
}
