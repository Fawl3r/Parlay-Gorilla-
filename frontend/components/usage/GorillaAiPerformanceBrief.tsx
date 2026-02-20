"use client"

import { motion } from "framer-motion"
import { Sparkles, TrendingUp } from "lucide-react"

import { cn } from "@/lib/utils"

export type GorillaAiPerformanceBriefProps = {
  insight: string
  statusLabel?: string
  trend?: "up" | "stable" | "attention"
  className?: string
}

export function GorillaAiPerformanceBrief({
  insight,
  statusLabel,
  trend = "stable",
  className,
}: GorillaAiPerformanceBriefProps) {
  const safe = String(insight || "").trim()
  if (!safe) return null

  const trendCopy =
    trend === "up" ? "Trending up" : trend === "attention" ? "Review usage" : "On track"

  return (
    <motion.section
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className={cn(
        "relative w-full rounded-xl overflow-hidden",
        "border border-white/10",
        "bg-gradient-to-br from-emerald-950/40 via-black/60 to-black/70",
        "backdrop-blur-xl",
        "shadow-[0_0_0_1px_rgba(16,185,129,0.08),0_4px_24px_-4px_rgba(0,0,0,0.4)]",
        "before:absolute before:inset-0 before:rounded-xl before:pointer-events-none",
        "before:bg-gradient-to-r before:from-emerald-500/5 before:via-transparent before:to-cyan-500/5",
        className
      )}
      aria-label="Gorilla AI Performance Brief"
    >
      <div className="relative p-6 md:p-8">
        <div className="flex flex-col md:flex-row md:items-start gap-6">
          {/* Icon / Avatar */}
          <div
            className={cn(
              "flex-shrink-0 w-14 h-14 rounded-xl flex items-center justify-center",
              "bg-emerald-500/20 border border-emerald-400/30",
              "ring-2 ring-emerald-400/10"
            )}
          >
            <Sparkles className="w-7 h-7 text-emerald-400" aria-hidden />
          </div>

          <div className="flex-1 min-w-0 space-y-4">
            <div>
              <h2 className="text-lg font-black text-white uppercase tracking-wide">
                Gorilla AI Performance Brief
              </h2>
              <p className="mt-1 text-sm text-gray-100/98 max-w-2xl">{safe}</p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              {statusLabel && (
                <span className="text-xs uppercase tracking-wider text-gray-200/90">
                  {statusLabel}
                </span>
              )}
              <span className="flex items-center gap-1.5 text-xs text-emerald-300/90">
                <TrendingUp className="w-4 h-4" aria-hidden />
                {trendCopy}
              </span>
            </div>
          </div>
        </div>
      </div>
    </motion.section>
  )
}
