"use client"

import { useEffect, useMemo, useState } from "react"
import type { GeoLocation } from "./GeoLocation"
import { GeoLocationService } from "./GeoLocationService"

export interface UseGeoLocationResult {
  geo: GeoLocation
  loading: boolean
}

export function useGeoLocation(): UseGeoLocationResult {
  const enableIpApiFallback = process.env.NEXT_PUBLIC_GEOIP_FALLBACK_IPAPI === "true"

  const service = useMemo(
    () => new GeoLocationService({ enableIpApiFallback, stateOverrideQueryParam: "pg_state" }),
    [enableIpApiFallback]
  )

  const [loading, setLoading] = useState(true)
  const [geo, setGeo] = useState<GeoLocation>({ countryCode: null, regionCode: null, source: "unknown" })

  useEffect(() => {
    let cancelled = false
    async function run() {
      try {
        const next = await service.resolve()
        if (!cancelled) setGeo(next)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    run()
    return () => {
      cancelled = true
    }
  }, [service])

  return { geo, loading }
}


