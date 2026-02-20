"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { GlassPanel } from "./glass-panel"

export interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Stronger blur/background for emphasis */
  variant?: "default" | "strong"
}

/**
 * Premium panel for builder sections: glass style, rounded-2xl, border, subtle shadow.
 * Use for Sport picker, Risk slider, Filters, Strategy rules, Preview.
 */
export const GlassCard = React.forwardRef<HTMLDivElement, GlassCardProps>(
  ({ className, variant = "default", children, ...props }, ref) => {
    return (
      <GlassPanel
        ref={ref}
        variant={variant === "strong" ? "strong" : "default"}
        className={cn("rounded-2xl border-white/10 shadow-lg shadow-black/20 p-4 sm:p-5", className)}
        {...props}
      >
        {children}
      </GlassPanel>
    )
  }
)
GlassCard.displayName = "GlassCard"
