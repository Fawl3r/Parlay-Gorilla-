"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

export interface FloatingCardProps extends React.HTMLAttributes<HTMLDivElement> {
  hover?: boolean
  delay?: number
}

export const FloatingCard = React.forwardRef<HTMLDivElement, FloatingCardProps>(
  ({ className, hover = true, delay = 0, children, ...props }, ref) => {
    return (
      <motion.div
        ref={ref}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay, duration: 0.3 }}
        whileHover={hover ? { y: -2, transition: { duration: 0.2 } } : undefined}
        className={cn(
          "rounded-xl border border-white/8",
          "bg-[rgba(18,18,23,0.6)] backdrop-blur-md",
          "shadow-lg shadow-black/20",
          hover && "transition-shadow duration-300 hover:shadow-xl hover:shadow-emerald-500/10",
          className
        )}
        {...props}
      >
        {children}
      </motion.div>
    )
  }
)
FloatingCard.displayName = "FloatingCard"
