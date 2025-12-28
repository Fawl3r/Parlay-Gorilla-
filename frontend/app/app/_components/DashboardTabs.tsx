"use client"

import { motion } from "framer-motion"
import type { LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

export type TabType = "games" | "custom-builder" | "ai-builder" | "analytics"

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
    <>
      {/* Desktop / Tablet tab row */}
      <section className="hidden sm:block border-b border-white/10 bg-black/30 backdrop-blur-md">
        <div className="container mx-auto px-2 sm:px-4">
          <div className="flex gap-2 overflow-x-auto scrollbar-hide py-2">
            {tabs.map((tab) => {
              const Icon = tab.icon
              const isActive = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => onChange(tab.id)}
                  className={cn(
                    "relative flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all whitespace-nowrap",
                    isActive ? "text-black bg-emerald-500" : "text-gray-300 bg-white/5 hover:bg-white/10"
                  )}
                >
                  <span className="relative z-10 flex items-center gap-2">
                    <Icon className="h-4 w-4" />
                    <span>{tab.label}</span>
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

      {/* Mobile bottom nav */}
      <nav
        className="sm:hidden fixed bottom-0 left-0 right-0 z-50 border-t border-white/10 bg-[#0A0F0A]/95 backdrop-blur-xl"
        role="navigation"
        aria-label="Dashboard navigation"
        data-testid="dashboard-bottom-nav"
      >
        <div className="mx-auto max-w-6xl px-2 pt-2 pb-[calc(env(safe-area-inset-bottom,0px)+10px)]">
          <div className="grid grid-cols-4 gap-1">
            {tabs.map((tab) => {
              const Icon = tab.icon
              const isActive = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => onChange(tab.id)}
                  className={cn(
                    "flex flex-col items-center justify-center gap-1 rounded-xl px-2 py-2.5 transition-colors",
                    isActive ? "bg-emerald-500 text-black" : "text-gray-200 hover:bg-white/10"
                  )}
                  aria-current={isActive ? "page" : undefined}
                >
                  <Icon className={cn("h-5 w-5", isActive ? "text-black" : "text-emerald-300")} />
                  <span className={cn("text-[11px] font-bold leading-none", isActive ? "text-black" : "text-gray-200")}>
                    {tab.label}
                  </span>
                </button>
              )
            })}
          </div>
        </div>
      </nav>
    </>
  )
}


