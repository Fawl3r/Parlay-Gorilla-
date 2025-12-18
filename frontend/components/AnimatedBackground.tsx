"use client"

import { motion } from "framer-motion"
import { useMemo } from "react"

// Pre-generate particle positions to avoid hydration mismatch
function seededRandom(seed: number): number {
  const x = Math.sin(seed) * 10000
  return x - Math.floor(x)
}

interface AnimatedBackgroundProps {
  variant?: "default" | "intense" | "subtle"
}

export function AnimatedBackground({ variant = "default" }: AnimatedBackgroundProps) {
  // Memoize particle positions with deterministic values
  const particlePositions = useMemo(() => 
    [...Array(variant === "intense" ? 40 : variant === "subtle" ? 15 : 25)].map((_, i) => ({
      // Round to 4 decimals to match SSR/client formatting and avoid hydration mismatches.
      left: `${(40 + seededRandom(i * 2) * 20).toFixed(4)}%`,
      top: `${(40 + seededRandom(i * 2 + 1) * 20).toFixed(4)}%`,
      xOffset: seededRandom(i * 3) * 50 - 25,
      duration: 3 + seededRandom(i * 4) * 2,
      delay: seededRandom(i * 5) * 2,
      size: variant === "intense" ? 2 : 1,
    })), [variant]
  )

  const intensity = variant === "intense" ? 0.35 : variant === "subtle" ? 0.2 : 0.3

  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none" style={{ zIndex: 0, backgroundColor: '#0a0a0f' }}>
      {/* Base Gradient - Rich dark tones - Always visible and more vibrant */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#0a0a0f] via-[#0f172a] to-[#1a1a2e]" />
      
      {/* Secondary gradient layer for depth */}
      <div className="absolute inset-0 bg-gradient-to-t from-[#1a1a2e] via-transparent to-[#0a0a0f]" />
      
      {/* Animated Radial Gradients - More dynamic and visible */}
      <motion.div
        className="absolute inset-0"
        style={{ opacity: intensity + 0.2 }}
        animate={{
          background: [
            "radial-gradient(circle at 20% 30%, rgba(0, 255, 140, 0.35) 0%, transparent 60%), radial-gradient(circle at 80% 70%, rgba(56, 189, 248, 0.3) 0%, transparent 60%)",
            "radial-gradient(circle at 80% 30%, rgba(0, 255, 140, 0.3) 0%, transparent 60%), radial-gradient(circle at 20% 70%, rgba(139, 92, 246, 0.35) 0%, transparent 60%)",
            "radial-gradient(circle at 50% 50%, rgba(0, 255, 140, 0.35) 0%, transparent 60%), radial-gradient(circle at 30% 80%, rgba(56, 189, 248, 0.3) 0%, transparent 60%)",
            "radial-gradient(circle at 20% 30%, rgba(0, 255, 140, 0.35) 0%, transparent 60%), radial-gradient(circle at 80% 70%, rgba(56, 189, 248, 0.3) 0%, transparent 60%)",
          ],
        }}
        transition={{
          duration: 25,
          repeat: Infinity,
          ease: "linear",
        }}
      />
      
      {/* Enhanced Grid Pattern - Subtle but visible */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: `
            linear-gradient(rgba(0, 255, 140, 0.08) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 255, 140, 0.08) 1px, transparent 1px),
            linear-gradient(rgba(56, 189, 248, 0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(56, 189, 248, 0.04) 1px, transparent 1px)
          `,
          backgroundSize: '100px 100px, 100px 100px, 20px 20px, 20px 20px',
          backgroundPosition: '0 0, 0 0, 0 0, 0 0',
        }}
      />
      
      {/* Animated Particles - Subtle but visible */}
      {particlePositions.map((particle, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full bg-emerald-400/30"
          style={{
            left: particle.left,
            top: particle.top,
            width: `${particle.size}px`,
            height: `${particle.size}px`,
            boxShadow: `0 0 ${particle.size * 4}px rgba(0, 255, 140, 0.3)`,
          }}
          animate={{
            y: [0, -40 - Math.random() * 20, 0],
            x: [0, particle.xOffset, 0],
            opacity: [0.2, 0.6, 0.2],
            scale: [1, 1.5, 1],
          }}
          transition={{
            duration: particle.duration,
            repeat: Infinity,
            delay: particle.delay,
            ease: "easeInOut",
          }}
        />
      ))}
      
      {/* Enhanced Corner Glows with animation - Subtle */}
      <motion.div
        className="absolute top-0 left-0 w-[500px] h-[500px] bg-emerald-500/15 rounded-full blur-[150px] -translate-x-1/2 -translate-y-1/2"
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.2, 0.4, 0.2],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      <motion.div
        className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-blue-500/15 rounded-full blur-[150px] translate-x-1/2 translate-y-1/2"
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.2, 0.4, 0.2],
        }}
        transition={{
          duration: 10,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 2,
        }}
      />
      
      {/* Additional accent glows - Subtle */}
      <motion.div
        className="absolute top-1/2 left-1/4 w-[300px] h-[300px] bg-purple-500/10 rounded-full blur-[100px]"
        animate={{
          x: [-50, 50, -50],
          y: [-30, 30, -30],
          opacity: [0.15, 0.3, 0.15],
        }}
        transition={{
          duration: 15,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      
      {/* Subtle scan line effect */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-b from-transparent via-emerald-500/5 to-transparent"
        animate={{
          y: ["-100%", "200%"],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "linear",
        }}
      />
    </div>
  )
}
