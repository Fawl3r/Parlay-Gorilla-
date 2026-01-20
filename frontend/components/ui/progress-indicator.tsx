"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

export interface ProgressIndicatorProps {
  value?: number
  max?: number
  showLabel?: boolean
  variant?: "default" | "success" | "warning" | "error"
  className?: string
}

export function ProgressIndicator({
  value = 0,
  max = 100,
  showLabel = false,
  variant = "default",
  className,
}: ProgressIndicatorProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100)

  const variantColors = {
    default: "bg-emerald-500",
    success: "bg-emerald-500",
    warning: "bg-amber-500",
    error: "bg-red-500",
  }

  return (
    <div className={cn("w-full", className)}>
      {showLabel && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-white/70">Progress</span>
          <span className="text-sm font-medium text-white">{Math.round(percentage)}%</span>
        </div>
      )}
      <div className="h-2 w-full rounded-full bg-white/10 overflow-hidden">
        <motion.div
          className={cn("h-full rounded-full", variantColors[variant])}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>
    </div>
  )
}
