"use client"

import Link from "next/link"
import Image from "next/image"
import { useEffect, useMemo, useState } from "react"

import { cn } from "@/lib/utils"
import { useSubscription } from "@/lib/subscription-context"
import { trackEvent } from "@/lib/track-event"
import { useGeoLocation } from "@/lib/geo/useGeoLocation"
import { isOnlineSportsBettingState } from "@/lib/geo/UsOnlineSportsBettingStates"
import type { UsStateCode } from "@/lib/geo/UsState"

import { AdSlot, InArticleAd } from "./AdSlot"
import { AD_SIZE_CLASSES, type AdSlotSize } from "./adSizes"
import { getSportsbookAffiliateOffers } from "@/lib/ads/sportsbooks/SportsbookAffiliateOffers"
import { SportsbookAffiliateOfferSelector } from "@/lib/ads/sportsbooks/SportsbookAffiliateOfferSelector"
import type { SportsbookAffiliateOffer } from "@/lib/ads/sportsbooks/SportsbookAffiliateOffer"

interface SportsbookAdSlotProps {
  slotId: string
  className?: string
  size?: AdSlotSize
}

function buildTrackedUrl(baseUrl: string, params: Record<string, string>): string {
  try {
    const url = new URL(baseUrl)
    for (const [k, v] of Object.entries(params)) {
      if (!url.searchParams.has(k)) url.searchParams.set(k, v)
    }
    return url.toString()
  } catch {
    return baseUrl
  }
}

