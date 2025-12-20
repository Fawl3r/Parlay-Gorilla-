import type { UsStateCode } from "./UsState"

export type GeoSource = "override" | "api" | "ipapi" | "unknown"

export interface GeoLocation {
  countryCode: string | null
  regionCode: UsStateCode | null
  source: GeoSource
}


