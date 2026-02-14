export type SportsListItem = {
  slug: string
  in_season?: boolean
  status_label?: string
  sport_state?: string
  next_game_at?: string | null
  /** If false, tab is disabled and parlay builder cannot select this sport. */
  is_enabled?: boolean
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
    // Keep in sync with backend sports_config (HIDDEN_SPORT_SLUGS, COMING_SOON_SPORT_SLUGS). Backend owns visibility; frontend only filters display and derives isEnabled from API.
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
    const isEnabled =
      typeof sport?.is_enabled === "boolean" ? sport.is_enabled : (sport?.in_season !== false)
    // isInSeason is aligned with "can interact" (isEnabled). For labels/badges use sport_state/statusLabel.
    const inSeason = !comingSoon && isEnabled

    let statusLabelRaw = comingSoon
      ? "Coming Soon"
      : sport?.status_label || (isEnabled ? "In season" : "Not in season")

    if (!comingSoon && sport?.next_game_at && (sport?.sport_state === "OFFSEASON" || sport?.sport_state === "IN_BREAK" || sport?.sport_state === "PRESEASON" || sport?.sport_state === "POSTSEASON")) {
      try {
        const next = new Date(sport.next_game_at)
        if (!Number.isNaN(next.getTime())) {
          const days = Math.ceil((next.getTime() - Date.now()) / (24 * 60 * 60 * 1000))
          if (sport?.sport_state === "IN_BREAK") {
            statusLabelRaw = `Break — next game ${next.toLocaleDateString()}`
          } else if (sport?.sport_state === "PRESEASON") {
            statusLabelRaw = `Preseason — starts ${next.toLocaleDateString()}`
          } else if (sport?.sport_state === "POSTSEASON") {
            statusLabelRaw = `Postseason — next game ${next.toLocaleDateString()}`
          } else if (days > 0) {
            statusLabelRaw = `Offseason — returns ${next.toLocaleDateString()}`
          }
        }
      } catch {
        // keep statusLabelRaw as-is
      }
    }

    const statusLabel = String(statusLabelRaw || "").trim() || (isEnabled ? "In season" : "Not in season")

    return {
      isAvailable: isEnabled && !comingSoon,
      isComingSoon: comingSoon || statusLabel.toLowerCase() === "coming soon",
      isInSeason: inSeason,
      statusLabel,
    }
  }
}

export const sportsUiPolicy = SportsUiPolicy.default()


