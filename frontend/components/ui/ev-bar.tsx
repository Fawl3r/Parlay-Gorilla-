"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

interface EVBarProps {
  value: number
  max?: number
  label?: string
  showValue?: boolean
  className?: string
}

const getEVColor = (value: number): string => {
  if (value >= 0.15) return "hsl(142 76% 36%)" // Green - High positive EV
  if (value >= 0.05) return "hsl(48 96% 53%)" // Yellow - Moderate positive EV
  if (value >= -0.05) return "hsl(199 89% 48%)" // Sky - Neutral
  if (value >= -0.15) return "hsl(25 95% 53%)" // Orange - Negative EV
  return "hsl(0 84% 60%)" // Red - Very negative EV
}

const getEVLabel = (value: number): string => {
  if (value >= 0.15) return "High Value"
  if (value >= 0.05) return "Positive EV"
  if (value >= -0.05) return "Neutral"
  if (value >= -0.15) return "Negative EV"
  return "Poor Value"
}

export function EVBar({
  value,
  max = 0.3,
  label = "Expected Value",
  showValue = true,
  className,
}: EVBarProps) {
  const normalizedValue = Math.max(-max, Math.min(max, value))
  const percentage = ((normalizedValue + max) / (max * 2)) * 100
  const color = getEVColor(value)
  const evLabel = getEVLabel(value)

  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">{label}</span>
        {showValue && (
          <div className="flex items-center gap-2">
            <span
              className="text-xs font-semibold"
              style={{ color }}
            >
              {value > 0 ? "+" : ""}
              {(value * 100).toFixed(1)}%
            </span>
            <span
              className="rounded-full px-2 py-0.5 text-xs"
              style={{
                backgroundColor: `${color}20`,
                color,
                border: `1px solid ${color}50`,
              }}
            >
              {evLabel}
            </span>
          </div>
        )}
      </div>

      <div className="relative h-3 overflow-hidden rounded-full bg-muted">
        {/* Center marker */}
        <div className="absolute left-1/2 top-0 h-full w-px -translate-x-1/2 bg-foreground/20" />
        
        {/* Value bar */}
        <motion.div
          className="h-full rounded-full"
          style={{
            width: `${percentage}%`,
            backgroundColor: color,
            marginLeft: value < 0 ? "50%" : "0%",
            marginRight: value >= 0 ? "50%" : "0%",
            boxShadow: `0 0 10px ${color}, 0 0 20px ${color}50`,
          }}
          initial={{ width: "0%" }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </div>

      <div className="flex justify-between text-xs text-muted-foreground">
        <span>-{(max * 100).toFixed(0)}%</span>
        <span>0%</span>
        <span>+{(max * 100).toFixed(0)}%</span>
      </div>
    </div>
  )
}

