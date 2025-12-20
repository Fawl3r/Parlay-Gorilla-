import type { AdSlotSize } from "@/components/ads/adSizes"
import type { UsStateCode } from "@/lib/geo/UsState"

export type SportsbookId =
  | "betmgm"
  | "caesars"
  | "bet365"
  | "fanduel"
  | "fanatics"
  | "draftkings"
  | "betrivers"

export interface SportsbookAffiliateCreative {
  /**
   * Optional image creative (must be partner-approved).
   * If omitted, we render a text-based creative.
   */
  imageSrc?: string
  imageAlt?: string
}

export interface SportsbookAffiliateOffer {
  id: SportsbookId
  displayName: string

  /**
   * Your affiliate tracking URL for this sportsbook (CPA/RevShare).
   * Leave blank to disable the offer.
   */
  affiliateUrl: string

  /**
   * US state codes where this offer is allowed to be shown.
   * If omitted, the caller can apply a global "online betting states" filter.
   */
  allowedStates?: readonly UsStateCode[]

  /**
   * Optional per-size creatives. If none are provided, we render a text creative.
   */
  creatives?: Partial<Record<AdSlotSize, SportsbookAffiliateCreative>>

  /**
   * Optional weight for rotation (higher = shown more often).
   */
  weight?: number
}


