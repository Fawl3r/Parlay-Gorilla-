import type { UgieSignal, UgieV2 } from "@/lib/api"

const MAX_TOP_FACTORS = 6
const MAX_EDGE_LEN = 200
const MAX_WHY_LEN = 500
const DQ_MISSING_SHOW = 5

function dedupeStrings(items: string[], maxLen: number): string[] {
  const seen = new Set<string>()
  const out: string[] = []
  for (const s of items) {
    const t = String(s ?? "").trim().slice(0, maxLen)
    if (!t || seen.has(t)) continue
    seen.add(t)
    out.push(t)
    if (out.length >= MAX_TOP_FACTORS) break
  }
  return out
}

function truncate(s: string, len: number): string {
  const t = String(s ?? "").trim()
  if (t.length <= len) return t
  return t.slice(0, len).trim() + "…"
}

function toPct(value: number): number {
  if (!Number.isFinite(value)) return 0
  return Math.max(0, Math.min(100, Math.round(value * 100)))
}

export type UgieModulesViewModel = {
  topFactors: string[]
  availability: { signals: UgieSignal[]; whySummary: string } | null
  efficiency: { signals: UgieSignal[]; whySummary: string } | null
  matchupMismatches: { whySummary: string; topEdges: string[] } | null
  gameScript: { whySummary: string; stabilityScore: number; stabilityConfidence: number } | null
  marketEdge: {
    whySummary: string
    signals: UgieSignal[]
    marketSnapshot: Record<string, unknown>
  } | null
  confidenceRisk: {
    confidencePercent: number
    riskLevel: string
    dataQualityStatus: string
    disclaimer?: string
  }
  weather: {
    why: string
    modifiers: { efficiency: number; volatility: number; confidence: number }
    rulesFired: string[]
    isMissingWarning?: boolean
  } | null
  dataQualityNotice: {
    status: string
    missing: string[]
    missingMore: number
    provider: string
    stale: string[]
  } | null
  /** For "Fetching roster…" badge when roster not ready */
  rosterStatus: "ready" | "stale" | "missing" | undefined
  /** For injury data badge when injuries not ready */
  injuriesStatus: "ready" | "stale" | "missing" | undefined
}

const WEATHER_SPORTS = new Set(["nfl", "mlb", "mls", "epl", "laliga", "ucl", "soccer"])

function isMeaningfulWeatherRule(rules: string[]): boolean {
  if (!rules?.length) return false
  const only = rules.filter(
    (r) => r !== "weather_missing" && !r.toLowerCase().includes("indoor") && !r.toLowerCase().includes("dome")
  )
  return only.length > 0
}

