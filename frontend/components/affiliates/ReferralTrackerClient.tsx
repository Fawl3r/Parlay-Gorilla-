"use client"

import { useEffect } from "react"
import { usePathname, useSearchParams } from "next/navigation"

import { api } from "@/lib/api"

type AffiliatePublicInfo = {
  referral_code: string
  tier: string
  tier_name: string
  lemonsqueezy_affiliate_code?: string | null
}

class AffiliateReferralTrackingManager {
  private readonly clickRecordedKeyPrefix = "pg_aff_click_recorded:"
  private readonly affInjectedKeyPrefix = "pg_aff_aff_injected:"

  public async handleRouteChange(params: {
    pathname: string
    searchParams: URLSearchParams
  }): Promise<void> {
    const refCode = (params.searchParams.get("ref") || "").trim()
    if (!refCode) return

    await this.recordClickOnce(refCode, params.pathname, params.searchParams)

    // NOTE: `?aff=` is the LemonSqueezy affiliate code parameter.
    // We can inject it for LemonSqueezy tracking if we have a mapping.
    const hasAff = Boolean((params.searchParams.get("aff") || "").trim())
    if (hasAff) return

    const publicInfo = await this.getAffiliatePublicInfo(refCode)
    const lsCode = (publicInfo?.lemonsqueezy_affiliate_code || "").trim()
    if (!lsCode) return

    this.injectAffParamOnce({ refCode, lsCode })
  }

  private async recordClickOnce(refCode: string, pathname: string, searchParams: URLSearchParams): Promise<void> {
    if (!this.canUseSessionStorage()) return

    const key = `${this.clickRecordedKeyPrefix}${refCode}`
    if (sessionStorage.getItem(key) === "1") return

    try {
      await api.post("/api/affiliates/click", {
        referral_code: refCode,
        landing_page: pathname,
        utm_source: searchParams.get("utm_source") || undefined,
        utm_medium: searchParams.get("utm_medium") || undefined,
        utm_campaign: searchParams.get("utm_campaign") || undefined,
      })
      sessionStorage.setItem(key, "1")
    } catch (e) {
      // Best-effort: do not break navigation if tracking fails.
      // eslint-disable-next-line no-console
      console.warn("Affiliate click tracking failed:", e)
    }
  }

  private async getAffiliatePublicInfo(refCode: string): Promise<AffiliatePublicInfo | null> {
    try {
      const res = await api.get(`/api/affiliates/public/${encodeURIComponent(refCode)}`)
      return (res.data || null) as AffiliatePublicInfo | null
    } catch {
      return null
    }
  }

  private injectAffParamOnce(params: { refCode: string; lsCode: string }): void {
    if (!this.canUseSessionStorage()) return

    const key = `${this.affInjectedKeyPrefix}${params.refCode}`
    if (sessionStorage.getItem(key) === "1") return

    try {
      const url = new URL(window.location.href)
      url.searchParams.set("aff", params.lsCode)

      sessionStorage.setItem(key, "1")
      // Force reload so LemonSqueezy tracking can reliably see `?aff=` on page load.
      window.location.replace(url.toString())
    } catch (e) {
      // eslint-disable-next-line no-console
      console.warn("Affiliate aff-param injection failed:", e)
    }
  }

  private canUseSessionStorage(): boolean {
    try {
      return typeof window !== "undefined" && typeof sessionStorage !== "undefined"
    } catch {
      return false
    }
  }
}

export function ReferralTrackerClient() {
  const pathname = usePathname()
  const searchParams = useSearchParams()

  useEffect(() => {
    const manager = new AffiliateReferralTrackingManager()
    void manager.handleRouteChange({
      pathname: pathname || "/",
      searchParams: new URLSearchParams(searchParams?.toString() || ""),
    })
  }, [pathname, searchParams])

  return null
}


