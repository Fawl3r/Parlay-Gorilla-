"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

interface ConfidenceMeterProps {
  score: number
  size?: number
  strokeWidth?: number
  label?: string
  className?: string
  showValue?: boolean
}

const getColor = (score: number): string => {
  if (score >= 80) return "hsl(142 76% 36%)" // Green
  if (score >= 60) return "hsl(48 96% 53%)" // Yellow
  if (score >= 40) return "hsl(25 95% 53%)" // Orange
  return "hsl(0 84% 60%)" // Red
}

export function ConfidenceMeter({
  score,
  size = 120,
  strokeWidth = 10,
  label = "Confidence",
  className,
  showValue = true,
}: ConfidenceMeterProps) {
  const normalizedScore = Math.min(100, Math.max(0, score))
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (normalizedScore / 100) * circumference
  const color = getColor(normalizedScore)

  return (
    <div className={cn("flex flex-col items-center text-center", className)}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          {/* Background circle */}
          <circle
            stroke="hsl(215 28% 25%)"
            fill="transparent"
            strokeWidth={strokeWidth}
            r={radius}
            cx={size / 2}
            cy={size / 2}
            strokeLinecap="round"
          />
          {/* Progress circle with neon glow */}
          <motion.circle
            stroke={color}
            fill="transparent"
            strokeWidth={strokeWidth}
            r={radius}
            cx={size / 2}
            cy={size / 2}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1, ease: "easeOut" }}
            style={{
              filter: `drop-shadow(0 0 10px ${color}) drop-shadow(0 0 20px ${color}80)`,
            }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {showValue && (
            <>
              <span className="text-xs uppercase tracking-wide text-muted-foreground">
                {label}
              </span>
              <motion.span
                className="text-2xl font-bold"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ duration: 0.5, delay: 0.3 }}
                style={{ color }}
              >
                {normalizedScore.toFixed(0)}%
              </motion.span>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

