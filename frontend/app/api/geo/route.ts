import { NextResponse } from "next/server"
import { isUsStateCode, normalizeUsStateCode } from "@/lib/geo/UsState"

type GeoResponse = {
  countryCode: string | null
  regionCode: string | null
  source: "vercel" | "cloudflare" | "unknown"
}

export const dynamic = "force-dynamic"

function normalizeCountryCode(value: string | null): string | null {
  if (!value) return null
  const trimmed = value.trim()
  if (!trimmed) return null
  return trimmed.toUpperCase()
}

function pickFirstHeader(headers: Headers, names: string[]): string | null {
  for (const name of names) {
    const v = headers.get(name)
    if (v && v.trim()) return v
  }
  return null
}

export async function GET(request: Request) {
  const h = request.headers

  // Prefer Vercel geo headers when deployed on Vercel.
  const vercelCountry = pickFirstHeader(h, ["x-vercel-ip-country"])
  const vercelRegion = pickFirstHeader(h, ["x-vercel-ip-country-region", "x-vercel-ip-region"])

  if (vercelCountry) {
    const countryCode = normalizeCountryCode(vercelCountry)
    const regionCandidate = normalizeUsStateCode(vercelRegion)
    const regionCode = isUsStateCode(regionCandidate) ? regionCandidate : null

    const body: GeoResponse = { countryCode, regionCode, source: "vercel" }
    return NextResponse.json(body, { headers: { "cache-control": "no-store" } })
  }

  // Cloudflare provides country; region/state is not always available as a header.
  const cfCountry = pickFirstHeader(h, ["cf-ipcountry", "CF-IPCountry"])
  const cfRegion = pickFirstHeader(h, ["cf-region-code", "cf-region", "CF-Region", "CF-Region-Code"])

  if (cfCountry) {
    const countryCode = normalizeCountryCode(cfCountry)
    const regionCandidate = normalizeUsStateCode(cfRegion)
    const regionCode = isUsStateCode(regionCandidate) ? regionCandidate : null

    const body: GeoResponse = { countryCode, regionCode, source: "cloudflare" }
    return NextResponse.json(body, { headers: { "cache-control": "no-store" } })
  }

  const body: GeoResponse = { countryCode: null, regionCode: null, source: "unknown" }
  return NextResponse.json(body, { headers: { "cache-control": "no-store" } })
}


