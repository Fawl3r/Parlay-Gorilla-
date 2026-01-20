"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { useClickAnimation } from "@/lib/hooks/useClickAnimation"

export interface FluidButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "primary" | "ghost" | "glass"
  size?: "sm" | "md" | "lg"
  loading?: boolean
  ripple?: boolean
}

export const FluidButton = React.forwardRef<HTMLButtonElement, FluidButtonProps>(
  (
    {
      className,
      variant = "default",
      size = "md",
      loading = false,
      ripple = true,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const { scale, handleMouseDown, handleMouseUp, handleMouseLeave } = useClickAnimation()
    const [ripples, setRipples] = React.useState<Array<{ x: number; y: number; id: number }>>([])
    const buttonRef = React.useRef<HTMLButtonElement>(null)

    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
      if (ripple && buttonRef.current) {
        const rect = buttonRef.current.getBoundingClientRect()
        const x = e.clientX - rect.left
        const y = e.clientY - rect.top

        const newRipple = {
          x,
          y,
          id: Date.now(),
        }

        setRipples((prev) => [...prev, newRipple])

        setTimeout(() => {
          setRipples((prev) => prev.filter((r) => r.id !== newRipple.id))
        }, 600)
      }

      props.onClick?.(e)
    }

    const variantClasses = {
      default: "bg-white/10 hover:bg-white/20 text-white border border-white/10",
      primary: "bg-emerald-500 hover:bg-emerald-600 text-white border border-emerald-500",
      ghost: "bg-transparent hover:bg-white/10 text-white/70 hover:text-white border border-transparent",
      glass: "bg-[rgba(255,255,255,0.05)] backdrop-blur-sm hover:bg-[rgba(255,255,255,0.1)] text-white border border-white/10",
    }

    const sizeClasses = {
      sm: "px-3 py-1.5 text-sm",
      md: "px-4 py-2 text-base",
      lg: "px-6 py-3 text-lg",
    }

    return (
      <motion.button
        ref={(node) => {
          if (typeof ref === "function") {
            ref(node)
          } else if (ref) {
            ref.current = node
          }
          buttonRef.current = node
        }}
        className={cn(
          "relative overflow-hidden rounded-lg font-medium transition-colors",
          "flex items-center justify-center gap-2",
          variantClasses[variant],
          sizeClasses[size],
          (disabled || loading) && "opacity-50 cursor-not-allowed",
          className
        )}
        disabled={disabled || loading}
        onClick={handleClick}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={() => {
          handleMouseLeave()
        }}
        animate={{ scale }}
        transition={{ type: "spring", stiffness: 400, damping: 17 }}
        whileHover={!disabled && !loading ? { scale: 1.02 } : undefined}
        whileTap={!disabled && !loading ? { scale: 0.98 } : undefined}
        {...props}
      >
        {loading && <Loader2 className="w-4 h-4 animate-spin" />}
        {children}
        {ripples.map((ripple) => (
          <motion.span
            key={ripple.id}
            className="absolute rounded-full pointer-events-none"
            style={{
              left: ripple.x,
              top: ripple.y,
              backgroundColor: "rgba(255, 255, 255, 0.3)",
            }}
            initial={{ width: 0, height: 0, x: "-50%", y: "-50%", opacity: 1 }}
            animate={{ width: 200, height: 200, opacity: 0 }}
            transition={{ duration: 0.6 }}
          />
        ))}
      </motion.button>
    )
  }
)
FluidButton.displayName = "FluidButton"
