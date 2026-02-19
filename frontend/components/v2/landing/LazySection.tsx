'use client'

import { ReactNode, useEffect, useRef, useState } from 'react'

interface LazySectionProps {
  children: ReactNode
  /** Root margin (e.g. "0px 0px 400px 0px") so we mount only when user scrolls near */
  rootMargin?: string
  /** Placeholder height so scrollbar length is ~correct before mount */
  minHeight?: number
}

/**
 * Renders children only when the sentinel is near the viewport.
 * Keeps initial DOM/paint smaller so scroll stays fluid.
 */
export function LazySection({
  children,
  rootMargin = '0px 0px 400px 0px',
  minHeight = 800,
}: LazySectionProps) {
  const [inView, setInView] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) setInView(true)
      },
      { rootMargin, threshold: 0 }
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [rootMargin])

  if (inView) {
    return <div className="v2-page-enter">{children}</div>
  }

  return <div ref={ref} style={{ minHeight }} aria-hidden className="v2-section-defer" />
}
