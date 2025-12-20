import { GeoLocation, type GeoSource } from "./GeoLocation"
import { isUsStateCode, normalizeUsStateCode, type UsStateCode } from "./UsState"

type GeoApiResponse = {
  countryCode: string | null
  regionCode: string | null
  source: "vercel" | "cloudflare" | "unknown"
}

type IpApiResponse = {
  country_code?: string
  region_code?: string
}

export interface GeoLocationServiceOptions {
  /**
   * When true, allows an external IP-to-geo fallback request (ipapi.co) if
   * `/api/geo` doesn't provide a US state.
   */
  enableIpApiFallback: boolean

  /**
   * Query string param used for local/dev overrides, e.g. `?pg_state=NJ`.
   */
  stateOverrideQueryParam: string
}

const DEFAULT_OPTIONS: GeoLocationServiceOptions = {
  enableIpApiFallback: false,
  stateOverrideQueryParam: "pg_state",
}

export class GeoLocationService {
  private readonly options: GeoLocationServiceOptions

  public constructor(options?: Partial<GeoLocationServiceOptions>) {
    this.options = { ...DEFAULT_OPTIONS, ...(options || {}) }
  }

  public async resolve(): Promise<GeoLocation> {
    const override = this.getOverrideFromUrl()
    if (override) {
      return { countryCode: "US", regionCode: override, source: "override" }
    }

    const cached = this.getCached()
    if (cached) return cached

    const fromApi = await this.fetchFromInternalApi()
    if (fromApi.regionCode) {
      this.setCached(fromApi)
      return fromApi
    }

    if (this.options.enableIpApiFallback) {
      const fromIpApi = await this.fetchFromIpApi()
      if (fromIpApi.regionCode) {
        this.setCached(fromIpApi)
        return fromIpApi
      }
    }

    const unknown: GeoLocation = { countryCode: fromApi.countryCode, regionCode: null, source: fromApi.source }
    this.setCached(unknown)
    return unknown
  }

  private getOverrideFromUrl(): UsStateCode | null {
    if (typeof window === "undefined") return null
    try {
      const url = new URL(window.location.href)
      const raw = url.searchParams.get(this.options.stateOverrideQueryParam)
      const normalized = normalizeUsStateCode(raw)
      return isUsStateCode(normalized) ? normalized : null
    } catch {
      return null
    }
  }

  private getCached(): GeoLocation | null {
    if (typeof window === "undefined") return null
    try {
      const raw = sessionStorage.getItem("pg_geo_cache_v1")
      if (!raw) return null
      const parsed = JSON.parse(raw) as Partial<GeoLocation> | null
      if (!parsed || typeof parsed !== "object") return null

      const countryCode = typeof parsed.countryCode === "string" ? parsed.countryCode : null
      const regionCandidate = normalizeUsStateCode(
        typeof parsed.regionCode === "string" ? parsed.regionCode : null
      )
      const regionCode = isUsStateCode(regionCandidate) ? regionCandidate : null
      const source = (parsed.source as GeoSource) || "unknown"
      return { countryCode, regionCode, source }
    } catch {
      return null
    }
  }

  private setCached(geo: GeoLocation) {
    if (typeof window === "undefined") return
    try {
      sessionStorage.setItem("pg_geo_cache_v1", JSON.stringify(geo))
    } catch {
      // ignore
    }
  }

  private async fetchFromInternalApi(): Promise<GeoLocation> {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 3000)

      const res = await fetch("/api/geo", {
        method: "GET",
        headers: { "accept": "application/json" },
        cache: "no-store",
        signal: controller.signal,
      }).finally(() => clearTimeout(timeoutId))

      if (!res.ok) {
        return { countryCode: null, regionCode: null, source: "unknown" }
      }

      const data = (await res.json()) as GeoApiResponse
      const countryCode = typeof data.countryCode === "string" ? data.countryCode : null
      const regionCandidate = normalizeUsStateCode(typeof data.regionCode === "string" ? data.regionCode : null)
      const regionCode = isUsStateCode(regionCandidate) ? regionCandidate : null

      return { countryCode, regionCode, source: "api" }
    } catch {
      return { countryCode: null, regionCode: null, source: "unknown" }
    }
  }

  private async fetchFromIpApi(): Promise<GeoLocation> {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 4000)

      const res = await fetch("https://ipapi.co/json/", {
        method: "GET",
        headers: { "accept": "application/json" },
        signal: controller.signal,
      }).finally(() => clearTimeout(timeoutId))

      if (!res.ok) {
        return { countryCode: null, regionCode: null, source: "unknown" }
      }

      const data = (await res.json()) as IpApiResponse
      const countryCode = typeof data.country_code === "string" ? data.country_code.toUpperCase() : null
      const regionCandidate = normalizeUsStateCode(typeof data.region_code === "string" ? data.region_code : null)
      const regionCode = isUsStateCode(regionCandidate) ? regionCandidate : null

      return { countryCode, regionCode, source: "ipapi" }
    } catch {
      return { countryCode: null, regionCode: null, source: "unknown" }
    }
  }
}


