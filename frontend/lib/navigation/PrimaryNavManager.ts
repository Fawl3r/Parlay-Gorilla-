export type PrimaryNavId = "home" | "build" | "games" | "insights" | "pricing" | "pg101" | "development" | "affiliates"

export type PrimaryNavItem = {
  id: PrimaryNavId
  label: string
  href: string
  isActive: (pathname: string) => boolean
}

export class PrimaryNavManager {
  public getItems({ isAuthed }: { isAuthed: boolean }): PrimaryNavItem[] {
    if (isAuthed) {
      // Authenticated users see app-focused navigation
      return [
        { id: "home", label: "Home", href: "/", isActive: (p) => this.isHome(p) },
        { id: "build", label: "AI Picks", href: "/app", isActive: (p) => this.isBuild(p) },
        { id: "games", label: "Games", href: "/analysis", isActive: (p) => this.isGames(p) },
        { id: "insights", label: "Insights", href: "/analytics", isActive: (p) => this.isInsights(p) },
      ]
    } else {
      // Public users see marketing/informational navigation
      return [
        { id: "home", label: "Home", href: "/", isActive: (p) => this.isHome(p) },
        { id: "pricing", label: "Pricing", href: "/pricing", isActive: (p) => this.isPricing(p) },
        { id: "pg101", label: "PG-101", href: "/pg-101", isActive: (p) => this.isPg101(p) },
        { id: "development", label: "Development News", href: "/development-news", isActive: (p) => this.isDevelopment(p) },
        { id: "affiliates", label: "Affiliates", href: "/affiliates", isActive: (p) => this.isAffiliates(p) },
      ]
    }
  }

  public resolveActiveId(pathname: string): PrimaryNavId | null {
    const p = this.normalize(pathname)
    if (this.isHome(p)) return "home"
    if (this.isBuild(p)) return "build"
    if (this.isGames(p)) return "games"
    if (this.isInsights(p)) return "insights"
    if (this.isPricing(p)) return "pricing"
    if (this.isPg101(p)) return "pg101"
    if (this.isDevelopment(p)) return "development"
    if (this.isAffiliates(p)) return "affiliates"
    return null
  }

  private isHome(pathname: string): boolean {
    const p = this.normalize(pathname)
    return p === "/"
  }

  private isBuild(pathname: string): boolean {
    const p = this.normalize(pathname)
    if (p === "/app" || p.startsWith("/app/")) return true
    if (p === "/build" || p.startsWith("/build/")) return true
    return (
      p.startsWith("/parlays/same-game") ||
      p.startsWith("/parlays/round-robin") ||
      p.startsWith("/parlays/teasers")
    )
  }

  private isGames(pathname: string): boolean {
    const p = this.normalize(pathname)
    return p === "/analysis" || p.startsWith("/analysis/") || p.startsWith("/games/")
  }

  private isInsights(pathname: string): boolean {
    const p = this.normalize(pathname)
    if (p === "/analytics" || p.startsWith("/analytics/")) return true
    if (p.startsWith("/tools/") || p === "/tools") return true
    if (p.startsWith("/social") || p === "/social") return true
    return p.startsWith("/parlays/history")
  }

  private isPricing(pathname: string): boolean {
    const p = this.normalize(pathname)
    return p === "/pricing" || p.startsWith("/pricing/")
  }

  private isPg101(pathname: string): boolean {
    const p = this.normalize(pathname)
    return p === "/pg-101" || p.startsWith("/pg-101/")
  }

  private isDevelopment(pathname: string): boolean {
    const p = this.normalize(pathname)
    return p === "/development-news" || p.startsWith("/development-news/")
  }

  private isAffiliates(pathname: string): boolean {
    const p = this.normalize(pathname)
    return p === "/affiliates" || p.startsWith("/affiliates/")
  }

  private normalize(pathname: string): string {
    const raw = String(pathname || "/").trim()
    if (!raw) return "/"
    const withLeading = raw.startsWith("/") ? raw : `/${raw}`
    const withoutTrailing = withLeading.replace(/\/+$/, "")
    return withoutTrailing || "/"
  }
}


