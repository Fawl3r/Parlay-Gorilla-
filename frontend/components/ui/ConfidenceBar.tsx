"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

export interface ConfidenceBarProps {
  /** 0–100 */
  percent: number
  className?: string
  /** Optional label (e.g. "Confidence") */
  label?: string
}

/**
 * Horizontal confidence bar: track bg-white/10, fill gradient red → yellow → green by %.
 * Animate width with transition-all duration-300. No framer-motion.
 */
export function ConfidenceBar({ percent, className, label }: ConfidenceBarProps) {
  const value = Math.min(100, Math.max(0, percent))
  return (
    <div className={cn("w-full", className)}>
      {label && <span className="text-xs text-muted-foreground mb-1 block">{label}</span>}
      <div className="h-2 rounded-full bg-white/10 overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-red-500 via-yellow-400 to-green-500 transition-all duration-300"
          style={{ width: `${value}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
      <span className="text-xs text-muted-foreground mt-0.5 inline-block">{value.toFixed(0)}%</span>
    </div>
  )
}
