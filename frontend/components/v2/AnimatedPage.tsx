/**
 * V2 Animated Page Wrapper
 * Smooth page transitions for V2 routes
 */

'use client'

import { ReactNode, useEffect, useState } from 'react'

interface AnimatedPageProps {
  children: ReactNode
}

export function AnimatedPage({ children }: AnimatedPageProps) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  return (
    <div
      className={`
        transition-all duration-[180ms]
        ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-1'}
      `}
      style={{
        transitionTimingFunction: 'cubic-bezier(0.4, 0, 0.2, 1)',
      }}
    >
      {children}
    </div>
  )
}
