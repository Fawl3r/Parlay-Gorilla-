"use client"

import { useEffect, useRef } from "react"
import { motion } from "framer-motion"

interface AnimatedBackgroundProps {
  variant?: "grid" | "particles" | "rain" | "all"
  intensity?: "low" | "medium" | "high"
  className?: string
}

export function AnimatedBackground({
  variant = "all",
  intensity = "medium",
  className = "",
}: AnimatedBackgroundProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const particlesRef = useRef<Array<{
    x: number
    y: number
    vx: number
    vy: number
    size: number
    opacity: number
  }>>([])

  const intensityMap = {
    low: { particles: 20, gridOpacity: 0.1, rainSpeed: 1 },
    medium: { particles: 50, gridOpacity: 0.2, rainSpeed: 2 },
    high: { particles: 100, gridOpacity: 0.3, rainSpeed: 3 },
  }

  const config = intensityMap[intensity]

  // Initialize particles
  useEffect(() => {
    if ((variant === "particles" || variant === "all") && typeof window !== "undefined") {
      const particles: typeof particlesRef.current = []
      for (let i = 0; i < config.particles; i++) {
        particles.push({
          x: Math.random() * window.innerWidth,
          y: Math.random() * window.innerHeight,
          vx: (Math.random() - 0.5) * 0.5,
          vy: (Math.random() - 0.5) * 0.5,
          size: Math.random() * 2 + 1,
          opacity: Math.random() * 0.5 + 0.2,
        })
      }
      particlesRef.current = particles
    }
  }, [variant, config.particles])

  // Animate particles and rain
  useEffect(() => {
    if (
      (variant !== "particles" && variant !== "rain" && variant !== "all") ||
      !canvasRef.current ||
      typeof window === "undefined"
    ) {
      return
    }

    const canvas = canvasRef.current
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const resizeCanvas = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    resizeCanvas()
    window.addEventListener("resize", resizeCanvas)

    let animationFrame: number

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      if (variant === "particles" || variant === "all") {
        // Draw particles
        particlesRef.current.forEach((particle) => {
          particle.x += particle.vx
          particle.y += particle.vy

          // Wrap around edges
          if (particle.x < 0) particle.x = canvas.width
          if (particle.x > canvas.width) particle.x = 0
          if (particle.y < 0) particle.y = canvas.height
          if (particle.y > canvas.height) particle.y = 0

          // Draw particle with glow
          ctx.beginPath()
          ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2)
          ctx.fillStyle = `rgba(0, 255, 140, ${particle.opacity})`
          ctx.shadowBlur = 10
          ctx.shadowColor = "rgba(0, 255, 140, 0.8)"
          ctx.fill()
          ctx.shadowBlur = 0
        })
      }

      if (variant === "rain" || variant === "all") {
        // Draw digital rain effect
        ctx.strokeStyle = `rgba(0, 255, 140, ${config.gridOpacity})`
        ctx.lineWidth = 1
        for (let i = 0; i < 50; i++) {
          const x = (i * canvas.width) / 50
          const y = (Date.now() * config.rainSpeed + i * 100) % canvas.height
          ctx.beginPath()
          ctx.moveTo(x, y)
          ctx.lineTo(x, y + 20)
          ctx.stroke()
        }
      }

      animationFrame = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      window.removeEventListener("resize", resizeCanvas)
      cancelAnimationFrame(animationFrame)
    }
  }, [variant, config.gridOpacity, config.rainSpeed])

  return (
    <div className={`fixed inset-0 -z-10 overflow-hidden ${className}`}>
      {/* Glowing Grid */}
      {(variant === "grid" || variant === "all") && (
        <motion.div
          className="absolute inset-0"
          style={{
            backgroundImage: `
              linear-gradient(rgba(0, 255, 140, ${config.gridOpacity}) 1px, transparent 1px),
              linear-gradient(90deg, rgba(0, 255, 140, ${config.gridOpacity}) 1px, transparent 1px)
            `,
            backgroundSize: "50px 50px",
          }}
          animate={{
            backgroundPosition: ["0 0", "50px 50px"],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "linear",
          }}
        />
      )}

      {/* Particle Fog Canvas */}
      {(variant === "particles" || variant === "all") && (
        <canvas
          ref={canvasRef}
          className="absolute inset-0"
          style={{ mixBlendMode: "screen" }}
        />
      )}

      {/* Digital Rain Canvas */}
      {(variant === "rain" || variant === "all") && variant !== "particles" && (
        <canvas
          ref={canvasRef}
          className="absolute inset-0"
          style={{ mixBlendMode: "screen" }}
        />
      )}

      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-background/50" />
    </div>
  )
}

