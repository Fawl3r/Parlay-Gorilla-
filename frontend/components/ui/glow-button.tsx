"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
import { buttonPress, buttonGlow } from "@/lib/animations"

const PRIMARY_NEON = "hsl(150, 100%, 50%)"
const primaryNeonWithAlpha = (alpha: number) => `hsla(150, 100%, 50%, ${alpha})`

const glowButtonVariants = cva(
  "relative inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 overflow-hidden",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground",
        neon: "bg-transparent border-2 text-neon",
        outline: "border-2 border-primary/50 bg-transparent text-primary hover:border-primary",
        ghost: "hover:bg-primary/10 text-primary",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "neon",
      size: "default",
    },
  }
)

export interface GlowButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof glowButtonVariants> {
  asChild?: boolean
}

const GlowButton = React.forwardRef<HTMLButtonElement, GlowButtonProps>(
  ({ className, variant, size, children, ...props }, ref) => {
    return (
      <motion.button
        className={cn(glowButtonVariants({ variant, size, className }))}
        ref={ref}
        variants={buttonPress}
        whileHover="hover"
        whileTap="tap"
        style={{
          borderColor: variant === "neon" ? PRIMARY_NEON : undefined,
          color: variant === "neon" ? PRIMARY_NEON : undefined,
          boxShadow:
            variant === "neon"
              ? `0 0 20px ${primaryNeonWithAlpha(0.3)}, 0 0 40px ${primaryNeonWithAlpha(0.2)}`
              : undefined,
        }}
        {...props}
      >
        {/* Glow effect on hover */}
        <motion.div
          className="absolute inset-0 rounded-md"
          variants={buttonGlow}
          initial="initial"
          whileHover="hover"
          style={{
            background: `radial-gradient(circle, ${primaryNeonWithAlpha(0.3)} 0%, transparent 70%)`,
            filter: "blur(10px)",
          }}
        />
        {/* Particle effect */}
        <motion.div
          className="absolute inset-0"
          initial={{ opacity: 0 }}
          whileHover={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          {[...Array(5)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute h-1 w-1 rounded-full bg-primary"
              style={{
                left: `${20 + i * 15}%`,
                top: "50%",
              }}
              animate={{
                y: [-20, -40],
                opacity: [0, 1, 0],
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                delay: i * 0.2,
                ease: "easeOut",
              }}
            />
          ))}
        </motion.div>
        <span className="relative z-10">{children}</span>
      </motion.button>
    )
  }
)
GlowButton.displayName = "GlowButton"

export { GlowButton, glowButtonVariants }

