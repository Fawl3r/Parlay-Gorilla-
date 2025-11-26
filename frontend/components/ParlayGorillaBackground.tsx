"use client"

import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import Image from "next/image"

interface ParlayGorillaBackgroundProps {
  intensity?: "subtle" | "medium" | "strong"
  className?: string
}

export function ParlayGorillaBackground({
  intensity = "medium",
  className = "",
}: ParlayGorillaBackgroundProps) {
  const [scrollY, setScrollY] = useState(0)

  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.scrollY)
    }

    window.addEventListener("scroll", handleScroll, { passive: true })
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  const opacity = {
    subtle: "opacity-40",
    medium: "opacity-50",
    strong: "opacity-60",
  }[intensity]

  // Parallax offset calculation
  const parallaxOffset = scrollY * 0.3

  return (
    <div className={`fixed inset-0 -z-10 overflow-hidden pointer-events-none ${className}`}>
      {/* Grey Gradient Background - Base layer */}
      <div
        className="absolute inset-0"
        style={{
          background: "linear-gradient(180deg, hsl(215 16% 30%) 0%, hsl(215 16% 20%) 30%, hsl(222 47% 11%) 70%, hsl(215 16% 15%) 100%)",
        }}
      />

      {/* Parlay Gorilla Image */}
      <div
        className={`absolute inset-0 ${opacity} transition-opacity duration-300`}
        style={{
          transform: `translateY(${parallaxOffset}px)`,
          willChange: "transform",
        }}
      >
        <Image
          src="/parlay-gorilla.png.webp"
          alt="Parlay Gorilla"
          fill
          priority
          quality={90}
          className="object-cover object-center"
          style={{
            mixBlendMode: "normal",
          }}
        />
      </div>

      {/* Subtle dark overlay for content readability */}
      <div className="absolute inset-0 dark-overlay opacity-30" />

      {/* Animated Circuit Veins - Enhanced Gorilla Armor Pattern */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Horizontal circuit lines */}
        {[...Array(15)].map((_, i) => (
          <motion.div
            key={`h-${i}`}
            className="absolute h-px"
            style={{
              left: `${(i * 6.66) % 100}%`,
              top: `${(i * 7) % 100}%`,
              width: "300px",
              background: `linear-gradient(90deg, 
                transparent 0%, 
                hsl(150 100% 50% / ${0.4 - i * 0.015}) 30%,
                hsl(199 89% 48% / ${0.3 - i * 0.01}) 50%,
                hsl(150 100% 50% / ${0.4 - i * 0.015}) 70%,
                transparent 100%)`,
              boxShadow: `0 0 ${10 + i * 2}px hsl(150 100% 50% / 0.3)`,
            }}
            animate={{
              x: [0, 150, 0],
              opacity: [0.3, 0.8, 0.3],
              scaleX: [1, 1.2, 1],
            }}
            transition={{
              duration: 4 + i * 0.3,
              repeat: Infinity,
              delay: i * 0.2,
              ease: "easeInOut",
            }}
          />
        ))}
        {/* Vertical circuit lines */}
        {[...Array(10)].map((_, i) => (
          <motion.div
            key={`v-${i}`}
            className="absolute w-px"
            style={{
              left: `${(i * 10) % 100}%`,
              top: `${(i * 10) % 100}%`,
              height: "250px",
              background: `linear-gradient(180deg, 
                transparent 0%, 
                hsl(199 89% 48% / ${0.3 - i * 0.02}) 40%,
                hsl(150 100% 50% / ${0.4 - i * 0.015}) 60%,
                transparent 100%)`,
              boxShadow: `0 0 ${8 + i * 2}px hsl(199 89% 48% / 0.3)`,
            }}
            animate={{
              y: [0, 100, 0],
              opacity: [0.2, 0.7, 0.2],
              scaleY: [1, 1.3, 1],
            }}
            transition={{
              duration: 3 + i * 0.4,
              repeat: Infinity,
              delay: i * 0.25,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>

      {/* Gorilla Backlight Pulse - Enhanced Breathing Animation */}
      <motion.div
        className="absolute inset-0"
        style={{
          background: "radial-gradient(ellipse at center 40%, hsl(150 100% 50% / 0.15) 0%, hsl(199 89% 48% / 0.1) 30%, transparent 60%)",
        }}
        animate={{
          opacity: [0.4, 0.7, 0.4],
          scale: [1, 1.08, 1],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      {/* Secondary backlight pulse */}
      <motion.div
        className="absolute inset-0"
        style={{
          background: "radial-gradient(ellipse at center 60%, hsl(25 95% 53% / 0.08) 0%, transparent 50%)",
        }}
        animate={{
          opacity: [0.2, 0.4, 0.2],
          scale: [1, 1.05, 1],
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          delay: 1.5,
          ease: "easeInOut",
        }}
      />

      {/* Electric Blue Accent Glow */}
      <motion.div
        className="absolute top-1/4 right-1/4 w-96 h-96 rounded-full blur-3xl"
        style={{
          background: "radial-gradient(circle, hsl(199 89% 48% / 0.2) 0%, transparent 70%)",
        }}
        animate={{
          x: [0, 50, 0],
          y: [0, -30, 0],
          opacity: [0.2, 0.4, 0.2],
        }}
        transition={{
          duration: 5,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      {/* Orange/Amber Eye Glow Effect */}
      <motion.div
        className="absolute top-1/3 left-1/3 w-64 h-64 rounded-full blur-2xl"
        style={{
          background: "radial-gradient(circle, hsl(25 95% 53% / 0.15) 0%, transparent 70%)",
        }}
        animate={{
          opacity: [0.15, 0.3, 0.15],
          scale: [1, 1.1, 1],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
    </div>
  )
}

