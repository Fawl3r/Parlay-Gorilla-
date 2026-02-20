"use client"

import { cn } from "@/lib/utils"
import { useSubscription } from "@/lib/subscription-context"
import {
  PREMIUM_AI_PARLAYS_PER_PERIOD,
  PREMIUM_AI_PARLAYS_PERIOD_DAYS,
  PREMIUM_CUSTOM_PARLAYS_PER_PERIOD,
  PREMIUM_CUSTOM_PARLAYS_PERIOD_DAYS,
} from "@/lib/pricingConfig"

export function MonthlyAllowanceSection({ className }: { className?: string }) {
  const {
    isPremium,
    aiParlaysLimit,
    customAiParlaysLimit,
  } = useSubscription()

  // Show actual limits: premium standard is 100/25 per 30 days; backend may return -1 for some plans
  const aiLimit =
    aiParlaysLimit >= 0
      ? aiParlaysLimit
      : isPremium
        ? PREMIUM_AI_PARLAYS_PER_PERIOD
        : 5
  const customLimit =
    customAiParlaysLimit >= 0
      ? customAiParlaysLimit
      : isPremium
        ? PREMIUM_CUSTOM_PARLAYS_PER_PERIOD
        : 0

  const aiLabel = String(aiLimit)
  const customLabel = customLimit > 0 ? String(customLimit) : "—"
  const aiPeriod = isPremium
    ? `per ${PREMIUM_AI_PARLAYS_PERIOD_DAYS}-day period`
    : "per week (rolling)"
  const customPeriod =
    customLimit > 0
      ? `per ${PREMIUM_CUSTOM_PARLAYS_PERIOD_DAYS}-day period`
      : ""

  return (
    <section className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur p-6", className)}>
      <div className="mb-4">
        <h2 className="text-xl font-bold text-white">Usage Allowances</h2>
        <p className="text-sm text-gray-200 mt-1">
          Rolling windows; limits reset automatically. Credits can be purchased anytime.
        </p>
      </div>

      <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5">
        <div className="text-sm font-black text-white mb-3">Included</div>
        <ul className="space-y-2 text-sm text-gray-100/95">
          <li>
            <span className="font-semibold text-white">{aiLabel}</span> Gorilla Parlays (AI) <span className="text-gray-200">{aiPeriod}</span>
          </li>
          <li>
            <span className="font-semibold text-white">{customLabel}</span> Gorilla Parlay Builder builds {customPeriod && <span className="text-gray-200">{customPeriod}</span>}
            {isPremium && customLimit > 0 && " (verified)"}
          </li>
          <li>Credits can be purchased anytime for extra usage</li>
        </ul>
      </div>
    </section>
  )
}

export default MonthlyAllowanceSection


