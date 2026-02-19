"use client"

import { useEffect } from "react"
import { Lock } from "lucide-react"
import { cn } from "@/lib/utils"
import { recordBlurredContentView, emitIntentEvent } from "@/lib/monetization-timing"

export type BlurredPremiumOverlayProps = {
  /** Main message above lock */
  title?: string
  /** Subtext below title */
  subtext?: string
  className?: string
}

const DEFAULT_TITLE = "Premium AI Insight Locked"
const DEFAULT_SUBTEXT = "Unlock full AI analysis and edge detection."

/**
 * Overlay for premium-gated content: blur, gradient fade, lock icon, CTA copy.
 * GPU-friendly (backdrop-blur, no layout shift). Use over real content so users see value but cannot access it.
 * Records blurred view for intent timing; shows "Included in Premium Intelligence" for value preview.
 */
export function BlurredPremiumOverlay({
  title = DEFAULT_TITLE,
  subtext = DEFAULT_SUBTEXT,
  className,
}: BlurredPremiumOverlayProps) {
  useEffect(() => {
    recordBlurredContentView()
    emitIntentEvent("blurred_content_viewed")
  }, [])

  return (
    <div
      className={cn(
        "absolute inset-0 z-10 flex flex-col items-center justify-center rounded-lg",
        "bg-black/40 backdrop-blur-md",
        "border border-white/10",
        "pg-premium-shimmer",
        className
      )}
      aria-hidden
    >
      <div
        className="absolute inset-0 rounded-lg bg-gradient-to-t from-black/80 via-transparent to-transparent pointer-events-none"
        style={{ background: "linear-gradient(to top, rgba(0,0,0,0.85) 0%, transparent 50%, transparent 100%)" }}
      />
      <div className="relative z-10 flex flex-col items-center justify-center gap-3 px-4 text-center">
        <div className="rounded-full bg-white/10 p-3">
          <Lock className="h-6 w-6 text-white/90" aria-hidden />
        </div>
        <p className="text-sm font-semibold text-white drop-shadow-sm">{title}</p>
        <p className="text-xs text-white/70 max-w-[220px]">{subtext}</p>
        <p className="text-[11px] text-white/50 mt-0.5">Included in Premium Intelligence</p>
      </div>
    </div>
  )
}
