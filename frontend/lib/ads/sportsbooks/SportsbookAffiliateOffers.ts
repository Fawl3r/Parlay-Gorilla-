import type { AdSlotSize } from "@/components/ads/adSizes"
import type { SportsbookAffiliateOffer, SportsbookAffiliateCreative } from "./SportsbookAffiliateOffer"
import { isUsStateCode, normalizeUsStateCode, type UsStateCode } from "@/lib/geo/UsState"

function normalizeAffiliateUrl(url: string | undefined): string {
  if (!url) return ""
  const trimmed = url.trim()
  return trimmed
}

function buildDefaultCreatives(id: string, displayName: string): Partial<Record<AdSlotSize, SportsbookAffiliateCreative>> {
  // Drop partner-approved creatives in:
  //   frontend/public/ads/sportsbooks/<id>/{banner,leaderboard,rectangle,sidebar,square,mobile-banner}.png
  // If an image is missing, the UI will automatically fall back to a text creative.
  const base = `/ads/sportsbooks/${id}`
  const alt = `${displayName} sportsbook offer`
  return {
    banner: { imageSrc: `${base}/banner.png`, imageAlt: alt },
    leaderboard: { imageSrc: `${base}/leaderboard.png`, imageAlt: alt },
    rectangle: { imageSrc: `${base}/rectangle.png`, imageAlt: alt },
    sidebar: { imageSrc: `${base}/sidebar.png`, imageAlt: alt },
    square: { imageSrc: `${base}/square.png`, imageAlt: alt },
    "mobile-banner": { imageSrc: `${base}/mobile-banner.png`, imageAlt: alt },
  }
}

function parseAllowedStatesMap(raw: string | undefined): Partial<Record<string, readonly UsStateCode[]>> {
  if (!raw) return {}
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>
    if (!parsed || typeof parsed !== "object") return {}

    const out: Record<string, UsStateCode[]> = {}
    for (const [key, value] of Object.entries(parsed)) {
      if (!Array.isArray(value)) continue
      const states: UsStateCode[] = []
      for (const item of value) {
        if (typeof item !== "string") continue
        const normalized = normalizeUsStateCode(item)
        if (isUsStateCode(normalized)) states.push(normalized)
      }
      if (states.length > 0) out[key] = states
    }
    return out
  } catch {
    return {}
  }
}

/**
 * Sportsbook affiliate configuration
 *
 * Set the URLs in `.env.local` (or your hosting provider env vars).
 * If a URL is blank, that sportsbook is treated as disabled.
 */
export function getSportsbookAffiliateOffers(): SportsbookAffiliateOffer[] {
  const betmgmUrl = normalizeAffiliateUrl(process.env.NEXT_PUBLIC_BETMGM_AFFILIATE_URL)
  const caesarsUrl = normalizeAffiliateUrl(process.env.NEXT_PUBLIC_CAESARS_AFFILIATE_URL)
  const bet365Url = normalizeAffiliateUrl(process.env.NEXT_PUBLIC_BET365_AFFILIATE_URL)
  const fanduelUrl = normalizeAffiliateUrl(process.env.NEXT_PUBLIC_FANDUEL_AFFILIATE_URL)
  const fanaticsUrl = normalizeAffiliateUrl(process.env.NEXT_PUBLIC_FANATICS_AFFILIATE_URL)
  const draftkingsUrl = normalizeAffiliateUrl(process.env.NEXT_PUBLIC_DRAFTKINGS_AFFILIATE_URL)
  const betriversUrl = normalizeAffiliateUrl(process.env.NEXT_PUBLIC_BETRIVERS_AFFILIATE_URL)

  const allowedStatesBySportsbook = parseAllowedStatesMap(process.env.NEXT_PUBLIC_SPORTSBOOK_ALLOWED_STATES_JSON)

  const offers: SportsbookAffiliateOffer[] = [
    {
      id: "betmgm",
      displayName: "BetMGM",
      affiliateUrl: betmgmUrl,
      weight: 1,
      creatives: buildDefaultCreatives("betmgm", "BetMGM"),
    },
    {
      id: "caesars",
      displayName: "Caesars Sportsbook",
      affiliateUrl: caesarsUrl,
      weight: 1,
      creatives: buildDefaultCreatives("caesars", "Caesars Sportsbook"),
    },
    {
      id: "bet365",
      displayName: "bet365",
      affiliateUrl: bet365Url,
      weight: 1,
      creatives: buildDefaultCreatives("bet365", "bet365"),
    },
    {
      id: "fanduel",
      displayName: "FanDuel Sportsbook",
      affiliateUrl: fanduelUrl,
      weight: 1,
      creatives: buildDefaultCreatives("fanduel", "FanDuel Sportsbook"),
    },
    {
      id: "fanatics",
      displayName: "Fanatics Sportsbook",
      affiliateUrl: fanaticsUrl,
      weight: 1,
      creatives: buildDefaultCreatives("fanatics", "Fanatics Sportsbook"),
    },
    {
      id: "draftkings",
      displayName: "DraftKings Sportsbook",
      affiliateUrl: draftkingsUrl,
      weight: 1,
      creatives: buildDefaultCreatives("draftkings", "DraftKings Sportsbook"),
    },
    {
      id: "betrivers",
      displayName: "BetRivers Sportsbook",
      affiliateUrl: betriversUrl,
      weight: 1,
      creatives: buildDefaultCreatives("betrivers", "BetRivers Sportsbook"),
    },
  ]

  return offers
    .filter((o) => Boolean(o.affiliateUrl))
    .map((o) => {
      const allowed = allowedStatesBySportsbook[o.id]
      return allowed ? { ...o, allowedStates: allowed } : o
    })
}


