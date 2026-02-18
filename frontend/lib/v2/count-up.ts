/**
 * V2 COUNT-UP ANIMATION UTILITY
 * Lightweight number animation for stats
 */

import { useEffect, useRef, useState } from 'react'
import { prefersReducedMotion } from './motion'

interface CountUpOptions {
  start?: number
  end: number
  duration?: number
  decimals?: number
  suffix?: string
  prefix?: string
}

export function useCountUp({
  start = 0,
  end,
  duration = 600,
  decimals = 0,
  suffix = '',
  prefix = '',
}: CountUpOptions): string {
  const [count, setCount] = useState(start)
  const frameRef = useRef<number>()
  const startTimeRef = useRef<number>()

  useEffect(() => {
    // Skip animation if reduced motion
    if (prefersReducedMotion()) {
      setCount(end)
      return
    }

    const animate = (currentTime: number) => {
      if (!startTimeRef.current) {
        startTimeRef.current = currentTime
      }

      const elapsed = currentTime - startTimeRef.current
      const progress = Math.min(elapsed / duration, 1)

      // Easing function (ease-out)
      const eased = 1 - Math.pow(1 - progress, 3)
      const current = start + (end - start) * eased

      setCount(current)

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(animate)
      }
    }

    frameRef.current = requestAnimationFrame(animate)

    return () => {
      if (frameRef.current) {
        cancelAnimationFrame(frameRef.current)
      }
    }
  }, [start, end, duration])

  const formatted = count.toFixed(decimals)
  return `${prefix}${formatted}${suffix}`
}
