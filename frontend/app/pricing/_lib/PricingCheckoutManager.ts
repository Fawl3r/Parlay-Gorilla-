import { PREMIUM_CRYPTO_URL, PREMIUM_LEMONSQUEEZY_URL } from "@/lib/pricingConfig"
import { LemonSqueezyAffiliateUrlBuilder } from "@/lib/lemonsqueezy/LemonSqueezyAffiliateUrlBuilder"

export type PricingCheckoutVariant =
  | "card-monthly"
  | "card-annual"
  | "card-lifetime"
  | "crypto-monthly"
  | "crypto-annual"
  | "crypto-lifetime"

type CheckoutProvider = "lemonsqueezy" | "coinbase"

type CheckoutPlanCode =
  | "PG_PREMIUM_MONTHLY"
  | "PG_PREMIUM_ANNUAL"
  | "PG_LIFETIME_CARD"
  | "PG_PREMIUM_MONTHLY_CRYPTO"
  | "PG_PREMIUM_ANNUAL_CRYPTO"
  | "PG_LIFETIME"

type CheckoutAction =
  | { kind: "auth_required"; redirectAfterLogin: string }
  | { kind: "redirect"; url: string }
  | { kind: "error"; message: string }

type CreateCheckout = (provider: CheckoutProvider, planCode: string) => Promise<string>

type VariantConfig = {
  provider: CheckoutProvider
  planCode: CheckoutPlanCode
  fallbackUrl?: string
  errorMessage: string
}

const VARIANTS: Record<PricingCheckoutVariant, VariantConfig> = {
  "card-monthly": {
    provider: "lemonsqueezy",
    planCode: "PG_PREMIUM_MONTHLY",
    fallbackUrl: PREMIUM_LEMONSQUEEZY_URL,
    errorMessage: "Card checkout failed. Please try again.",
  },
  "card-annual": {
    provider: "lemonsqueezy",
    planCode: "PG_PREMIUM_ANNUAL",
    fallbackUrl: PREMIUM_LEMONSQUEEZY_URL,
    errorMessage: "Yearly checkout failed. Please try again.",
  },
  "card-lifetime": {
    provider: "lemonsqueezy",
    planCode: "PG_LIFETIME_CARD",
    errorMessage: "Lifetime checkout is not configured yet. Please contact support.",
  },
  "crypto-monthly": {
    provider: "coinbase",
    planCode: "PG_PREMIUM_MONTHLY_CRYPTO",
    errorMessage: "Crypto monthly checkout failed. Please try again.",
  },
  "crypto-annual": {
    provider: "coinbase",
    planCode: "PG_PREMIUM_ANNUAL_CRYPTO",
    errorMessage: "Crypto annual checkout failed. Please try again.",
  },
  "crypto-lifetime": {
    provider: "coinbase",
    planCode: "PG_LIFETIME",
    fallbackUrl: PREMIUM_CRYPTO_URL,
    errorMessage: "Crypto checkout failed. Please try again.",
  },
}

/**
 * Business logic for starting subscription checkouts.
 *
 * UI state + navigation belong in a Coordinator (see `usePricingCheckoutCoordinator`).
 */
export class PricingCheckoutManager {
  constructor(private readonly createCheckout: CreateCheckout) {}

  async beginCheckout(params: {
    variant: PricingCheckoutVariant
    isAuthenticated: boolean
    redirectAfterLogin?: string
  }): Promise<CheckoutAction> {
    const redirectAfterLogin = params.redirectAfterLogin ?? "/pricing"

    if (!params.isAuthenticated) {
      return { kind: "auth_required", redirectAfterLogin }
    }

    const cfg = VARIANTS[params.variant]

    try {
      const checkoutUrl = await this.createCheckout(cfg.provider, cfg.planCode)
      if (checkoutUrl) {
        return { kind: "redirect", url: checkoutUrl }
      }

      const fallbackUrl = await this.getRedirectFallbackUrl(cfg)
      if (fallbackUrl) return { kind: "redirect", url: fallbackUrl }

      return { kind: "error", message: cfg.errorMessage }
    } catch {
      const fallbackUrl = await this.getRedirectFallbackUrl(cfg)
      if (fallbackUrl) return { kind: "redirect", url: fallbackUrl }

      return { kind: "error", message: cfg.errorMessage }
    }
  }

  private async getRedirectFallbackUrl(cfg: VariantConfig): Promise<string | undefined> {
    if (!cfg.fallbackUrl) return undefined
    if (cfg.provider !== "lemonsqueezy") return cfg.fallbackUrl
    return await new LemonSqueezyAffiliateUrlBuilder().build(cfg.fallbackUrl)
  }
}


