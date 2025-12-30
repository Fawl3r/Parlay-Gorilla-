"use client"

import { useId, useState } from "react"
import { Info } from "lucide-react"

import { cn } from "@/lib/utils"

export type TooltipProps = {
  content: string
  className?: string
  iconClassName?: string
}

export function Tooltip({ content, className, iconClassName }: TooltipProps) {
  const id = useId()
  const [open, setOpen] = useState(false)
  const safe = String(content || "").trim()
  if (!safe) return null

  return (
    <span className={cn("relative inline-flex items-center", className)}>
      <button
        type="button"
        aria-label="More info"
        aria-describedby={id}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        className={cn(
          "inline-flex items-center justify-center rounded-full",
          "h-6 w-6",
          "border border-white/10 bg-black/30 text-white/70 hover:text-white hover:bg-black/40",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/50"
        )}
      >
        <Info className={cn("h-4 w-4", iconClassName)} />
      </button>
      <span
        id={id}
        role="tooltip"
        className={cn(
          "absolute left-0 top-full mt-2 z-50 w-64",
          "rounded-xl border border-white/10 bg-black/90 text-white/90 shadow-lg",
          "px-3 py-2 text-xs leading-5",
          open ? "block" : "hidden"
        )}
      >
        {safe}
      </span>
    </span>
  )
}


