"use client"

import { useState } from "react"
import { Info } from "lucide-react"
import { cn } from "@/lib/utils"

type Props = {
  label: string
  content: string
  className?: string
}

/**
 * Small info icon with hover/focus tooltip. Academic tone for authority layer.
 */
export function AuthorityTooltip({ label, content, className }: Props) {
  const [visible, setVisible] = useState(false)
  return (
    <span className={cn("inline-flex items-center gap-1", className)}>
      <span>{label}</span>
      <span className="relative inline-flex">
        <button
          type="button"
          className="text-white/45 hover:text-white/70 focus:text-white/70 focus:outline-none rounded p-0.5"
          onMouseEnter={() => setVisible(true)}
          onMouseLeave={() => setVisible(false)}
          onFocus={() => setVisible(true)}
          onBlur={() => setVisible(false)}
          aria-label={`${label}: ${content}`}
        >
          <Info className="h-3.5 w-3.5" />
        </button>
        {visible && (
          <span
            className="absolute left-0 top-full mt-1 z-50 min-w-[180px] max-w-[260px] px-2.5 py-1.5 text-[11px] leading-snug text-white/90 bg-black/90 border border-white/10 rounded shadow-xl"
            role="tooltip"
          >
            {content}
          </span>
        )}
      </span>
    </span>
  )
}
