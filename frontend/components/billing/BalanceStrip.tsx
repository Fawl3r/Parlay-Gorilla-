"use client"

import Link from "next/link"
import { Coins, Sparkles, CalendarDays, Target } from "lucide-react"

import { useAuth } from "@/lib/auth-context"
import { useSubscription } from "@/lib/subscription-context"
import { cn } from "@/lib/utils"

type Props = {
  compact?: boolean
  className?: string
}

function Chip({
  icon,
  label,
  value,
  compact,
}: {
  icon: React.ReactNode
  label: string
  value: string
  compact: boolean
}) {
  return (
    <div
      className={cn(
        "shrink-0 rounded-xl border border-white/10 bg-black/25 backdrop-blur-sm",
        compact ? "px-2 py-1.5 sm:px-3 sm:py-2" : "px-3 py-2 sm:px-4 sm:py-3"
      )}
    >
      <div className="flex items-center gap-1.5 sm:gap-2">
        <div className="text-emerald-300 shrink-0">{icon}</div>
        <div className="min-w-0">
          <div className={cn(
            "uppercase tracking-wide text-gray-400",
            compact ? "text-[9px] sm:text-[10px]" : "text-[10px] sm:text-[11px]"
          )}>
            {label}
          </div>
          <div className={cn(
            "font-bold text-white",
            compact ? "text-xs sm:text-sm" : "text-sm sm:text-base"
          )}>{value}</div>
        </div>
      </div>
    </div>
  )
}

function Skeleton({ compact }: { compact: boolean }) {
  return (
    <div
      className={cn(
        "flex gap-2",
        "overflow-x-auto scrollbar-hide snap-x snap-mandatory",
        "pb-1"
      )}
      aria-label="Loading balances"
    >
      {Array.from({ length: 3 }).map((_, idx) => (
        <div
          key={idx}
          className={cn(
            "shrink-0 snap-start rounded-xl border border-white/10 bg-white/5",
            compact ? "h-[44px] w-[160px]" : "h-[56px] w-[200px]",
            "animate-pulse"
          )}
        />
      ))}
    </div>
  )
}

export function BalanceStrip({ compact = false, className }: Props) {
  const { user } = useAuth()
  const {
    loading,
    isPremium,
    creditsRemaining,
    freeParlaysUsed,
    freeParlaysTotal,
    freeRemaining,
    todayRemaining,
    todayLimit,
    aiParlaysRemaining,
    aiParlaysLimit,
    customAiParlaysRemaining,
    customAiParlaysLimit,
  } = useSubscription()

  if (!user) return null
  if (loading) return <Skeleton compact={compact} />

  const aiLimitLabel = aiParlaysLimit < 0 ? "∞" : String(aiParlaysLimit)
  const aiRemainingLabel = aiParlaysLimit < 0 ? "∞" : String(Math.max(0, aiParlaysRemaining))

  const todayLimitLabel = todayLimit < 0 ? "∞" : String(todayLimit)
  const todayRemainingLabel = todayLimit < 0 ? "∞" : String(Math.max(0, todayRemaining))

  const customLimitLabel = customAiParlaysLimit < 0 ? "∞" : String(customAiParlaysLimit)
  const customRemainingLabel =
    customAiParlaysLimit < 0 ? "∞" : String(Math.max(0, customAiParlaysRemaining))

  return (
    <div className={cn("flex items-center gap-2 sm:gap-3", className)}>
      <div
        className={cn(
          "min-w-0 flex-1 flex gap-1.5 sm:gap-2",
          "overflow-x-auto scrollbar-hide snap-x snap-mandatory",
          "pb-1",
          "scroll-smooth touch-pan-x"
        )}
        aria-label="Balances"
      >
        <Chip
          compact={compact}
          icon={<Coins className={cn("h-3.5 w-3.5 sm:h-4 sm:w-4", compact && "h-3.5 w-3.5 sm:h-4 sm:w-4")} />}
          label="Credits"
          value={String(creditsRemaining)}
        />
        {isPremium ? (
          <>
            <Chip
              compact={compact}
              icon={<Sparkles className={cn("h-3.5 w-3.5 sm:h-4 sm:w-4", compact && "h-3.5 w-3.5 sm:h-4 sm:w-4")} />}
              label="AI Picks (this period)"
              value={`${aiRemainingLabel}/${aiLimitLabel} left`}
            />
            <Chip
              compact={compact}
              icon={<Target className={cn("h-3.5 w-3.5 sm:h-4 sm:w-4", compact && "h-3.5 w-3.5 sm:h-4 sm:w-4")} />}
              label="Gorilla Builder Parlays (this period)"
              value={`${customRemainingLabel}/${customLimitLabel} left`}
            />
          </>
        ) : (
          <>
            <Chip
              compact={compact}
              icon={<Sparkles className={cn("h-3.5 w-3.5 sm:h-4 sm:w-4", compact && "h-3.5 w-3.5 sm:h-4 sm:w-4")} />}
              label="Free (lifetime)"
              value={`${freeRemaining} left`}
            />
            <Chip
              compact={compact}
              icon={<CalendarDays className={cn("h-3.5 w-3.5 sm:h-4 sm:w-4", compact && "h-3.5 w-3.5 sm:h-4 sm:w-4")} />}
              label="This Week"
              value={`${todayRemainingLabel}/${todayLimitLabel} left`}
            />
          </>
        )}
      </div>


      {creditsRemaining === 0 ? (
        <Link
          href="/pricing#credits"
          className={cn(
            "shrink-0 inline-flex items-center justify-center rounded-xl font-bold transition-colors",
            "bg-amber-500 text-black hover:bg-amber-400 active:bg-amber-600",
            "min-h-[44px] min-w-[44px]",
            compact ? "px-2.5 py-1.5 text-xs sm:px-3 sm:py-2" : "px-3 py-2 text-xs sm:px-4 sm:py-2.5 sm:text-sm"
          )}
          aria-label="Buy credits"
        >
          Buy Credits
        </Link>
      ) : null}
    </div>
  )
}

export default BalanceStrip


