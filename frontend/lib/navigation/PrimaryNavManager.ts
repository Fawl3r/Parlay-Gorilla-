export type PrimaryNavId = "home" | "build" | "games" | "insights"

export type PrimaryNavItem = {
  id: PrimaryNavId
  label: string
  href: string
  isActive: (pathname: string) => boolean
}

export class PrimaryNavManager {
  public getItems({ isAuthed }: { isAuthed: boolean }): PrimaryNavItem[] {
    return [
      { id: "home", label: "Home", href: "/", isActive: (p) => this.isHome(p) },
      { id: "build", label: "AI Picks", href: "/app", isActive: (p) => this.isBuild(p) },
      { id: "games", label: "Games", href: "/analysis", isActive: (p) => this.isGames(p) },
      { id: "insights", label: "Insights", href: "/analytics", isActive: (p) => this.isInsights(p) },
    ]
  }

  public resolveActiveId(pathname: string): PrimaryNavId | null {
    const p = this.normalize(pathname)
    if (this.isHome(p)) return "home"
    if (this.isBuild(p)) return "build"
    if (this.isGames(p)) return "games"
    if (this.isInsights(p)) return "insights"
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

  private normalize(pathname: string): string {
    const raw = String(pathname || "/").trim()
    if (!raw) return "/"
    const withLeading = raw.startsWith("/") ? raw : `/${raw}`
    const withoutTrailing = withLeading.replace(/\/+$/, "")
    return withoutTrailing || "/"
  }
}


