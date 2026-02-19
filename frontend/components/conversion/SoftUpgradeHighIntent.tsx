"use client"

import Link from "next/link"
import { Sparkles } from "lucide-react"
import { cn } from "@/lib/utils"

export type SoftUpgradeHighIntentProps = {
  onDismiss?: () => void
  onViewPlans?: () => void
  className?: string
}

/**
 * High Intent level: upgrade panel after successful interaction.
 * "View Plans" — premium framing, same glass system.
 */
export function SoftUpgradeHighIntent({ onDismiss, onViewPlans, className }: SoftUpgradeHighIntentProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-white/12 bg-[rgba(18,18,23,0.8)] backdrop-blur-xl p-5",
        "shadow-lg shadow-emerald-500/5",
        className
      )}
    >
      <div className="flex items-start gap-3">
        <div className="rounded-lg bg-[#00FF5E]/15 p-2 shrink-0">
          <Sparkles className="h-5 w-5 text-[#00FF5E]" aria-hidden />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-white">
            Ready to access full AI analytics?
          </p>
          <p className="text-xs text-white/60 mt-0.5">
            Advanced Intelligence Layer · Full model visibility.
          </p>
          <div className="mt-4 flex items-center gap-3">
            <Link
              href="/pricing"
              onClick={onViewPlans}
              className="inline-flex items-center justify-center px-5 py-2.5 text-sm font-semibold text-black bg-[#00FF5E] rounded-lg hover:bg-[#22FF6E] transition-colors"
            >
              View Plans
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
