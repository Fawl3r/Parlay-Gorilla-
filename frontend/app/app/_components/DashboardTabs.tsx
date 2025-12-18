"use client"

import { motion } from "framer-motion"
import type { LucideIcon } from "lucide-react"

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
    <section className="border-b border-white/10 bg-black/30 backdrop-blur-md">
      <div className="container mx-auto px-2 sm:px-4">
        <div className="flex gap-2 overflow-x-auto scrollbar-hide py-2">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => onChange(tab.id)}
                className={`relative flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all whitespace-nowrap ${
                  isActive ? "text-black bg-emerald-500" : "text-gray-300 bg-white/5 hover:bg-white/10"
                }`}
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
  )
}


