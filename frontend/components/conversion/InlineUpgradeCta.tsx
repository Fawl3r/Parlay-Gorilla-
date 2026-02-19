"use client"

import Link from "next/link"
import { Unlock } from "lucide-react"
import { cn } from "@/lib/utils"

export type InlineUpgradeCtaProps = {
  className?: string
  /** Optional context (e.g. "analysis" vs "landing") for future A/B copy */
  variant?: "default" | "compact"
}

/**
 * Small inline upgrade CTA card — helpful, not pushy. No modal, no blocking.
 * Links to /pricing (View Plans).
 */
export function InlineUpgradeCta({ className, variant = "default" }: InlineUpgradeCtaProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-[#00FF5E]/25 bg-black/50 backdrop-blur-sm p-4",
        "shadow-lg shadow-black/20",
        variant === "compact" && "p-3",
        className
      )}
    >
      <div className="flex items-center gap-3">
        <div className="rounded-lg bg-[#00FF5E]/15 p-2">
          <Unlock className="h-5 w-5 text-[#00FF5E]" aria-hidden />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-white">Unlock Full AI Intelligence</p>
          <p className="text-xs text-white/60 mt-0.5">
            Advanced AI research layer used by serious bettors daily.
          </p>
        </div>
        <Link
          href="/pricing"
          className="shrink-0 inline-flex items-center justify-center px-4 py-2 text-sm font-semibold text-black bg-[#00FF5E] rounded-lg hover:bg-[#22FF6E] transition-colors"
        >
          View Plans
        </Link>
      </div>
    </div>
  )
}
