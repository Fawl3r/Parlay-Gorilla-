"use client"

import Link from "next/link"
import { Coins, Sparkles, CalendarDays, Target, FileText } from "lucide-react"

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
    inscriptionCostUsd,
    premiumInscriptionsLimit,
    premiumInscriptionsUsed,
    premiumInscriptionsRemaining,
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

  const inscriptionsLimitLabel = premiumInscriptionsLimit < 0 ? "∞" : String(premiumInscriptionsLimit)
  const inscriptionsRemainingLabel =
    premiumInscriptionsLimit < 0 ? "∞" : String(Math.max(0, premiumInscriptionsRemaining))

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
          value={String(creditsRemaining)}
        />
        {isPremium ? (
          <>
            <Chip
              compact={compact}
              icon={<Sparkles className={cn("h-4 w-4", compact && "h-4 w-4")} />}
              label="Gorilla Parlays (this period)"
              value={`${aiRemainingLabel}/${aiLimitLabel} left`}
            />
            <Chip
              compact={compact}
              icon={<Target className={cn("h-4 w-4", compact && "h-4 w-4")} />}
              label="Custom AI (this period)"
              value={`${customRemainingLabel}/${customLimitLabel} left`}
            />
            <Chip
              compact={compact}
              icon={<FileText className={cn("h-4 w-4", compact && "h-4 w-4")} />}
              label="Inscription Balance"
              value={`${inscriptionsRemainingLabel}/${inscriptionsLimitLabel} left`}
            />
          </>
        ) : (
          <>
            <Chip
              compact={compact}
              icon={<Sparkles className={cn("h-4 w-4", compact && "h-4 w-4")} />}
              label="Free (lifetime)"
              value={`${freeRemaining} left`}
            />
            <Chip
              compact={compact}
              icon={<CalendarDays className={cn("h-4 w-4", compact && "h-4 w-4")} />}
              label="Today"
              value={`${todayRemainingLabel}/${todayLimitLabel} left`}
            />
          </>
        )}
      </div>

      {isPremium ? (
        <div className={cn("hidden md:block text-xs text-gray-200/60", compact && "hidden")}>
          On-chain verification is optional
        </div>
      ) : null}

      {creditsRemaining === 0 ? (
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


