export type LemonSqueezyAffiliateBuildFn = (url: string) => string | Promise<string>

declare global {
  // eslint-disable-next-line no-var
  var LemonSqueezy: unknown

  interface Window {
    LemonSqueezy?: {
      Affiliate?: {
        Build?: LemonSqueezyAffiliateBuildFn
      }
    }
  }
}

export class LemonSqueezyAffiliateUrlBuilder {
  public async build(url: string): Promise<string> {
    try {
      if (typeof window === "undefined") return url

      const buildFn = window.LemonSqueezy?.Affiliate?.Build
      if (!buildFn) return url

      const result = buildFn(url)
      if (typeof (result as any)?.then === "function") {
        return await (result as Promise<string>)
      }
      return result as string
    } catch {
      return url
    }
  }
}


