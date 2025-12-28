"use client"

import { useMemo } from "react"
import { cn } from "@/lib/utils"

export type PricingTabId = "subscriptions" | "credits"

export function PricingTabs({
  value,
  onChange,
}: {
  value: PricingTabId
  onChange: (tab: PricingTabId) => void
}) {
  const tabs = useMemo(
    () => [
      { id: "subscriptions" as const, label: "Subscriptions" },
      { id: "credits" as const, label: "Credit Packs" },
    ],
    []
  )

  return (
    <div
      className="mt-6 flex flex-nowrap items-center gap-1 overflow-x-auto scrollbar-hide rounded-2xl border border-white/10 bg-black/25 backdrop-blur p-1"
      role="tablist"
      aria-label="Pricing sections"
      data-testid="pricing-tabs"
    >
      {tabs.map((t) => {
        const active = value === t.id
        return (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(t.id)}
            className={cn(
              "shrink-0 inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-bold transition-colors",
              active ? "bg-emerald-500 text-black" : "text-gray-200 hover:bg-white/10"
            )}
            data-testid={`pricing-tab-${t.id}`}
          >
            {t.label}
          </button>
        )
      })}
    </div>
  )
}


