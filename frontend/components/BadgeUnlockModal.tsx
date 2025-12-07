"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { X, ChevronLeft, ChevronRight } from "lucide-react"
import type { BadgeResponse } from "@/lib/api"

interface BadgeUnlockModalProps {
  badges: BadgeResponse[]
  onClose: () => void
}

interface ConfettiParticle {
  id: number
  x: number
  y: number
  color: string
  duration: number
  rotate: number
}

export function BadgeUnlockModal({ badges, onClose }: BadgeUnlockModalProps) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [showConfetti, setShowConfetti] = useState(true)
  const [confettiParticles, setConfettiParticles] = useState<ConfettiParticle[]>([])
  const [mounted, setMounted] = useState(false)

  // Only generate confetti on client side to avoid hydration mismatch
  useEffect(() => {
    setMounted(true)
    if (showConfetti && typeof window !== "undefined") {
      const particles: ConfettiParticle[] = Array.from({ length: 50 }).map((_, i) => ({
        id: i,
        x: Math.random() * window.innerWidth,
        y: Math.random() * window.innerHeight,
        color: ["bg-emerald-400", "bg-green-400", "bg-yellow-400", "bg-blue-400", "bg-purple-400"][
          Math.floor(Math.random() * 5)
        ],
        duration: 1.5 + Math.random(),
        rotate: Math.random() * 360,
      }))
      setConfettiParticles(particles)
    }
  }, [showConfetti])

  useEffect(() => {
    // Remove confetti after 2 seconds
    const timer = setTimeout(() => setShowConfetti(false), 2000)
    return () => clearTimeout(timer)
  }, [currentIndex])

  if (badges.length === 0) return null

  const currentBadge = badges[currentIndex]
  const hasMultiple = badges.length > 1

  const handleNext = () => {
    if (currentIndex < badges.length - 1) {
      setCurrentIndex(currentIndex + 1)
      setShowConfetti(true)
    } else {
      onClose()
    }
  }

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1)
      setShowConfetti(true)
    }
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
        onClick={onClose}
      >
        {/* Confetti Effect - Only render on client */}
        {mounted && showConfetti && confettiParticles.length > 0 && (
          <div className="absolute inset-0 pointer-events-none overflow-hidden">
            {confettiParticles.map((particle) => (
              <motion.div
                key={particle.id}
                initial={{
                  x: typeof window !== "undefined" ? window.innerWidth / 2 : 0,
                  y: typeof window !== "undefined" ? window.innerHeight / 2 : 0,
                  scale: 0,
                  rotate: 0,
                }}
                animate={{
                  x: particle.x,
                  y: particle.y,
                  scale: [0, 1, 1],
                  rotate: particle.rotate,
                }}
                transition={{
                  duration: particle.duration,
                  ease: "easeOut",
                }}
                className={`absolute h-2 w-2 rounded-full ${particle.color}`}
              />
            ))}
          </div>
        )}

        {/* Modal Content */}
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          className="relative bg-gradient-to-br from-gray-900 to-black border border-emerald-500/30 rounded-2xl p-8 max-w-md w-full mx-4 text-center overflow-hidden"
        >
          {/* Close Button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-500 hover:text-white transition-colors"
          >
            <X className="h-6 w-6" />
          </button>

          {/* Badge Counter */}
          {hasMultiple && (
            <div className="absolute top-4 left-4 text-sm text-gray-400">
              {currentIndex + 1} / {badges.length}
            </div>
          )}

          {/* Header */}
          <motion.div
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="mb-6"
          >
            <h2 className="text-lg text-emerald-400 font-medium mb-1">🎉 Badge Unlocked!</h2>
            {hasMultiple && (
              <p className="text-xs text-gray-500">You unlocked {badges.length} badges!</p>
            )}
          </motion.div>

          {/* Badge Icon */}
          <motion.div
            key={currentBadge.id}
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ type: "spring", duration: 0.6 }}
            className="mb-6"
          >
            <div className="text-8xl">{currentBadge.icon || "🏆"}</div>
          </motion.div>

          {/* Badge Name & Description */}
          <motion.div
            key={`info-${currentBadge.id}`}
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <h3 className="text-2xl font-bold text-white mb-2">{currentBadge.name}</h3>
            <p className="text-gray-400">{currentBadge.description}</p>
          </motion.div>

          {/* Navigation */}
          <div className="flex items-center justify-center gap-4 mt-8">
            {hasMultiple && currentIndex > 0 && (
              <button
                onClick={handlePrev}
                className="flex items-center gap-1 px-4 py-2 text-gray-400 hover:text-white transition-colors"
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </button>
            )}
            
            <button
              onClick={handleNext}
              className="px-6 py-2 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-lg hover:from-emerald-400 hover:to-green-400 transition-all flex items-center gap-1"
            >
              {currentIndex < badges.length - 1 ? (
                <>
                  Next Badge
                  <ChevronRight className="h-4 w-4" />
                </>
              ) : (
                "Awesome!"
              )}
            </button>
          </div>

          {/* Glow Effect */}
          <div className="absolute inset-0 bg-gradient-to-t from-emerald-500/10 to-transparent pointer-events-none" />
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}

