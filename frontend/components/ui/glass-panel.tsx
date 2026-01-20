import * as React from "react"
import { cn } from "@/lib/utils"

export interface GlassPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "strong" | "subtle"
  hover?: boolean
}

export const GlassPanel = React.forwardRef<HTMLDivElement, GlassPanelProps>(
  ({ className, variant = "default", hover = false, ...props }, ref) => {
    const variantClasses = {
      default: "bg-[rgba(18,18,23,0.6)] backdrop-blur-md",
      strong: "bg-[rgba(18,18,23,0.8)] backdrop-blur-xl",
      subtle: "bg-[rgba(18,18,23,0.4)] backdrop-blur-sm",
    }

    return (
      <div
        ref={ref}
        className={cn(
          "rounded-xl border border-white/8",
          variantClasses[variant],
          hover && "transition-all duration-300 hover:border-white/12 hover:shadow-lg hover:shadow-emerald-500/10",
          className
        )}
        {...props}
      />
    )
  }
)
GlassPanel.displayName = "GlassPanel"
