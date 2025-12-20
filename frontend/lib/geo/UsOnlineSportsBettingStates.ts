import { isUsStateCode, normalizeUsStateCode, type UsStateCode } from "./UsState"

/**
 * US jurisdictions where statewide online/mobile sports betting is generally available.
 *
 * IMPORTANT:
 * - Sports betting laws and availability change frequently.
 * - Some states have "retail-only" betting, on-premise mobile-only betting, or limited operator availability.
 * - Treat this list as a conservative default and update as needed for compliance.
 */
export const US_ONLINE_SPORTS_BETTING_STATE_CODES: readonly UsStateCode[] = [
  "AZ",
  "AR",
  "CO",
  "CT",
  "DC",
  "DE",
  "FL",
  "IL",
  "IN",
  "IA",
  "KS",
  "KY",
  "LA",
  "ME",
  "MD",
  "MA",
  "MI",
  "NH",
  "NJ",
  "NY",
  "NC",
  "NV",
  "OH",
  "OR",
  "PA",
  "RI",
  "TN",
  "VT",
  "VA",
  "WV",
  "WY",
]

function parseOverrideStates(raw: string | undefined): readonly UsStateCode[] | null {
  if (!raw) return null
  const parts = raw
    .split(/[,\s]+/g)
    .map((p) => normalizeUsStateCode(p))
    .filter((p): p is UsStateCode => isUsStateCode(p))
  return parts.length > 0 ? parts : null
}

export function isOnlineSportsBettingState(code: UsStateCode): boolean {
  const override = parseOverrideStates(process.env.NEXT_PUBLIC_ONLINE_SPORTS_BETTING_STATES)
  return (override || US_ONLINE_SPORTS_BETTING_STATE_CODES).includes(code)
}