function SportsbookAffiliateAdCreative({
  offer,
  slotId,
  size,
  state,
  className,
}: {
  offer: SportsbookAffiliateOffer
  slotId: string
  size: AdSlotSize
  state: UsStateCode
  className?: string
}) {
  const creative = offer.creatives?.[size]
  const [imageFailed, setImageFailed] = useState(false)

  useEffect(() => {
    setImageFailed(false)
  }, [creative?.imageSrc])

  const href = useMemo(
    () =>
      buildTrackedUrl(offer.affiliateUrl, {
        utm_source: "parlaygorilla",
        utm_medium: "affiliate",
        utm_campaign: slotId,
        utm_content: offer.id,
        utm_term: state,
      }),
    [offer.affiliateUrl, offer.id, slotId, state]
  )

  const isCompact = size === "banner" || size === "leaderboard" || size === "mobile-banner"
  const showFooter = !isCompact
  const hasImage = Boolean(creative?.imageSrc) && !imageFailed

  if (hasImage && creative?.imageSrc) {
    return (
      <div
        className={cn(
          "overflow-hidden rounded-lg border border-emerald-500/25 bg-black/30",
          "shadow-lg shadow-black/30",
          AD_SIZE_CLASSES[size],
          className
        )}
      >
        <a
          href={href}
          target="_blank"
          rel="sponsored nofollow noopener noreferrer"
          onClick={() => {
            trackEvent("click_sportsbook_affiliate", {
              sportsbook: offer.id,
              sportsbook_name: offer.displayName,
              slot_id: slotId,
              state,
            })
          }}
          className="relative block w-full h-full"
          aria-label={`Advertisement: ${offer.displayName} (opens in a new tab)`}
        >
          <Image
            src={creative.imageSrc}
            alt={creative.imageAlt || `${offer.displayName} sportsbook offer`}
            fill
            sizes={size === "leaderboard" ? "(min-width: 768px) 728px, 320px" : "100vw"}
            className="object-cover"
            onError={() => setImageFailed(true)}
            priority={false}
          />

          <div className="absolute left-2 top-2 rounded-md bg-black/70 px-2 py-1 text-[10px] font-semibold text-gray-200 backdrop-blur-sm">
            Ad • 21+
          </div>
        </a>
      </div>
    )
  }

  return (
    <div
      className={cn(
        "overflow-hidden rounded-lg border border-emerald-500/25 bg-black/30 backdrop-blur-sm",
        "shadow-lg shadow-black/30",
        AD_SIZE_CLASSES[size],
        className
      )}
    >
      <div className="flex h-full flex-col">
        <a
          href={href}
          target="_blank"
          rel="sponsored nofollow noopener noreferrer"
          onClick={() => {
            trackEvent("click_sportsbook_affiliate", {
              sportsbook: offer.id,
              sportsbook_name: offer.displayName,
              slot_id: slotId,
              state,
            })
          }}
          className={cn(
            "flex-1 w-full h-full",
            isCompact
              ? "flex items-center justify-between px-4 py-2"
              : "flex flex-col justify-between p-4"
          )}
          aria-label={`Advertisement: ${offer.displayName} (opens in a new tab)`}
        >
          <div className={cn(isCompact ? "min-w-0" : "")}>
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase tracking-wider text-gray-400">Advertisement</span>
              <span className="text-[10px] text-gray-500">•</span>
              <span className="text-[10px] uppercase tracking-wider text-gray-400">21+</span>
            </div>
            <div className={cn("font-black text-white", isCompact ? "text-sm md:text-base truncate" : "text-xl")}>
              {offer.displayName}
            </div>
            <div className={cn("text-xs text-gray-400", isCompact ? "truncate" : "mt-1")}>
              {isCompact ? `Available in ${state}` : `Available in ${state} • New users in eligible states`}
            </div>
          </div>

          <div className={cn(isCompact ? "ml-3 flex-shrink-0" : "mt-3")}>
            <span
              className={cn(
                "inline-flex items-center justify-center rounded-lg font-bold",
                "bg-emerald-500 text-black hover:bg-emerald-400 transition-colors",
                isCompact ? "px-3 py-2 text-xs" : "px-4 py-2.5 text-sm"
              )}
            >
              Claim Offer
            </span>
          </div>
        </a>

        {showFooter ? (
          <div className="px-4 pb-3">
            <div className="text-[11px] text-gray-400 leading-snug">
              Must be 21+. Terms may apply.{" "}
              <Link href="/responsible-gaming" className="text-emerald-300 hover:underline">
                Gamble responsibly
              </Link>
              .
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}

function shouldUseSportsbookAffiliates(): boolean {
  return process.env.NEXT_PUBLIC_SPORTSBOOK_AFFILIATE_ADS_ENABLED === "true"
}

export function SportsbookAdSlot({ slotId, className, size = "banner" }: SportsbookAdSlotProps) {
  const { isPremium } = useSubscription()
  const { geo, loading } = useGeoLocation()
  const offers = useMemo(() => getSportsbookAffiliateOffers(), [])
  const selector = useMemo(() => new SportsbookAffiliateOfferSelector(offers), [offers])

  // Premium users should be ad-free across the product.
  if (isPremium) return null

  // If affiliate ads aren't enabled, fall back to the existing AdSense/placeholder logic.
  if (!shouldUseSportsbookAffiliates()) {
    return <AdSlot slotId={slotId} size={size} className={className} />
  }

  // Wait for geo so we don't accidentally show offers in unknown states.
  if (loading) {
    return <AdSlot slotId={slotId} size={size} className={className} />
  }

  if (geo.countryCode !== "US" || !geo.regionCode) {
    return <AdSlot slotId={slotId} size={size} className={className} />
  }

  const state = geo.regionCode
  if (!isOnlineSportsBettingState(state)) {
    return <AdSlot slotId={slotId} size={size} className={className} />
  }

  const offer = selector.select({ slotId, size, state })

  if (!offer) {
    return <AdSlot slotId={slotId} size={size} className={className} />
  }

  return <SportsbookAffiliateAdCreative offer={offer} slotId={slotId} size={size} state={state} className={className} />
}

export function SportsbookInArticleAd({ slotId, className }: { slotId: string; className?: string }) {
  // For affiliate, we render a fixed rectangle that blends into content.
  // If affiliates are disabled or geo is unknown, fall back to the existing InArticleAd.
  if (!shouldUseSportsbookAffiliates()) {
    return <InArticleAd slotId={slotId} className={className} />
  }

  return <SportsbookAdSlot slotId={slotId} size="rectangle" className={cn("my-6", className)} />
}

export function SportsbookStickyAd({ slotId, className }: { slotId: string; className?: string }) {
  return (
    <div className={cn("sticky top-24", className)}>
      <SportsbookAdSlot slotId={slotId} size="sidebar" />
    </div>
  )
}


