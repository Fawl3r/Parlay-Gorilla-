"use client"

import { ReactNode, useEffect, useMemo, useRef, useState } from "react"
import { ChevronLeft, ChevronRight } from "lucide-react"

import { cn } from "@/lib/utils"
import { HorizontalOverflowIndicatorManager, HorizontalOverflowIndicators } from "@/lib/ui/HorizontalOverflowIndicatorManager"

type HorizontalScrollCueProps = Readonly<{
  className?: string
  scrollContainerClassName?: string
  scrollContainerProps?: Omit<React.HTMLAttributes<HTMLDivElement>, "className">
  children: ReactNode
}>

export function HorizontalScrollCue({
  className,
  scrollContainerClassName,
  scrollContainerProps,
  children,
}: HorizontalScrollCueProps) {
  const scrollRef = useRef<HTMLDivElement | null>(null)
  const [indicators, setIndicators] = useState<HorizontalOverflowIndicators>({
    canScrollLeft: false,
    canScrollRight: false,
  })

  const updateIndicators = useMemo(() => {
    let rafId: number | null = null

    const run = () => {
      const el = scrollRef.current
      if (!el) return

      const next = HorizontalOverflowIndicatorManager.compute({
        scrollLeft: el.scrollLeft,
        clientWidth: el.clientWidth,
        scrollWidth: el.scrollWidth,
      })

      setIndicators((prev) =>
        prev.canScrollLeft === next.canScrollLeft && prev.canScrollRight === next.canScrollRight ? prev : next
      )
    }

    return () => {
      if (rafId != null) cancelAnimationFrame(rafId)
      rafId = requestAnimationFrame(run)
    }
  }, [])

  useEffect(() => {
    const el = scrollRef.current
    if (!el) return

    // Initial measurement (after layout).
    updateIndicators()

    // Update on scroll.
    const handleScroll = () => updateIndicators()
    el.addEventListener("scroll", handleScroll, { passive: true })

    // Update on resize (content width can change across breakpoints).
    const handleResize = () => updateIndicators()
    window.addEventListener("resize", handleResize, { passive: true })

    // Update when the container is resized (e.g. layout changes).
    const observer = "ResizeObserver" in window ? new ResizeObserver(() => updateIndicators()) : null
    observer?.observe(el)

    return () => {
      el.removeEventListener("scroll", handleScroll)
      window.removeEventListener("resize", handleResize)
      observer?.disconnect()
    }
  }, [updateIndicators])

  return (
    <div className={cn("relative", className)}>
      <div
        ref={scrollRef}
        className={cn("overflow-x-auto scrollbar-hide", scrollContainerClassName)}
        {...scrollContainerProps}
      >
        {children}
      </div>

      {/* Left cue */}
      {indicators.canScrollLeft ? (
        <div
          aria-hidden="true"
          className="pointer-events-none absolute left-0 top-0 bottom-0 w-10 bg-gradient-to-r from-black/70 to-transparent flex items-center justify-start pl-1"
        >
          <ChevronLeft className="h-5 w-5 text-gray-200/80 drop-shadow" />
        </div>
      ) : null}

      {/* Right cue */}
      {indicators.canScrollRight ? (
        <div
          aria-hidden="true"
          className="pointer-events-none absolute right-0 top-0 bottom-0 w-10 bg-gradient-to-l from-black/70 to-transparent flex items-center justify-end pr-1"
        >
          <ChevronRight className="h-5 w-5 text-gray-200/80 drop-shadow" />
        </div>
      ) : null}
    </div>
  )
}


