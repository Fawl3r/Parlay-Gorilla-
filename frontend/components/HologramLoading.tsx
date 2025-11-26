"use client"

import { motion } from "framer-motion"
import { useState, useEffect } from "react"
import { fadeIn, spin, pulse } from "@/lib/animations"

interface HologramLoadingProps {
  messages?: string[]
  duration?: number
  onComplete?: () => void
  skipable?: boolean
}

const defaultMessages = [
  "Analyzing matchups...",
  "Calculating win probabilities...",
  "Simulating outcomes...",
  "Optimizing parlay...",
]

export function HologramLoading({
  messages = defaultMessages,
  duration = 4000,
  onComplete,
  skipable = true,
}: HologramLoadingProps) {
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0)
  const [isComplete, setIsComplete] = useState(false)

  useEffect(() => {
    if (isComplete) return

    const messageInterval = duration / messages.length
    const interval = setInterval(() => {
      setCurrentMessageIndex((prev) => {
        if (prev >= messages.length - 1) {
          setIsComplete(true)
          if (onComplete) {
            setTimeout(onComplete, 500)
          }
          return prev
        }
        return prev + 1
      })
    }, messageInterval)

    return () => clearInterval(interval)
  }, [messages.length, duration, onComplete, isComplete])

  const handleSkip = () => {
    setIsComplete(true)
    if (onComplete) {
      onComplete()
    }
  }

  return (
    <motion.div
      className="fixed inset-0 z-50 flex items-center justify-center bg-background/95 backdrop-blur-sm"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      {/* Circuit Lines Background */}
      <div className="absolute inset-0 overflow-hidden">
        {[...Array(20)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute h-px bg-gradient-to-r from-transparent via-neon-green to-transparent"
            style={{
              top: `${(i * 100) / 20}%`,
              left: 0,
              width: "100%",
            }}
            animate={{
              opacity: [0.2, 0.8, 0.2],
              x: typeof window !== "undefined" ? [-100, window.innerWidth + 100] : [-100, 2000],
            }}
            transition={{
              duration: 2 + Math.random() * 2,
              repeat: Infinity,
              delay: Math.random() * 2,
              ease: "linear",
            }}
          />
        ))}
      </div>

      <div className="relative z-10 flex flex-col items-center gap-8">
        {/* 3D Rotating Sports Orb */}
        <motion.div
          className="relative h-32 w-32"
          variants={spin}
          animate="animate"
        >
          <motion.div
            className="absolute inset-0 rounded-full border-2"
            style={{
              borderColor: "hsl(150 100% 50%)",
              background: "radial-gradient(circle, rgba(0,255,140,0.2) 0%, transparent 70%)",
              boxShadow: "0 0 40px rgba(0,255,140,0.5), inset 0 0 40px rgba(0,255,140,0.2)",
            }}
            variants={pulse}
            animate="animate"
          />
          <motion.div
            className="absolute inset-0 rounded-full"
            style={{
              background: "conic-gradient(from 0deg, transparent, rgba(0,255,140,0.3), transparent)",
            }}
            animate={{ rotate: 360 }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: "linear",
            }}
          />
          {/* Inner rotating elements */}
          {[...Array(3)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute inset-0 rounded-full border"
              style={{
                borderColor: "rgba(0,255,140,0.3)",
                transform: `rotate(${i * 120}deg)`,
              }}
              animate={{
                rotate: 360 + i * 120,
              }}
              transition={{
                duration: 4 + i,
                repeat: Infinity,
                ease: "linear",
              }}
            />
          ))}
        </motion.div>

        {/* Scanning Effect */}

        {/* Text Animation */}
        <motion.div
          className="text-center"
          variants={fadeIn}
          initial="initial"
          animate="animate"
        >
          <motion.p
            key={currentMessageIndex}
            className="text-xl font-semibold"
            style={{
              color: "hsl(150 100% 50%)",
              textShadow: "0 0 20px hsl(150 100% 50% / 0.5), 0 0 40px hsl(150 100% 50% / 0.3)",
            }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            {messages[currentMessageIndex]}
          </motion.p>
        </motion.div>

        {/* Progress Bar */}
        <div className="h-1 w-64 overflow-hidden rounded-full bg-muted">
          <motion.div
            className="h-full"
            style={{
              background: "linear-gradient(to right, hsl(150 100% 50%), hsl(199 89% 48%))",
            }}
            initial={{ width: "0%" }}
            animate={{ width: isComplete ? "100%" : `${((currentMessageIndex + 1) / messages.length) * 100}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </div>

        {/* Skip Button */}
        {skipable && !isComplete && (
          <motion.button
            onClick={handleSkip}
            className="mt-4 rounded-lg border bg-background/50 px-4 py-2 text-sm text-muted-foreground transition-colors"
            style={{
              borderColor: "rgba(0,255,140,0.5)",
            }}
            whileHover={{
              scale: 1.05,
              borderColor: "hsl(150 100% 50%)",
              color: "hsl(150 100% 50%)",
            }}
            whileTap={{ scale: 0.95 }}
          >
            Skip
          </motion.button>
        )}
      </div>
    </motion.div>
  )
}

