"use client"

import { cn } from "@/lib/utils"

export type SportBackgroundOverlay = "light" | "medium" | "strong"
export type SportBackgroundFit = "contain" | "cover" | "containThenCover"

type Props = {
  imageUrl: string
  overlay?: SportBackgroundOverlay
  fit?: SportBackgroundFit
  className?: string
}

const OVERLAYS: Record<SportBackgroundOverlay, { base: string; gradient: string }> = {
  light: {
    base: "bg-black/20",
    gradient: "from-black/25 via-transparent to-black/45",
  },
  medium: {
    base: "bg-black/30",
    gradient: "from-black/35 via-transparent to-black/60",
  },
  strong: {
    base: "bg-black/40",
    gradient: "from-black/50 via-transparent to-black/70",
  },
}

/**
 * Full-screen sport background with readability overlays.
 *
 * - Uses `contain` on mobile to avoid aggressive cropping.
 * - Uses `cover` on md+ screens to fill the viewport and avoid "small image" feel.
 */
export function SportBackground({
  imageUrl,
  overlay = "medium",
  fit = "containThenCover",
  className,
}: Props) {
  const overlayCfg = OVERLAYS[overlay]
  const fitClass =
    fit === "cover" ? "bg-cover" : fit === "contain" ? "bg-contain" : "bg-contain md:bg-cover"

  return (
    <div className={cn("fixed inset-0 z-0 bg-[#0a0a0f] pointer-events-none", className)}>
      <div
        className={cn("absolute inset-0 bg-no-repeat bg-center", fitClass)}
        style={{ backgroundImage: `url('${imageUrl}')` }}
      />
      <div className={cn("absolute inset-0", overlayCfg.base)} />
      <div className={cn("absolute inset-0 bg-gradient-to-b", overlayCfg.gradient)} />
    </div>
  )
}


