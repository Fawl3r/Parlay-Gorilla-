export class NavLabelResolver {
  public getTitle(pathname: string): string {
    const p = this.normalize(pathname)

    if (p === "/") return "Home"
    if (p === "/app" || p.startsWith("/app/")) return "Home"
    if (p === "/build" || p.startsWith("/build/")) return "Build"

    if (p === "/analysis" || p.startsWith("/analysis/") || p.startsWith("/games/")) return "Games"
    if (p === "/analytics" || p.startsWith("/analytics/")) return "Insights"

    if (p === "/profile" || p.startsWith("/profile/")) return "Account"
    if (p === "/billing" || p.startsWith("/billing/")) return "Plan & Billing"
    if (p === "/usage" || p.startsWith("/usage/")) return "Usage & Performance"
    if (p === "/leaderboards" || p.startsWith("/leaderboards/")) return "Leaderboards"
    if (p === "/tutorial" || p.startsWith("/tutorial/")) return "Tutorial"

    if (p === "/auth/login") return "Sign in"
    if (p === "/auth/signup") return "Create account"
    if (p.startsWith("/auth/")) return "Account"

    if (p === "/pricing" || p.startsWith("/pricing/")) return "Pricing"
    if (p === "/support" || p.startsWith("/support/")) return "Help"

    if (p === "/pg-101" || p.startsWith("/pg-101/")) return "PG-101"
    if (p === "/development-news" || p.startsWith("/development-news/")) return "News"

    if (p === "/affiliates" || p.startsWith("/affiliates/")) return "Affiliates"
    if (p === "/admin" || p.startsWith("/admin/")) return "Admin"

    return "Parlay Gorilla"
  }

  public shouldShowBack(pathname: string): boolean {
    const p = this.normalize(pathname)

    // Root destinations (no back arrow)
    if (p === "/") return false
    if (p === "/app" || p.startsWith("/app/")) return false
    if (p === "/build" || p.startsWith("/build/")) return false
    if (p === "/analysis") return false
    if (p === "/analytics") return false
    if (p === "/profile") return false

    return true
  }

  private normalize(pathname: string): string {
    const raw = String(pathname || "/").trim()
    if (!raw) return "/"
    const withLeading = raw.startsWith("/") ? raw : `/${raw}`
    const withoutTrailing = withLeading.replace(/\/+$/, "")
    return withoutTrailing || "/"
  }
}


