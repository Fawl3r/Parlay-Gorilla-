/**
 * V2 Count-Up Stat — renders a single animated number
 */

'use client'

import { useCountUp } from '@/lib/v2/count-up'

interface CountUpStatProps {
  end: number
  duration?: number
  decimals?: number
  prefix?: string
  suffix?: string
  className?: string
}

export function CountUpStat({
  end,
  duration = 700,
  decimals = 0,
  prefix = '',
  suffix = '',
  className = '',
}: CountUpStatProps) {
  const value = useCountUp({ end, duration, decimals, prefix, suffix })
  return <span className={className}>{value}</span>
}
