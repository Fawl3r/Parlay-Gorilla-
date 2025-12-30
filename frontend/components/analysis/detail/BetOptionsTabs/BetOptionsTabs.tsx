"use client"

import { useMemo, useState } from "react"

import { cn } from "@/lib/utils"

import { BetOptionCard, type BetOptionCardProps } from "./BetOptionCard"

export type BetTabId = "moneyline" | "spread" | "total" | string

export type BetOptionsTab = {
  id: BetTabId
  label: string
  option: Omit<BetOptionCardProps, "label">
}

export type BetOptionsTabsProps = {
  tabs: BetOptionsTab[]
  initialTabId?: BetTabId
  activeTabId?: BetTabId
  onTabChange?: (tabId: BetTabId) => void
  className?: string
}

export function BetOptionsTabs({ tabs, initialTabId, activeTabId, onTabChange, className }: BetOptionsTabsProps) {
  const safeTabs = useMemo(() => (Array.isArray(tabs) ? tabs.filter((t) => t && t.label) : []), [tabs])

  const initial = useMemo(() => {
    if (!safeTabs.length) return ""
    if (initialTabId) {
      const hit = safeTabs.find((t) => t.id === initialTabId)
      if (hit) return hit.id
    }
    return safeTabs[0].id
  }, [initialTabId, safeTabs])

  const [uncontrolledActiveId, setUncontrolledActiveId] = useState<BetTabId>(initial)
  const activeId = activeTabId ?? uncontrolledActiveId

  const active = useMemo(() => safeTabs.find((t) => t.id === activeId) ?? safeTabs[0], [activeId, safeTabs])

  if (!safeTabs.length) return null

  return (
    <section className={cn("rounded-2xl border border-white/10 bg-black/20 backdrop-blur-sm p-4", className)}>
      <div className="text-sm font-extrabold text-white px-1">Bet Options</div>

      <div className="mt-3">
        <div
          className={cn(
            "flex gap-2 overflow-x-auto scrollbar-hide",
            "pb-1"
          )}
          role="tablist"
          aria-label="Bet options"
        >
          {safeTabs.map((t) => {
            const isActive = t.id === activeId
            return (
              <button
                key={String(t.id)}
                type="button"
                role="tab"
                aria-selected={isActive}
                onClick={() => {
                  onTabChange?.(t.id)
                  if (!activeTabId) setUncontrolledActiveId(t.id)
                }}
                className={cn(
                  "shrink-0 rounded-full border px-4 py-2 text-xs font-extrabold transition-all",
                  isActive
                    ? "border-emerald-500/50 bg-emerald-500/15 text-emerald-200"
                    : "border-white/10 bg-white/5 text-white/70 hover:bg-white/10 hover:text-white"
                )}
              >
                {t.label}
              </button>
            )
          })}
        </div>
      </div>

      {active ? (
        <div className="mt-4">
          <BetOptionCard
            label={active.label}
            lean={active.option.lean}
            confidenceLevel={active.option.confidenceLevel}
            riskLevel={active.option.riskLevel}
            explanation={active.option.explanation}
          />
        </div>
      ) : null}
    </section>
  )
}


