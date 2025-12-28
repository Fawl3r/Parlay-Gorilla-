"use client"

import { ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"

export function PricingAccordion({
  title,
  children,
  defaultOpen = false,
  className,
}: {
  title: string
  children: React.ReactNode
  defaultOpen?: boolean
  className?: string
}) {
  return (
    <details
      className={cn("group rounded-2xl border border-white/10 bg-black/25 backdrop-blur p-4", className)}
      open={defaultOpen}
    >
      <summary className="list-none cursor-pointer select-none">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-lg font-black text-white">{title}</h3>
          <ChevronDown className="h-5 w-5 text-gray-400 transition-transform group-open:rotate-180" />
        </div>
        <div className="mt-1 text-sm text-gray-200/70">Tap to expand</div>
      </summary>
      <div className="mt-4 text-sm text-gray-200/80">{children}</div>
    </details>
  )
}


