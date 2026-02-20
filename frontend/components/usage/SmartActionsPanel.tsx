"use client"

import { motion } from "framer-motion"
import Link from "next/link"
import { ChevronRight, Sparkles, BarChart3, TrendingUp } from "lucide-react"

import { cn } from "@/lib/utils"

const ACTIONS = [
  {
    href: "/app",
    label: "Generate Optimal Parlay",
    icon: Sparkles,
    description: "Use Gorilla AI to build a parlay",
  },
  {
    href: "/analysis",
    label: "Analyze My Strategy",
    icon: BarChart3,
    description: "Review past parlays and outcomes",
  },
  {
    href: "/usage",
    label: "Improve My Score",
    icon: TrendingUp,
    description: "You're already here — keep building",
  },
] as const

export function SmartActionsPanel({ className }: { className?: string }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.2 }}
      className={cn("space-y-4", className)}
    >
      <h2 className="text-lg font-black text-white">Smart Actions</h2>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {ACTIONS.map((action, i) => {
          const Icon = action.icon
          return (
            <motion.div
              key={action.href}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25, delay: 0.25 + i * 0.05 }}
            >
              <Link
                href={action.href}
                className={cn(
                  "block rounded-xl border border-white/10 backdrop-blur-xl p-5",
                  "bg-black/45 hover:bg-black/55 hover:border-emerald-500/20",
                  "shadow-[0_4px_20px_-8px_rgba(0,0,0,0.5)]",
                  "hover:shadow-[0_4px_24px_-8px_rgba(0,0,0,0.6)]",
                  "transition-all duration-200 group"
                )}
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center group-hover:bg-emerald-500/30 transition-colors">
                    <Icon className="w-5 h-5 text-emerald-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-bold text-white group-hover:text-emerald-200 transition-colors">
                      {action.label}
                    </span>
                    <p className="text-xs text-gray-200/92 mt-0.5">{action.description}</p>
                    <span className="inline-flex items-center gap-1 text-xs text-emerald-400 mt-2">
                      Go <ChevronRight className="w-4 h-4" />
                    </span>
                  </div>
                </div>
              </Link>
            </motion.div>
          )
        })}
      </div>
    </motion.section>
  )
}
