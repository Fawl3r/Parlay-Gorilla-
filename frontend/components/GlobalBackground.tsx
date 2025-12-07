"use client"

import { useEffect, useState, useMemo } from "react"
import { motion } from "framer-motion"
import { useTheme } from "next-themes"
import { usePathname } from "next/navigation"
import Image from "next/image"

interface GlobalBackgroundProps {
  showGorilla?: boolean
  intensity?: "subtle" | "medium" | "strong"
}

/**
 * Global background component with animated effects.
 * 
 * Includes:
 * - Gorilla background image with parallax (dark mode only)
 * - Animated circuit board grid
 * - Horizontal circuit lines
 * - Glowing particles
 * - Pulsing glow orbs
 * 
 * Light mode has a clean, minimal background.
 */
export function GlobalBackground({
  showGorilla = true,
  intensity = "medium",
}: GlobalBackgroundProps) {
  const pathname = usePathname()
  // Hide gorilla on logged-in pages (app, profile, etc.)
  const isLoggedInPage = pathname?.startsWith('/app') || pathname?.startsWith('/profile')
  const shouldShowGorilla = showGorilla && !isLoggedInPage
  const [scrollY, setScrollY] = useState(0)
  const [mounted, setMounted] = useState(false)
  const { resolvedTheme } = useTheme()
  const isDark = resolvedTheme === "dark"

  // Generate stable random positions for particles
  const particlePositions = useMemo(() => 
    [...Array(20)].map(() => ({
      left: Math.random() * 100,
      top: Math.random() * 100,
      duration: 2 + Math.random() * 2,
      delay: Math.random() * 2,
    })), []
  )

  useEffect(() => {
    setMounted(true)
    
    const handleScroll = () => {
      setScrollY(window.scrollY)
    }

    window.addEventListener("scroll", handleScroll, { passive: true })
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  // Force dark background on body and html if dark mode is active
  // Must be called before any early returns to follow React hooks rules
  useEffect(() => {
    if (!mounted) return
    
    if (isDark) {
      document.documentElement.classList.add('dark')
      document.body.style.backgroundColor = '#0a0a0f'
      document.documentElement.style.backgroundColor = '#0a0a0f'
    } else {
      document.documentElement.classList.remove('dark')
      document.body.style.backgroundColor = '#e5e7eb'
      document.documentElement.style.backgroundColor = '#e5e7eb'
    }
  }, [isDark, mounted])

  const opacityMap = {
    subtle: { overlay: 0.5, effects: 0.1 },  // Reduced overlay to show gorilla
    medium: { overlay: 0.4, effects: 0.15 },  // Reduced overlay to show gorilla
    strong: { overlay: 0.3, effects: 0.2 },  // Reduced overlay to show gorilla
  }

  // Reduce effects on logged-in pages to show AnimatedBackground
  const config = isLoggedInPage 
    ? { overlay: 0.8, effects: 0.05 }  // Much more transparent on logged-in pages
    : opacityMap[intensity]
  const parallaxOffset = scrollY * 0.3

  if (!mounted) {
    return (
      <div className="fixed inset-0 -z-10 bg-gray-100 dark:bg-[#0a0a0f]" />
    )
  }

  // Light mode: Clean, minimal background with reduced white intensity
  if (!isDark) {
    return (
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        {/* Base light background - darker shades to reduce white intensity */}
        <div className="absolute inset-0 bg-gradient-to-br from-gray-200 via-gray-300 to-gray-400" />
        
        {/* Subtle grid pattern */}
        <div 
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%2310b981' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }}
        />
        
        {/* Subtle gradient orb - darker tones */}
        <div className="absolute top-20 right-1/4 w-96 h-96 bg-emerald-200/30 rounded-full blur-3xl" />
        <div className="absolute bottom-20 left-1/4 w-80 h-80 bg-cyan-200/25 rounded-full blur-3xl" />
      </div>
    )
  }

  // Dark mode: Full animated background
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      {/* Base dark background */}
      <div className="absolute inset-0 bg-[#0a0a0f]" />

      {/* Gorilla Background Image with Parallax */}
      {shouldShowGorilla && (
        <div 
          className="absolute inset-0"
          style={{
            transform: `translateY(${parallaxOffset}px)`,
            willChange: "transform",
            zIndex: 1
          }}
        >
          {/* Full gorilla image - using Next.js Image for optimization */}
          <Image
            src="/gorilla.png"
            alt="Parlay Gorilla Background"
            fill
            priority
            quality={90}
            className="object-contain object-center"
            style={{
              opacity: 0.7,
              filter: 'brightness(1.1) contrast(1.1)',
              zIndex: 0
            }}
            sizes="100vw"
          />
          
          {/* Gradient overlays for readability - lighter to show gorilla */}
          <div 
            className="absolute inset-0" 
            style={{
              background: `linear-gradient(to bottom, 
                rgba(10, 10, 15, ${config.overlay}) 0%, 
                rgba(10, 10, 15, ${config.overlay * 0.4}) 50%, 
                rgba(10, 10, 15, ${config.overlay}) 100%)`,
              zIndex: 1,
              pointerEvents: 'none'
            }}
          />
          <div 
            className="absolute inset-0"
            style={{
              background: `linear-gradient(to right, 
                rgba(10, 10, 15, ${config.overlay * 0.7}) 0%, 
                transparent 50%, 
                rgba(10, 10, 15, ${config.overlay * 0.7}) 100%)`,
              zIndex: 1,
              pointerEvents: 'none'
            }}
          />
          
          {/* Radial gradient for center focus - lighter */}
          <div 
            className="absolute inset-0" 
            style={{
              background: `radial-gradient(ellipse 75% 100% at center 45%, 
                transparent 0%, 
                rgba(10, 10, 15, 0.05) 40%, 
                rgba(10, 10, 15, 0.2) 70%, 
                rgba(10, 10, 15, 0.5) 100%)`,
              zIndex: 1,
              pointerEvents: 'none'
            }} 
          />
        </div>
      )}
      
      {/* Animated Circuit Board Grid Overlay */}
      <motion.div 
        className="absolute inset-0"
        animate={{
          backgroundPosition: ["0% 0%", "100% 100%"]
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "linear"
        }}
        style={{
          backgroundImage: `linear-gradient(rgba(0, 255, 136, 0.3) 1px, transparent 1px),
                           linear-gradient(90deg, rgba(0, 255, 136, 0.3) 1px, transparent 1px)`,
          backgroundSize: '50px 50px',
          opacity: config.effects
        }}
      />
      
      {/* Animated Circuit Lines */}
      <div className="absolute inset-0 overflow-hidden">
        {[...Array(6)].map((_, i) => (
          <motion.div
            key={`circuit-${i}`}
            className="absolute w-full h-px bg-gradient-to-r from-transparent via-emerald-400 to-transparent"
            style={{
              top: `${20 + i * 15}%`,
              opacity: 0.3
            }}
            animate={{
              x: ["-100%", "200%"],
              opacity: [0, 0.5, 0]
            }}
            transition={{
              duration: 3 + i * 0.5,
              repeat: Infinity,
              delay: i * 0.3,
              ease: "linear"
            }}
          />
        ))}
      </div>
      
      {/* Glowing Particles Effect */}
      <div className="absolute inset-0">
        {particlePositions.map((particle, i) => (
          <motion.div
            key={`particle-${i}`}
            className="absolute w-2 h-2 bg-emerald-400 rounded-full blur-sm"
            style={{
              left: `${particle.left}%`,
              top: `${particle.top}%`,
            }}
            animate={{
              y: [0, -30, 0],
              opacity: [0.3, 1, 0.3],
              scale: [1, 1.5, 1]
            }}
            transition={{
              duration: particle.duration,
              repeat: Infinity,
              delay: particle.delay,
              ease: "easeInOut"
            }}
          />
        ))}
      </div>
      
      {/* Pulsing Glow Orbs */}
      <div className="absolute inset-0">
        <motion.div
          className="absolute top-1/4 left-1/4 w-96 h-96 bg-emerald-500/20 rounded-full blur-[120px]"
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.2, 0.4, 0.2]
          }}
          transition={{
            duration: 4,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        <motion.div
          className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-500/15 rounded-full blur-[120px]"
          animate={{
            scale: [1, 1.4, 1],
            opacity: [0.15, 0.35, 0.15]
          }}
          transition={{
            duration: 5,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 1
          }}
        />
        <motion.div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-emerald-400/10 rounded-full blur-[150px]"
          animate={{
            scale: [1, 1.5, 1],
            opacity: [0.1, 0.3, 0.1]
          }}
          transition={{
            duration: 6,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 2
          }}
        />
      </div>

      {/* Additional Electric Blue Accent (from ParlayGorillaBackground) */}
      <motion.div
        className="absolute top-1/4 right-1/4 w-96 h-96 rounded-full blur-3xl"
        style={{
          background: "radial-gradient(circle, hsl(199 89% 48% / 0.15) 0%, transparent 70%)",
        }}
        animate={{
          x: [0, 50, 0],
          y: [0, -30, 0],
          opacity: [0.15, 0.3, 0.15],
        }}
        transition={{
          duration: 5,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      {/* Orange/Amber Accent Glow */}
      <motion.div
        className="absolute top-1/3 left-1/3 w-64 h-64 rounded-full blur-2xl"
        style={{
          background: "radial-gradient(circle, hsl(25 95% 53% / 0.1) 0%, transparent 70%)",
        }}
        animate={{
          opacity: [0.1, 0.2, 0.1],
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

