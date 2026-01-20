"use client"

import { Tooltip } from "./tooltip"
import { getCopy } from "@/lib/content"

interface ConfidenceScoreTooltipProps {
  className?: string
  iconClassName?: string
}

export function ConfidenceScoreTooltip({ className, iconClassName }: ConfidenceScoreTooltipProps) {
  const content = getCopy("confidence.tooltip.explanation")
  
  return (
    <Tooltip 
      content={content}
      className={className}
      iconClassName={iconClassName}
    />
  )
}
