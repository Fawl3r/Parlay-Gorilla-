import type { AdSlotSize } from "@/components/ads/adSizes"
import type { UsStateCode } from "@/lib/geo/UsState"
import type { SportsbookAffiliateOffer } from "./SportsbookAffiliateOffer"

export interface SportsbookOfferSelectionContext {
  slotId: string
  size: AdSlotSize
  state: UsStateCode
}

export class SportsbookAffiliateOfferSelector {
  private readonly offers: readonly SportsbookAffiliateOffer[]

  public constructor(offers: readonly SportsbookAffiliateOffer[]) {
    this.offers = offers
  }

  public select(ctx: SportsbookOfferSelectionContext): SportsbookAffiliateOffer | null {
    const eligible = this.offers.filter((o) => this.isEligible(o, ctx))
    if (eligible.length === 0) return null
    if (eligible.length === 1) return eligible[0]

    const dateKey = new Date().toISOString().slice(0, 10) // UTC day rotation
    const hashSeed = `${ctx.slotId}:${ctx.size}:${ctx.state}:${dateKey}`
    const pick = this.pickWeightedIndex(hashSeed, eligible)
    return eligible[pick] || eligible[0]
  }

  private isEligible(offer: SportsbookAffiliateOffer, ctx: SportsbookOfferSelectionContext): boolean {
    if (!offer.affiliateUrl) return false

    // If the offer provides per-size creatives, require a creative for this size.
    // If no creatives are provided, we render a text-based creative.
    if (offer.creatives && Object.keys(offer.creatives).length > 0) {
      const creative = offer.creatives[ctx.size]
      if (!creative) return false
    }

    if (offer.allowedStates && offer.allowedStates.length > 0) {
      return offer.allowedStates.includes(ctx.state)
    }

    return true
  }

  private pickWeightedIndex(seed: string, eligible: readonly SportsbookAffiliateOffer[]): number {
    const weights = eligible.map((o) =>
      typeof o.weight === "number" && o.weight > 0 ? Math.max(1, Math.round(o.weight)) : 1
    )
    const total = weights.reduce((sum, w) => sum + w, 0)
    if (total <= 0) return 0

    const n = this.fnv1a32(seed)
    const target = n % total
    let acc = 0
    for (let i = 0; i < eligible.length; i++) {
      acc += weights[i]
      if (target < acc) return i
    }
    return 0
  }

  /**
   * Deterministic 32-bit FNV-1a hash.
   */
  private fnv1a32(input: string): number {
    let hash = 0x811c9dc5
    for (let i = 0; i < input.length; i++) {
      hash ^= input.charCodeAt(i)
      hash = Math.imul(hash, 0x01000193)
    }
    // Convert to unsigned 32-bit
    return hash >>> 0
  }
}


