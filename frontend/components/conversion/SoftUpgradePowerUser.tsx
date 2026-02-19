"use client"

import Link from "next/link"
import { BarChart3 } from "lucide-react"
import { cn } from "@/lib/utils"

export type SoftUpgradePowerUserProps = {
  onDismiss?: () => void
  onLearnMore?: () => void
  className?: string
}

/**
 * Power User level: inline card after analysis. "Learn More" button.
 * Platform module style — glass card, analytical language.
 */
export function SoftUpgradePowerUser({ onDismiss, onLearnMore, className }: SoftUpgradePowerUserProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-white/8 bg-[rgba(18,18,23,0.6)] backdrop-blur-md p-4",
        "shadow-lg shadow-black/20",
        className
      )}
    >
      <div className="flex items-start gap-3">
        <div className="rounded-lg bg-white/8 p-2 shrink-0">
          <BarChart3 className="h-5 w-5 text-white/80" aria-hidden />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white">
            You&apos;re using advanced research features.
          </p>
          <p className="text-xs text-white/60 mt-0.5">
            Premium unlocks full intelligence visibility.
          </p>
          <div className="mt-3 flex items-center gap-2">
            <Link
              href="/pricing"
              onClick={onLearnMore}
              className="inline-flex items-center justify-center px-4 py-2 text-sm font-semibold text-black bg-[#00FF5E] rounded-lg hover:bg-[#22FF6E] transition-colors"
            >
              Learn More
            </Link>
            {onDismiss && (
              <button
                type="button"
                onClick={onDismiss}
                className="text-xs text-white/50 hover:text-white/70 transition-colors"
              >
                Dismiss
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
