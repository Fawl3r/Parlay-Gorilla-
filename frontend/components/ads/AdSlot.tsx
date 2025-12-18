"use client"

import { useEffect, useRef } from "react"
import { cn } from "@/lib/utils"
import { AD_SIZE_CLASSES, AD_SIZE_CONFIG, type AdSlotSize } from "./adSizes"

declare global {
  interface Window {
    adsbygoogle?: unknown[]
  }
}

interface AdSlotProps {
  slotId: string
  className?: string
  size?: AdSlotSize
  format?: "auto" | "fixed"
  responsive?: boolean
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
  const sizeConfig = AD_SIZE_CONFIG[size]
  
  // Check if we have AdSense configured
  const adsenseClientId = process.env.NEXT_PUBLIC_ADSENSE_CLIENT_ID
  const isProduction = process.env.NODE_ENV === "production"
  
  useEffect(() => {
    // Only attempt to load ads in production with valid AdSense ID
    if (isProduction && adsenseClientId && adRef.current) {
      try {
        // Push ad to AdSense
        const adsbygoogle = window.adsbygoogle || []
        adsbygoogle.push({})
        window.adsbygoogle = adsbygoogle
      } catch (error) {
        console.error("AdSense error:", error)
      }
    }
  }, [isProduction, adsenseClientId])

  // Show real ads in production with AdSense configured
  if (isProduction && adsenseClientId) {
    return (
      <div 
        ref={adRef}
        className={cn(
          "overflow-hidden",
          AD_SIZE_CLASSES[size],
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
        AD_SIZE_CLASSES[size],
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
