"use client"

import { cn } from "@/lib/utils"
import { motion } from "framer-motion"
import { useEffect, useState } from "react"

interface ConfidenceRingProps {
  score: number
  size?: number
  strokeWidth?: number
  label?: string
  className?: string
}

const getRingColor = (score: number) => {
  if (score >= 70) return "#10B981" // emerald
  if (score >= 50) return "#FACC15" // amber
  return "#EF4444" // red
}

export function ConfidenceRing({
  score,
  size = 120,
  strokeWidth = 10,
  label = "Confidence",
  className,
}: ConfidenceRingProps) {
  const normalizedScore = Math.min(100, Math.max(0, score))
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const color = getRingColor(normalizedScore)
  const [displayScore, setDisplayScore] = useState(0)

  // Animate score number
  useEffect(() => {
    const duration = 1000 // 1 second animation
    const steps = 60
    const increment = normalizedScore / steps
    let current = 0
    let step = 0

    const timer = setInterval(() => {
      step++
      current = Math.min(normalizedScore, increment * step)
      setDisplayScore(current)
      if (step >= steps) {
        clearInterval(timer)
        setDisplayScore(normalizedScore)
      }
    }, duration / steps)

    return () => clearInterval(timer)
  }, [normalizedScore])

  const offset = circumference - (displayScore / 100) * circumference

  return (
    <div className={cn("flex flex-col items-center text-center", className)}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size}>
          <circle
            className="stroke-gray-300 dark:stroke-gray-600"
            fill="transparent"
            strokeWidth={strokeWidth}
            r={radius}
            cx={size / 2}
            cy={size / 2}
            strokeLinecap="round"
          />
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
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1, ease: "easeOut" }}
          />
        </svg>
        <motion.div
          className="absolute inset-0 flex flex-col items-center justify-center gap-0.5"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          style={{
            padding: `${strokeWidth * 0.5}px`, // Add padding to keep text inside circle
          }}
        >
          <motion.span
            className="font-bold text-gray-900 dark:text-foreground leading-none"
            style={{
              fontSize: `${size * 0.25}px`, // Responsive font size based on circle size
            }}
            key={displayScore}
            initial={{ scale: 1.2 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.2 }}
          >
            {displayScore.toFixed(1)}%
          </motion.span>
          <span 
            className="uppercase tracking-wide text-gray-700 dark:text-muted-foreground font-medium leading-tight"
            style={{
              fontSize: `${size * 0.08}px`, // Responsive label size
            }}
          >
            {label}
          </span>
        </motion.div>
      </div>
    </div>
  )
}

