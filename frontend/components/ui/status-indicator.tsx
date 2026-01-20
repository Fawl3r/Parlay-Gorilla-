"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

export type StatusType = "success" | "warning" | "error" | "info" | "neutral"

export interface StatusIndicatorProps {
  type?: StatusType
  pulse?: boolean
  size?: "sm" | "md" | "lg"
  className?: string
}

const statusColors = {
  success: "bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.8)]",
  warning: "bg-amber-500",
  error: "bg-red-500",
  info: "bg-blue-500",
  neutral: "bg-gray-500",
}

const statusSizes = {
  sm: "w-2 h-2",
  md: "w-3 h-3",
  lg: "w-4 h-4",
}

export function StatusIndicator({
  type = "success",
  pulse = true,
  size = "md",
  className,
}: StatusIndicatorProps) {
  return (
    <div className={cn("relative inline-flex items-center justify-center", className)}>
      <motion.div
        className={cn(
          "rounded-full",
          statusColors[type],
          statusSizes[size]
        )}
        animate={
          pulse
            ? {
                scale: [1, 1.2, 1],
                opacity: [1, 0.7, 1],
              }
            : {}
        }
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      {pulse && (
        <motion.div
          className={cn(
            "absolute rounded-full",
            statusColors[type],
            statusSizes[size]
          )}
          animate={{
            scale: [1, 2, 2],
            opacity: [0.6, 0, 0],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeOut",
          }}
        />
      )}
    </div>
  )
}
