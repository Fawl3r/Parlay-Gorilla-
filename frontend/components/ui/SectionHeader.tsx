"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

export interface SectionHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string
  description?: string
  /** Optional right-side slot (e.g. Reset button) */
  right?: React.ReactNode
}

/**
 * Section title + description + optional right slot for builder sections.
 */
export const SectionHeader = React.forwardRef<HTMLDivElement, SectionHeaderProps>(
  ({ className, title, description, right, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("flex flex-wrap items-start justify-between gap-3 mb-3", className)}
        {...props}
      >
        <div>
          <h3 className="text-sm font-semibold text-white">{title}</h3>
          {description && <p className="text-xs text-white/60 mt-0.5">{description}</p>}
        </div>
        {right != null && <div className="shrink-0">{right}</div>}
      </div>
    )
  }
)
SectionHeader.displayName = "SectionHeader"
