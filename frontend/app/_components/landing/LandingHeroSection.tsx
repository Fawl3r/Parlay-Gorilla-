"use client"

import { motion, useScroll, useTransform } from "framer-motion"
import { useEffect, useMemo, useRef, useState } from "react"
import Link from "next/link"
import Image from "next/image"
import { Sparkles, ArrowRight } from "lucide-react"

import { api } from "@/lib/api"

// Pre-generate particle positions to avoid hydration mismatch
function seededRandom(seed: number): number {
  const x = Math.sin(seed) * 10000
  return x - Math.floor(x)
}

export function LandingHeroSection() {
  const [mounted, setMounted] = useState(false)

  // Memoize particle positions with deterministic values
  const particlePositions = useMemo(
    () =>
      [...Array(15)].map((_, i) => ({
        // Round to 4 decimals to match SSR/client formatting and avoid hydration mismatches.
        left: `${(40 + seededRandom(i * 2) * 20).toFixed(4)}%`,
        top: `${(40 + seededRandom(i * 2 + 1) * 20).toFixed(4)}%`,
        xOffset: seededRandom(i * 3) * 50 - 25,
        duration: 3 + seededRandom(i * 4) * 2,
        delay: seededRandom(i * 5) * 2,
      })),
    []
  )

  const heroRef = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"],
  })

  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0])

  // Trigger animations when page becomes visible (after age gate removal)
  useEffect(() => {
    setMounted(true)

    // Pre-warm the cache for faster app loads
    api.warmupCache()

    // Force a re-render to trigger animations after age gate is removed
    const checkVisibility = () => {
      if (!document.body.classList.contains("age-gate-active")) {
        // Trigger animations by forcing a small delay
        setTimeout(() => {
          window.dispatchEvent(new Event("resize"))
        }, 100)
      }
    }

    // Check immediately and on interval
    checkVisibility()
    const interval = setInterval(checkVisibility, 200)

    return () => clearInterval(interval)
  }, [])

  return (
    <section
      ref={heroRef}
      className="relative min-h-screen flex items-center justify-center overflow-hidden"
      style={{
        backgroundImage: "url('/images/s1back.png')",
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
      }}
    >
      {/* Dark overlay for text readability - lighter to showcase background */}
      <div className="absolute inset-0 bg-black/30 z-10" />

      {/* Subtle gradient overlay for better text contrast */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-black/20 to-black/40 z-10" />

      {/* Additional radial gradient for center focus */}
      <div
        className="absolute inset-0 bg-radial-gradient from-transparent via-transparent to-black/20 z-10"
        style={{
          background:
            "radial-gradient(ellipse at center, transparent 0%, rgba(0,0,0,0.1) 50%, rgba(0,0,0,0.3) 100%)",
        }}
      />

      {/* Content Container */}
      <motion.div
        className="container mx-auto max-w-7xl px-4 relative z-20"
        initial={{ opacity: 0 }}
        animate={mounted ? { opacity: 1 } : { opacity: 0 }}
        transition={{ duration: 0.6, delay: 0.1 }}
        style={mounted ? { opacity } : { opacity: 0 }}
      >
        <div className="grid lg:grid-cols-2 gap-12 items-center min-h-[80vh]">
          {/* Left Column - Text Content */}
          <motion.div
            key={mounted ? "mounted" : "unmounted"}
            initial={{ opacity: 0, x: -50 }}
            animate={mounted ? { opacity: 1, x: 0 } : { opacity: 0, x: -50 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-left lg:text-left"
          >
            {/* Badge with glow */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-[#00DD55]/20 border border-[#00DD55]/50 mb-8 backdrop-blur-md relative overflow-hidden"
              style={{
                boxShadow: "0 0 6px #00DD55, 0 0 12px #00BB44",
              }}
            >
              <div className="absolute inset-0 bg-[#00DD55]/30 blur-xl" />
              <Sparkles
                className="h-4 w-4 text-[#00DD55] relative z-10"
                style={{
                  filter: "drop-shadow(0 0 2px rgba(0, 221, 85, 0.5))",
                }}
              />
              <span
                className="text-sm font-semibold text-white tracking-wide relative z-10"
                style={{
                  textShadow: "0 0 3px rgba(0, 221, 85, 0.5)",
                }}
              >
                Gorilla Parlay Insights
              </span>
            </motion.div>

            {/* Main headline with animated gradient */}
            <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl xl:text-8xl 2xl:text-8xl font-black mb-6 leading-[0.95] tracking-tight max-w-4xl">
              <motion.span
                className="block text-[#00DD55]"
                style={{
                  textShadow: "0 0 4px rgba(0, 221, 85, 0.7), 0 0 7px rgba(0, 187, 68, 0.5)",
                  backgroundPosition: "0% 50%",
                  backgroundSize: "200% 200%",
                }}
                animate={{
                  backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"],
                }}
                transition={{
                  duration: 5,
                  repeat: Infinity,
                  ease: "linear",
                }}
              >
                Build Smarter
              </motion.span>
              <motion.span
                className="block text-[#00DD55] mt-2"
                style={{
                  textShadow: "0 0 4px rgba(0, 221, 85, 0.7), 0 0 7px rgba(0, 187, 68, 0.5)",
                }}
              >
                Parlays
              </motion.span>
              <span className="block text-white mt-4 text-4xl sm:text-5xl md:text-6xl lg:text-6xl xl:text-6xl 2xl:text-6xl font-bold">
                With AI Context
              </span>
            </h1>

            {/* Subtext with better contrast */}
            <p className="text-lg sm:text-xl md:text-2xl lg:text-2xl xl:text-2xl 2xl:text-2xl text-white mb-10 max-w-2xl leading-relaxed font-medium">
              Build 1–20 leg parlay ideas with{" "}
              <span
                className="text-[#00DD55] font-semibold"
                style={{
                  textShadow: "0 0 3px rgba(0, 221, 85, 0.6)",
                }}
              >
                probability estimates
              </span>
              , risk indicators, and plain-English explanations. Mix{" "}
              <span className="text-white font-semibold">NFL, NBA, and NHL</span> — then decide what to analyze (or skip).
            </p>

            {/* CTA Buttons with enhanced effects */}
            <div className="flex flex-col sm:flex-row gap-4 mb-6 max-w-2xl">
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} className="relative">
                <div className="absolute inset-0 bg-[#00DD55] blur-xl opacity-60 rounded-xl" />
                <Link
                  href="/auth/signup"
                  className="relative inline-flex items-center gap-2 px-6 sm:px-8 py-3 sm:py-4 text-base sm:text-lg font-bold text-black bg-[#00DD55] rounded-xl hover:bg-[#22DD66] transition-all max-w-[200px] sm:max-w-none"
                  style={{
                    boxShadow: "0 0 6px #00DD55, 0 0 12px #00BB44, 0 0 20px #22DD66",
                  }}
                >
                  Get Started Free
                  <ArrowRight className="h-4 w-4 sm:h-5 sm:w-5" />
                </Link>
              </motion.div>

              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Link
                  href="/auth/login"
                  className="inline-flex items-center gap-2 px-6 sm:px-8 py-3 sm:py-4 text-base sm:text-lg font-semibold text-white bg-transparent border-2 border-[#00DD55] rounded-xl hover:bg-[#00DD55]/10 transition-all backdrop-blur-md max-w-[150px] sm:max-w-none"
                  style={{
                    boxShadow: "0 0 6px #00DD55 / 0.3",
                  }}
                >
                  Sign In
                </Link>
              </motion.div>
            </div>

            <p className="text-sm text-white/60 font-medium">
              AI sports analytics & research • We do not accept bets or facilitate wagering • All scenarios are hypothetical and for informational/entertainment purposes only • 21+ only
            </p>
          </motion.div>

          {/* Right Column - Enhanced Visual Effects */}
          <motion.div
            key={mounted ? "mounted-right" : "unmounted-right"}
            initial={{ opacity: 0, x: 50 }}
            animate={mounted ? { opacity: 1, x: 0 } : { opacity: 0, x: 50 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="relative hidden lg:flex items-center justify-center"
          >
            <div className="relative w-full h-[600px] flex items-center justify-center">
              {/* Hero Image - Seamlessly blended with background */}
              <motion.div
                className="absolute inset-0 flex items-center justify-center z-0"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 1.2, delay: 0.3, ease: "easeOut" }}
              >
                <div
                  className="relative w-full h-full"
                  style={{
                    maskImage: "radial-gradient(ellipse 70% 70% at center, black 40%, transparent 75%)",
                    WebkitMaskImage: "radial-gradient(ellipse 70% 70% at center, black 40%, transparent 75%)",
                  }}
                >
                  <Image
                    src="/images/hero.png"
                    alt="Parlay Gorilla Hero"
                    fill
                    className="object-contain"
                    priority
                    style={{
                      opacity: 0.9,
                      filter: "brightness(1.15) saturate(1.3) contrast(1.1)",
                    }}
                  />
                </div>
              </motion.div>

              {/* Central Glow Effect */}
              <motion.div
                className="absolute inset-0 bg-[#00DD55]/20 rounded-full blur-[150px] z-10"
                animate={{
                  scale: [1, 1.2, 1],
                  opacity: [0.3, 0.6, 0.3],
                }}
                transition={{
                  duration: 4,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
              />

              {/* Animated Circuit Board Pattern */}
              <motion.div
                className="absolute inset-0 opacity-30 z-10"
                animate={{
                  backgroundPosition: ["0% 0%", "100% 100%"],
                }}
                transition={{
                  duration: 15,
                  repeat: Infinity,
                  ease: "linear",
                }}
                style={{
                  backgroundImage: "radial-gradient(circle, rgba(0, 255, 102, 0.4) 1px, transparent 1px)",
                  backgroundSize: "40px 40px",
                }}
              />

              {/* Multiple Animated Glow Rings */}
              {[1, 2, 3].map((ring, i) => (
                <motion.div
                  key={ring}
                  className="absolute border-2 border-[#00DD55]/30 rounded-full z-10"
                  style={{
                    width: `${300 + i * 100}px`,
                    height: `${300 + i * 100}px`,
                  }}
                  animate={{
                    scale: [1, 1.2 + i * 0.1, 1],
                    opacity: [0.2, 0.5, 0.2],
                    rotate: [0, 360],
                  }}
                  transition={{
                    duration: 4 + i,
                    repeat: Infinity,
                    ease: "easeInOut",
                    delay: i * 0.5,
                  }}
                />
              ))}

              {/* Floating Particles */}
              {particlePositions.map((particle, i) => (
                <motion.div
                  key={i}
                  className="absolute w-1 h-1 bg-[#00DD55] rounded-full z-20"
                  style={{
                    left: particle.left,
                    top: particle.top,
                  }}
                  animate={{
                    y: [0, -50, 0],
                    x: [0, particle.xOffset, 0],
                    opacity: [0, 1, 0],
                    scale: [0, 1, 0],
                  }}
                  transition={{
                    duration: particle.duration,
                    repeat: Infinity,
                    delay: particle.delay,
                    ease: "easeInOut",
                  }}
                />
              ))}
            </div>
          </motion.div>
        </div>
      </motion.div>
    </section>
  )
}


