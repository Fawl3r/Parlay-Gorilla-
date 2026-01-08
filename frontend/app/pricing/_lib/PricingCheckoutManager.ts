export type PricingCheckoutVariant =
  | "card-monthly"
  | "card-annual"
  | "card-lifetime"

type CheckoutProvider = "stripe"

type CheckoutPlanCode =
  | "PG_PRO_MONTHLY"
  | "PG_PRO_ANNUAL"
  | "PG_LIFETIME_CARD"

type CheckoutAction =
  | { kind: "auth_required"; redirectAfterLogin: string }
  | { kind: "redirect"; url: string }
  | { kind: "error"; message: string }

type CreateCheckout = (provider: "stripe", planCode: string) => Promise<string>

type VariantConfig = {
  provider: CheckoutProvider
  planCode: CheckoutPlanCode
  fallbackUrl?: string
  errorMessage: string
}

const VARIANTS: Record<PricingCheckoutVariant, VariantConfig> = {
  "card-monthly": {
    provider: "stripe",
    planCode: "PG_PRO_MONTHLY",
    errorMessage: "Card checkout failed. Please try again.",
  },
  "card-annual": {
    provider: "stripe",
    planCode: "PG_PRO_ANNUAL",
    errorMessage: "Yearly checkout failed. Please try again.",
  },
  "card-lifetime": {
    provider: "stripe",
    planCode: "PG_LIFETIME_CARD",
    errorMessage: "Lifetime checkout is not configured yet. Please contact support.",
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
    return cfg.fallbackUrl
  }
}


