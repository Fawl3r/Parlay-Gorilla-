"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"
import { GlassPanel } from "./glass-panel"

export interface SectionCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string
  description?: string
  hover?: boolean
  delay?: number
}

export const SectionCard = React.forwardRef<HTMLDivElement, SectionCardProps>(
  ({ className, title, description, hover = true, delay = 0, children, ...props }, ref) => {
    return (
      <motion.div
        ref={ref}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay, duration: 0.3 }}
        whileHover={hover ? { y: -2, transition: { duration: 0.2 } } : undefined}
      >
        <GlassPanel
          variant="default"
          hover={hover}
          className={cn("p-6", className)}
          {...props}
        >
          {(title || description) && (
            <div className="mb-4">
              {title && (
                <h3 className="text-lg font-semibold text-white mb-1">{title}</h3>
              )}
              {description && (
                <p className="text-sm text-white/60">{description}</p>
              )}
            </div>
          )}
          {children}
        </GlassPanel>
      </motion.div>
    )
  }
)
SectionCard.displayName = "SectionCard"
