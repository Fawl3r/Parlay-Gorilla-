"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { useHoverAnimation } from "@/lib/hooks/useHoverAnimation"
import { useClickAnimation } from "@/lib/hooks/useClickAnimation"
import { cn } from "@/lib/utils"

export interface RippleButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "primary" | "ghost"
  rippleColor?: string
}

export function RippleButton({
  children,
  className,
  variant = "default",
  rippleColor = "rgba(255, 255, 255, 0.3)",
  onClick,
  ...props
}: RippleButtonProps) {
  const [ripples, setRipples] = React.useState<Array<{ x: number; y: number; id: number }>>([])
  const buttonRef = React.useRef<HTMLButtonElement>(null)

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (!buttonRef.current) return

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

    onClick?.(e)
  }

  const variantClasses = {
    default: "bg-white/10 hover:bg-white/20 text-white",
    primary: "bg-emerald-500 hover:bg-emerald-600 text-white",
    ghost: "bg-transparent hover:bg-white/10 text-white/70 hover:text-white",
  }

  return (
    <button
      ref={buttonRef}
      className={cn(
        "relative overflow-hidden rounded-lg px-4 py-2 font-medium transition-colors",
        variantClasses[variant],
        className
      )}
      onClick={handleClick}
      {...props}
    >
      {children}
      {ripples.map((ripple) => (
        <motion.span
          key={ripple.id}
          className="absolute rounded-full pointer-events-none"
          style={{
            left: ripple.x,
            top: ripple.y,
            backgroundColor: rippleColor,
          }}
          initial={{ width: 0, height: 0, x: "-50%", y: "-50%", opacity: 1 }}
          animate={{ width: 200, height: 200, opacity: 0 }}
          transition={{ duration: 0.6 }}
        />
      ))}
    </button>
  )
}

export interface InteractiveCardProps extends React.HTMLAttributes<HTMLDivElement> {
  hover?: boolean
}

export function InteractiveCard({ children, className, hover = true, ...props }: InteractiveCardProps) {
  const { isHovered, handleMouseEnter, handleMouseLeave } = useHoverAnimation()
  const { scale, handleMouseDown, handleMouseUp, handleMouseLeave: handleClickLeave } = useClickAnimation()

  return (
    <motion.div
      className={cn("rounded-xl border border-white/8 bg-[rgba(18,18,23,0.6)] backdrop-blur-md", className)}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={() => {
        handleMouseLeave()
        handleClickLeave()
      }}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      animate={{
        scale: hover && isHovered ? 1.02 : scale.get(),
        y: hover && isHovered ? -2 : 0,
      }}
      transition={{ duration: 0.2 }}
      {...props}
    >
      {children}
    </motion.div>
  )
}
