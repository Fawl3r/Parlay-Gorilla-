"use client"

import { useEffect, useRef, useState } from "react"
import { cn } from "@/lib/utils"

interface AdSlotProps {
  slotId: string
  className?: string
  size?: "banner" | "leaderboard" | "rectangle" | "sidebar" | "square" | "mobile-banner"
  format?: "auto" | "fixed"
  responsive?: boolean
}

// Ad size configurations (in pixels)
const AD_SIZES = {
  banner: { width: 728, height: 90, mobileWidth: 320, mobileHeight: 50 },
  leaderboard: { width: 728, height: 90, mobileWidth: 320, mobileHeight: 100 },
  rectangle: { width: 300, height: 250, mobileWidth: 300, mobileHeight: 250 },
  sidebar: { width: 300, height: 600, mobileWidth: 300, mobileHeight: 250 },
  square: { width: 250, height: 250, mobileWidth: 250, mobileHeight: 250 },
  "mobile-banner": { width: 320, height: 50, mobileWidth: 320, mobileHeight: 50 },
}

/**
 * AdSlot Component
 * 
 * Supports Google AdSense and other ad networks.
 * In development, shows placeholder. In production, renders actual ads.
 * 
 * To enable Google AdSense:
 * 1. Add your AdSense script to the layout.tsx head
 * 2. Set NEXT_PUBLIC_ADSENSE_CLIENT_ID in .env
 * 3. Replace the slotId with your actual ad slot ID from AdSense
 */
export function AdSlot({ 
  slotId, 
  className, 
  size = "banner",
  format = "auto",
  responsive = true
}: AdSlotProps) {
  const adRef = useRef<HTMLDivElement>(null)
  const [isLoaded, setIsLoaded] = useState(false)
  const sizeConfig = AD_SIZES[size]
  
  // Check if we have AdSense configured
  const adsenseClientId = process.env.NEXT_PUBLIC_ADSENSE_CLIENT_ID
  const isProduction = process.env.NODE_ENV === "production"
  
  useEffect(() => {
    // Only attempt to load ads in production with valid AdSense ID
    if (isProduction && adsenseClientId && adRef.current) {
      try {
        // Push ad to AdSense
        const adsbygoogle = (window as any).adsbygoogle || []
        adsbygoogle.push({})
        setIsLoaded(true)
      } catch (error) {
        console.error("AdSense error:", error)
      }
    }
  }, [isProduction, adsenseClientId])

  // CSS classes for responsive sizing
  const sizeClasses = {
    banner: "h-[90px] max-w-[728px] mx-auto",
    leaderboard: "h-[90px] md:h-[90px] max-w-[728px] mx-auto",
    rectangle: "h-[250px] w-[300px] mx-auto",
    sidebar: "min-h-[250px] md:min-h-[600px] w-[300px]",
    square: "h-[250px] w-[250px] mx-auto",
    "mobile-banner": "h-[50px] w-[320px] mx-auto md:hidden",
  }

  // Show real ads in production with AdSense configured
  if (isProduction && adsenseClientId) {
    return (
      <div 
        ref={adRef}
        className={cn(
          "overflow-hidden",
          sizeClasses[size],
          className
        )}
      >
        <ins
          className="adsbygoogle"
          style={{ 
            display: "block",
            width: responsive ? "100%" : `${sizeConfig.width}px`,
            height: responsive ? "auto" : `${sizeConfig.height}px`,
          }}
          data-ad-client={adsenseClientId}
          data-ad-slot={slotId}
          data-ad-format={format}
          data-full-width-responsive={responsive ? "true" : "false"}
        />
      </div>
    )
  }

  // Development placeholder
  return (
    <div
      className={cn(
        "rounded-lg border border-dashed border-emerald-500/30 bg-emerald-500/5",
        "flex items-center justify-center",
        sizeClasses[size],
        className
      )}
    >
      <div className="text-center p-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 mb-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs font-medium text-emerald-400">AD SPACE</span>
        </div>
        <p className="text-xs text-muted-foreground font-medium">
          {size.charAt(0).toUpperCase() + size.slice(1).replace("-", " ")} • {sizeConfig.width}×{sizeConfig.height}
        </p>
        <p className="text-[10px] text-muted-foreground/60 mt-1">
          Slot: {slotId}
        </p>
      </div>
    </div>
  )
}

/**
 * InArticleAd Component
 * 
 * Native in-article ad that blends with content.
 * Best placed between paragraphs in long-form content.
 */
export function InArticleAd({ slotId, className }: { slotId: string; className?: string }) {
  const adsenseClientId = process.env.NEXT_PUBLIC_ADSENSE_CLIENT_ID
  const isProduction = process.env.NODE_ENV === "production"

  if (isProduction && adsenseClientId) {
    return (
      <div className={cn("my-6", className)}>
        <ins
          className="adsbygoogle"
          style={{ display: "block", textAlign: "center" }}
          data-ad-layout="in-article"
          data-ad-format="fluid"
          data-ad-client={adsenseClientId}
          data-ad-slot={slotId}
        />
      </div>
    )
  }

  return (
    <div className={cn(
      "my-6 py-4 px-6 rounded-lg border border-dashed border-amber-500/30 bg-amber-500/5",
      className
    )}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-amber-400">IN-ARTICLE AD</span>
        <span className="text-[10px] text-muted-foreground">Slot: {slotId}</span>
      </div>
    </div>
  )
}

/**
 * StickyAd Component
 * 
 * Sticky sidebar ad that follows scroll.
 * Best for sidebar placements on desktop.
 */
export function StickyAd({ slotId, className }: { slotId: string; className?: string }) {
  return (
    <div className={cn("sticky top-24", className)}>
      <AdSlot slotId={slotId} size="sidebar" />
    </div>
  )
}
