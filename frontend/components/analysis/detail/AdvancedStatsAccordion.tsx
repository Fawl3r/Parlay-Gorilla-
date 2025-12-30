"use client"

import { cn } from "@/lib/utils"

export type AdvancedStatsAccordionProps = {
  title?: string
  description?: string
  children: React.ReactNode
  className?: string
}

export function AdvancedStatsAccordion({
  title = "Deeper stats",
  description = "For advanced users",
  children,
  className,
}: AdvancedStatsAccordionProps) {
  return (
    <details className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm p-5", className)}>
      <summary className="cursor-pointer select-none">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-sm font-extrabold text-white">{title}</div>
            <div className="text-xs text-white/60">{description}</div>
          </div>
          <div className="text-xs text-white/50">Tap to expand</div>
        </div>
      </summary>
      <div className="mt-4">{children}</div>
    </details>
  )
}


