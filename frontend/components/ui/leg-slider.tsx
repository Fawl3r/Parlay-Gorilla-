"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

interface LegSliderProps {
  value: number
  onChange: (value: number) => void
  min?: number
  max?: number
  className?: string
}

const getRiskColor = (legs: number): string => {
  if (legs <= 5) return "hsl(142 76% 36%)" // Green
  if (legs <= 10) return "hsl(48 96% 53%)" // Yellow
  if (legs <= 15) return "hsl(25 95% 53%)" // Orange
  return "hsl(0 84% 60%)" // Red
}

const getRiskLabel = (legs: number): string => {
  if (legs <= 5) return "Safe"
  if (legs <= 10) return "Balanced"
  if (legs <= 15) return "Risky"
  return "Degen"
}

export function LegSlider({
  value,
  onChange,
  min = 1,
  max = 20,
  className,
}: LegSliderProps) {
  const riskColor = getRiskColor(value)
  const riskLabel = getRiskLabel(value)

  return (
    <div className={cn("relative space-y-4", className)}>
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">Number of Legs: {value}</label>
        <span
          className="rounded-full px-3 py-1 text-xs font-semibold"
          style={{
            backgroundColor: `${riskColor}20`,
            color: riskColor,
            border: `1px solid ${riskColor}50`,
          }}
        >
          {riskLabel}
        </span>
      </div>

      <div className="relative">
        <input
          type="range"
          min={min}
          max={max}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="h-2 w-full appearance-none rounded-lg bg-muted outline-none"
          style={{
            background: `linear-gradient(to right, ${riskColor} 0%, ${riskColor} ${((value - min) / (max - min)) * 100}%, hsl(215 28% 25%) ${((value - min) / (max - min)) * 100}%, hsl(215 28% 25%) 100%)`,
          }}
        />
        <motion.div
          className="absolute top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 bg-background"
          style={{
            left: `${((value - min) / (max - min)) * 100}%`,
            borderColor: riskColor,
            boxShadow: `0 0 10px ${riskColor}, 0 0 20px ${riskColor}50`,
          }}
          animate={{
            scale: [1, 1.2, 1],
          }}
          transition={{
            duration: 0.3,
            ease: "easeOut",
          }}
        />
      </div>

      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{min}</span>
        <span>{max}</span>
      </div>
    </div>
  )
}

