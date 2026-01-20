"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { Info } from "lucide-react"
import { cn } from "@/lib/utils"

export interface InfoBadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "subtle" | "strong"
  interactive?: boolean
}

export const InfoBadge = React.forwardRef<HTMLDivElement, InfoBadgeProps>(
  ({ className, variant = "default", interactive = false, children, ...props }, ref) => {
    const variantClasses = {
      default: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
      subtle: "bg-white/5 text-white/60 border-white/10",
      strong: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
    }

    return (
      <motion.div
        ref={ref}
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        whileHover={interactive ? { scale: 1.05 } : undefined}
        className={cn(
          "inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm font-medium",
          variantClasses[variant],
          interactive && "cursor-pointer transition-colors hover:bg-emerald-500/15",
          className
        )}
        {...props}
      >
        <Info className="w-4 h-4 shrink-0" />
        <span>{children}</span>
      </motion.div>
    )
  }
)
InfoBadge.displayName = "InfoBadge"
