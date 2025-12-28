"use client"

import Link from "next/link"
import { Coins, Sparkles, CalendarDays } from "lucide-react"

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
        compact ? "px-3 py-2" : "px-4 py-3"
      )}
    >
      <div className="flex items-center gap-2">
        <div className="text-emerald-300">{icon}</div>
        <div className="min-w-0">
          <div className={cn("text-[11px] uppercase tracking-wide text-gray-400", compact && "text-[10px]")}>
            {label}
          </div>
          <div className={cn("text-sm font-bold text-white", compact ? "text-sm" : "text-base")}>{value}</div>
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
    creditBalance,
    freeParlaysUsed,
    freeParlaysTotal,
    freeParlaysRemaining,
    dailyAiRemaining,
    dailyAiLimit,
  } = useSubscription()

  if (!user) return null
  if (loading) return <Skeleton compact={compact} />

  const todayLimitLabel = dailyAiLimit < 0 ? "∞" : String(dailyAiLimit)
  const todayRemainingLabel = dailyAiLimit < 0 ? "∞" : String(Math.max(0, dailyAiRemaining))

  return (
    <div className={cn("flex items-center justify-between gap-3", className)}>
      <div
        className={cn(
          "flex gap-2",
          "overflow-x-auto scrollbar-hide snap-x snap-mandatory",
          "pb-1"
        )}
        aria-label="Balances"
      >
        <Chip
          compact={compact}
          icon={<Coins className={cn("h-4 w-4", compact && "h-4 w-4")} />}
          label="Credits"
          value={String(creditBalance)}
        />
        <Chip
          compact={compact}
          icon={<Sparkles className={cn("h-4 w-4", compact && "h-4 w-4")} />}
          label="Free"
          value={`${freeParlaysUsed}/${freeParlaysTotal} (${freeParlaysRemaining} left)`}
        />
        <Chip
          compact={compact}
          icon={<CalendarDays className={cn("h-4 w-4", compact && "h-4 w-4")} />}
          label="Today"
          value={`${todayRemainingLabel}/${todayLimitLabel} left`}
        />
      </div>

      {creditBalance === 0 ? (
        <Link
          href="/pricing#credits"
          className={cn(
            "shrink-0 inline-flex items-center justify-center rounded-xl font-bold transition-colors",
            "bg-amber-500 text-black hover:bg-amber-400",
            compact ? "px-3 py-2 text-xs" : "px-4 py-2.5 text-sm"
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


