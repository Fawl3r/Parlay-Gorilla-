"use client"

import { motion } from "framer-motion"
import type { LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

export type TabType = "games" | "custom-builder" | "ai-builder" | "analytics" | "feed" | "odds-heatmap" | "upset-finder"

type TabDef = {
  id: TabType
  label: string
  icon: LucideIcon
}

export function DashboardTabs({
  tabs,
  activeTab,
  onChange,
}: {
  tabs: TabDef[]
  activeTab: TabType
  onChange: (tab: TabType) => void
}) {
  return (
    <section className="border-b border-white/10 bg-black/30 backdrop-blur-md">
      <div className="w-full sm:container sm:mx-auto px-2 sm:px-3 md:px-4">
        <div className="flex gap-1.5 sm:gap-2 overflow-x-auto scrollbar-hide py-2 scroll-smooth touch-pan-x snap-x snap-mandatory">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => onChange(tab.id)}
                className={cn(
                  "relative flex items-center gap-1.5 sm:gap-2 rounded-lg font-semibold transition-all whitespace-nowrap",
                  "px-2.5 py-2 text-xs sm:px-3 sm:py-2 sm:text-[13px] md:px-4 md:text-sm",
                  "min-h-[44px] shrink-0 snap-start",
                  "active:scale-95",
                  isActive ? "text-black bg-emerald-500" : "text-gray-300 bg-white/5 hover:bg-white/10 active:bg-white/15"
                )}
                aria-current={isActive ? "page" : undefined}
              >
                <span className="relative z-10 flex items-center gap-1.5 sm:gap-2">
                  <Icon className="h-3.5 w-3.5 sm:h-4 sm:w-4 shrink-0" />
                  <span className="max-w-[14ch] sm:max-w-[16ch] truncate">{tab.label}</span>
                </span>
                {isActive && (
                  <motion.div
                    layoutId="dashboard-tab-indicator"
                    className="absolute inset-0 rounded-lg ring-2 ring-emerald-300/40 pointer-events-none"
                    transition={{ type: "spring", stiffness: 500, damping: 35 }}
                  />
                )}
              </button>
            )
          })}
        </div>
      </div>
    </section>
  )
}