export function buildUgieModulesViewModel(params: { ugie: UgieV2; sport: string }): UgieModulesViewModel {
  const { ugie, sport } = params
  const pillars = ugie.pillars ?? {}
  const sportLower = String(sport ?? "").toLowerCase().trim()

  const topEdgesFromPillars: string[] = []
  for (const key of ["availability", "efficiency", "matchup_fit"] as const) {
    const p = pillars[key]
    if (p?.top_edges) topEdgesFromPillars.push(...p.top_edges)
  }
  const topFactors = dedupeStrings(topEdgesFromPillars, MAX_EDGE_LEN)

  // Only show Availability when we have real injury signals; hide "Unable to assess" placeholder
  const availabilityPillar = pillars.availability
  const whySummary = (availabilityPillar?.why_summary ?? "").trim()
  const isUnableToAssessPlaceholder =
    whySummary.length > 0 &&
    whySummary.toLowerCase().includes("unable to assess injury impact") &&
    (availabilityPillar?.signals?.length ?? 0) === 0
  const availability =
    !isUnableToAssessPlaceholder &&
    (availabilityPillar?.signals?.length ?? 0) > 0
      ? {
          signals: availabilityPillar!.signals!,
          whySummary: truncate(whySummary, MAX_WHY_LEN),
        }
      : null

  const efficiencyPillar = pillars.efficiency
  const efficiency =
    (efficiencyPillar?.signals?.length ?? 0) > 0
      ? {
          signals: efficiencyPillar!.signals!,
          whySummary: truncate(efficiencyPillar!.why_summary ?? "", MAX_WHY_LEN),
        }
      : null

  const matchupPillar = pillars.matchup_fit
  const matchupMismatches =
    matchupPillar && (matchupPillar.why_summary || (matchupPillar.top_edges?.length ?? 0) > 0)
      ? {
          whySummary: truncate(matchupPillar.why_summary ?? "", MAX_WHY_LEN),
          topEdges: (matchupPillar.top_edges ?? []).slice(0, 10).map((s) => truncate(String(s), MAX_EDGE_LEN)),
        }
      : null

  const scriptPillar = pillars.script_stability
  const gameScript =
    scriptPillar != null
      ? {
          whySummary: truncate(scriptPillar.why_summary ?? "", MAX_WHY_LEN),
          stabilityScore: Number(scriptPillar.score) ?? 0.5,
          stabilityConfidence: Number(scriptPillar.confidence) ?? 0,
        }
      : null

  const marketPillar = pillars.market_alignment
  const marketSnapshot = ugie.market_snapshot && typeof ugie.market_snapshot === "object" ? ugie.market_snapshot : {}
  const marketEdge = {
    whySummary: truncate(marketPillar?.why_summary ?? "", MAX_WHY_LEN),
    signals: marketPillar?.signals ?? [],
    marketSnapshot: marketSnapshot as Record<string, unknown>,
  }

  const dq = ugie.data_quality ?? { status: "Partial" as const, missing: [], stale: [], provider: "" }
  const confidencePercent = toPct(ugie.confidence_score ?? 0.5)
  const riskLevel = ugie.risk_level ?? "Medium"
  const dataQualityStatus = dq.status ?? "Partial"
  const disclaimer =
    dataQualityStatus !== "Good"
      ? "Limited data available for this event — model confidence reduced."
      : undefined

  const confidenceRisk: UgieModulesViewModel["confidenceRisk"] = {
    confidencePercent,
    riskLevel,
    dataQualityStatus,
    disclaimer,
  }

  let weather: UgieModulesViewModel["weather"] = null
  const weatherBlock = ugie.weather
  if (weatherBlock && WEATHER_SPORTS.has(sportLower)) {
    const rules = weatherBlock.rules_fired ?? []
    const isMissingWarning = rules.includes("weather_missing")
    const meaningful = isMeaningfulWeatherRule(rules)
    if (meaningful || isMissingWarning) {
      weather = {
        why: truncate(weatherBlock.why ?? (isMissingWarning ? "Weather data missing — confidence slightly reduced." : ""), MAX_WHY_LEN),
        modifiers: {
          efficiency: Number(weatherBlock.weather_efficiency_modifier) ?? 1,
          volatility: Number(weatherBlock.weather_volatility_modifier) ?? 1,
          confidence: Number(weatherBlock.weather_confidence_modifier) ?? 1,
        },
        rulesFired: rules,
        isMissingWarning,
      }
    }
  }

  const missingList = dq.missing ?? []
  const missingShow = missingList.slice(0, DQ_MISSING_SHOW)
  const missingMore = Math.max(0, missingList.length - DQ_MISSING_SHOW)
  const dataQualityNotice: UgieModulesViewModel["dataQualityNotice"] =
    dataQualityStatus !== "Good"
      ? {
          status: dataQualityStatus,
          missing: missingShow,
          missingMore,
          provider: dq.provider ?? "",
          stale: dq.stale ?? [],
        }
      : null

  const rosterStatus = (dq as { roster?: "ready" | "stale" | "missing" }).roster
  const injuriesStatus = (dq as { injuries?: "ready" | "stale" | "missing" }).injuries

  return {
    topFactors,
    availability,
    efficiency,
    matchupMismatches,
    gameScript,
    marketEdge,
    confidenceRisk,
    weather,
    dataQualityNotice,
    rosterStatus,
    injuriesStatus,
  }
}
