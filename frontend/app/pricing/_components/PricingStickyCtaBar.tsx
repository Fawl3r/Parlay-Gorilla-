"use client"

import { useRouter } from "next/navigation"
import { Coins, Crown } from "lucide-react"

import { cn } from "@/lib/utils"

export function PricingStickyCtaBar({
  onUpgrade,
  onBuyCredits,
  className,
}: {
  onUpgrade: () => void
  onBuyCredits: () => void
  className?: string
}) {
  // router import kept for future-proofing; bar actions are passed in for tab switching.
  useRouter()

  return (
    <div
      className={cn(
        "sm:hidden fixed bottom-0 left-0 right-0 z-50",
        "border-t border-white/10 bg-[#0A0F0A]/95 backdrop-blur-xl",
        "px-4 py-3 pb-[calc(env(safe-area-inset-bottom,0px)+12px)]",
        className
      )}
      role="region"
      aria-label="Pricing actions"
      data-testid="pricing-sticky-cta"
    >
      <div className="mx-auto max-w-6xl flex gap-2">
        <button
          type="button"
          onClick={onUpgrade}
          className="flex-1 inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-500 text-black font-black py-3"
        >
          <Crown className="h-4 w-4" />
          Upgrade
        </button>
        <button
          type="button"
          onClick={onBuyCredits}
          className="flex-1 inline-flex items-center justify-center gap-2 rounded-xl bg-amber-500 text-black font-black py-3"
        >
          <Coins className="h-4 w-4" />
          Buy Credits
        </button>
      </div>
    </div>
  )
}


