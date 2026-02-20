"use client"

import { motion } from "framer-motion"
import { Coins, Crown, Gift, Wand2 } from "lucide-react"
import { cn } from "@/lib/utils"
import type { AccessStatus } from "./types"

interface UsageVisualizationProps {
  accessStatus: AccessStatus | null
  className?: string
}

function CircularGauge({
  value,
  max,
  label,
  sublabel,
  icon: Icon,
  color = "emerald",
}: {
  value: number
  max: number
  label: string
  sublabel: string
  icon: React.ElementType
  color?: "emerald" | "amber" | "cyan" | "purple"
}) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0
  const stroke = color === "emerald" ? "#00FF5E" : color === "amber" ? "#f59e0b" : color === "cyan" ? "#22d3ee" : "#a855f7"
  const circumference = 2 * Math.PI * 36
  const offset = circumference - (pct / 100) * circumference

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-24 h-24">
        <svg className="w-24 h-24 -rotate-90" viewBox="0 0 96 96">
          <circle
            cx="48"
            cy="48"
            r="36"
            fill="none"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth="8"
          />
          <motion.circle
            cx="48"
            cy="48"
            r="36"
            fill="none"
            stroke={stroke}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <Icon className={cn("h-8 w-8", color === "emerald" && "text-[#00FF5E]", color === "amber" && "text-amber-400", color === "cyan" && "text-cyan-400", color === "purple" && "text-purple-400")} />
        </div>
      </div>
      <p className="mt-2 text-xl font-black text-white">{value}</p>
      <p className="text-xs uppercase tracking-wide text-white/70">{label}</p>
      <p className="text-xs text-white/40 mt-0.5">{sublabel}</p>
    </div>
  )
}

function BarMetric({
  label,
  value,
  max,
  color = "emerald",
}: {
  label: string
  value: number
  max: number
  color?: "emerald" | "amber"
}) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-white/88">{label}</span>
        <span className="text-white font-semibold">{value} / {max}</span>
      </div>
      <div className="h-2 rounded-full bg-white/10 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className={cn(
            "h-full rounded-full",
            color === "emerald" && "bg-gradient-to-r from-[#00FF5E] to-emerald-400",
            color === "amber" && "bg-gradient-to-r from-amber-500 to-amber-400"
          )}
        />
      </div>
    </div>
  )
}

export function UsageVisualization({ accessStatus, className }: UsageVisualizationProps) {
  if (!accessStatus) return null

  const { free, subscription, custom_builder, credits } = accessStatus
  const sub = subscription.active ? subscription : null

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1, duration: 0.3 }}
      className={cn(
        "rounded-2xl border border-white/10 bg-black/20 backdrop-blur p-6",
        className
      )}
    >
      <p className="text-xs uppercase tracking-widest text-white/70 mb-4">
        Usage Visualization
      </p>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
        <CircularGauge
          value={free.remaining}
          max={free.total}
          label="Free parlays"
          sublabel="Lifetime remaining"
          icon={Gift}
          color="purple"
        />
        <CircularGauge
          value={sub ? sub.remaining_today : 0}
          max={sub ? sub.daily_limit : 1}
          label="Subscription"
          sublabel={sub?.is_lifetime ? "Lifetime" : "This period"}
          icon={Crown}
          color="emerald"
        />
        <CircularGauge
          value={custom_builder?.remaining ?? 0}
          max={custom_builder?.limit ?? 1}
          label="Builder"
          sublabel="Included this period"
          icon={Wand2}
          color="cyan"
        />
        <CircularGauge
          value={credits.balance}
          max={Math.max(credits.balance, 50)}
          label="Credits"
          sublabel="Pay-per-use"
          icon={Coins}
          color="amber"
        />
      </div>
      <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 space-y-4">
        <BarMetric
          label="AI parlays remaining"
          value={sub ? sub.remaining_today : free.remaining}
          max={sub ? sub.daily_limit : free.total}
          color="emerald"
        />
        <BarMetric
          label="Credits balance"
          value={credits.balance}
          max={Math.max(100, credits.balance + 20)}
          color="amber"
        />
      </div>
    </motion.section>
  )
}
