export type SportsListItem = {
  slug: string
  in_season?: boolean
  status_label?: string
}

export type SportAvailability = {
  /** Whether the UI should treat the sport as currently playable/clickable */
  isAvailable: boolean
  /** Whether the sport is explicitly marked as "Coming Soon" */
  isComingSoon: boolean
  /** Whether the sport is in season (as reported by backend, unless overridden by UI policy) */
  isInSeason: boolean
  /** Human-readable label shown in UI for unavailable states */
  statusLabel: string
}

type SportsUiPolicyConfig = {
  hiddenSlugs: readonly string[]
  comingSoonSlugs: readonly string[]
}

export class SportsUiPolicy {
  private readonly hiddenSlugs: Set<string>
  private readonly comingSoonSlugs: Set<string>

  constructor(config: SportsUiPolicyConfig) {
    this.hiddenSlugs = new Set((config.hiddenSlugs || []).map((s) => String(s).toLowerCase().trim()))
    this.comingSoonSlugs = new Set((config.comingSoonSlugs || []).map((s) => String(s).toLowerCase().trim()))
  }

  static default(): SportsUiPolicy {
    // Keep in sync with backend `SportsUiPolicy.default()`.
    return new SportsUiPolicy({
      hiddenSlugs: ["ucl"],
      comingSoonSlugs: ["ufc", "boxing"],
    })
  }

  isHidden(slug: string): boolean {
    return this.hiddenSlugs.has(String(slug || "").toLowerCase().trim())
  }

  isComingSoon(slug: string): boolean {
    return this.comingSoonSlugs.has(String(slug || "").toLowerCase().trim())
  }

  filterVisible<T extends { slug: string }>(sports: readonly T[]): T[] {
    return (sports || []).filter((s) => !this.isHidden(s.slug))
  }

  resolveAvailability(sport: SportsListItem): SportAvailability {
    const slug = String(sport?.slug || "").toLowerCase().trim()
    const comingSoon = this.isComingSoon(slug)
    const inSeason = !comingSoon && sport?.in_season !== false

    const statusLabelRaw = comingSoon
      ? "Coming Soon"
      : sport?.status_label || (inSeason ? "In season" : "Not in season")

    const statusLabel = String(statusLabelRaw || "").trim() || (inSeason ? "In season" : "Not in season")

    return {
      isAvailable: inSeason,
      isComingSoon: comingSoon || statusLabel.toLowerCase() === "coming soon",
      isInSeason: inSeason,
      statusLabel,
    }
  }
}

export const sportsUiPolicy = SportsUiPolicy.default()


