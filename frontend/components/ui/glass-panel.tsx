import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const glassPanelVariants = cva(
  [
    "rounded-xl border ring-1 shadow-[0_12px_40px_rgba(0,0,0,0.35)]",
    // Fallback when backdrop-filter isn't supported: keep the panel more opaque for readability.
    "bg-card/90 supports-[backdrop-filter]:bg-card/70",
    "backdrop-blur-xl",
    "ring-black/5 dark:ring-white/5",
  ].join(" "),
  {
    variants: {
      tone: {
        subtle: "bg-card/85 supports-[backdrop-filter]:bg-card/60 border-black/10 dark:border-white/10",
        default: "bg-card/90 supports-[backdrop-filter]:bg-card/70 border-black/10 dark:border-white/10",
        strong: "bg-card/95 supports-[backdrop-filter]:bg-card/80 border-black/15 dark:border-white/15",
      },
      padding: {
        none: "",
        sm: "p-4",
        md: "p-6",
        lg: "p-8",
      },
    },
    defaultVariants: {
      tone: "default",
      padding: "md",
    },
  }
)

export interface GlassPanelProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof glassPanelVariants> {}

export const GlassPanel = React.forwardRef<HTMLDivElement, GlassPanelProps>(
  ({ className, tone, padding, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(glassPanelVariants({ tone, padding }), className)}
        {...props}
      />
    )
  }
)

GlassPanel.displayName = "GlassPanel"


