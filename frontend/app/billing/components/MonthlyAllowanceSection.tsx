"use client"

import { cn } from "@/lib/utils"
import { useSubscription } from "@/lib/subscription-context"

export function MonthlyAllowanceSection({ className }: { className?: string }) {
  const {
    aiParlaysLimit,
    customAiParlaysLimit,
  } = useSubscription()

  const aiLimitLabel = aiParlaysLimit < 0 ? "Unlimited" : String(aiParlaysLimit)
  const customLimitLabel = customAiParlaysLimit < 0 ? "Unlimited" : String(customAiParlaysLimit)

  return (
    <section className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur p-6", className)}>
      <div className="mb-4">
        <h2 className="text-xl font-bold text-white">Monthly Allowance</h2>
        <p className="text-sm text-gray-200/70 mt-1">
          Clear allowances and opt-in add-ons — designed to prevent surprises.
        </p>
      </div>

      <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5">
        <div className="text-sm font-black text-white mb-3">Included Each Month</div>
        <ul className="space-y-2 text-sm text-gray-200/80">
          <li>
            <span className="font-semibold text-white">{aiLimitLabel}</span> AI Parlays
          </li>
          <li>
            <span className="font-semibold text-white">{customLimitLabel}</span> Custom AI Parlays (automatically verified)
          </li>
          <li>Credits can be purchased anytime</li>
        </ul>

        <div className="mt-4 text-sm text-gray-200/80">
          <span className="font-semibold text-white">Nothing is charged automatically.</span> You always choose when to use credits.
        </div>
      </div>
    </section>
  )
}

export default MonthlyAllowanceSection


