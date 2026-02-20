import type { LucideIcon } from "lucide-react"
import {
  Home,
  Zap,
  Calendar,
  BarChart3,
  Trophy,
  User,
  Activity,
  CreditCard,
  Settings,
  HelpCircle,
  MessageSquare,
  Newspaper,
  Map,
  AlertTriangle,
} from "lucide-react"

/**
 * Shared Support items (visible to all users). Frozen to prevent accidental mutation.
 */
const SUPPORT_BASE_ITEMS = Object.freeze([
  {
    id: "help",
    label: "Help",
    href: "/tutorial",
    icon: HelpCircle,
    section: "support",
  },
  {
    id: "development-news",
    label: "Development News",
    href: "/development-news",
    icon: Newspaper,
    section: "support",
  },
]) as readonly { id: string; label: string; href: string; icon: LucideIcon; section: "support" }[]

/**
 * Support items visible only when authenticated. Frozen to prevent accidental mutation.
 */
const SUPPORT_AUTH_ONLY_ITEMS = Object.freeze([
  {
    id: "feedback",
    label: "Feedback",
    href: "/support",
    icon: MessageSquare,
    section: "support",
  },
]) as readonly { id: string; label: string; href: string; icon: LucideIcon; section: "support" }[]

function buildSupportItems(
  isAuthenticated: boolean,
  getIsActive: (id: string) => (pathname: string) => boolean,
): SidebarNavItem[] {
  const base: SidebarNavItem[] = SUPPORT_BASE_ITEMS.map((item) => ({
    ...item,
    section: "support",
    isActive: getIsActive(item.id),
  }))
  if (!isAuthenticated) return base
  const authOnly: SidebarNavItem[] = SUPPORT_AUTH_ONLY_ITEMS.map((item) => ({
    ...item,
    section: "support",
    isActive: getIsActive(item.id),
  }))
  return [...base, ...authOnly]
}

export type SidebarNavSection = "dashboard" | "account" | "support"

export type SidebarNavItem = {
  id: string
  label: string
  href: string
  icon: LucideIcon
  section: SidebarNavSection
  isActive: (pathname: string) => boolean
}

export class SidebarNavManager {
  public getSections(isAuthed: boolean): SidebarNavSection[] {
    if (isAuthed) {
      return ["dashboard", "account", "support"]
    }
    return ["dashboard", "support"]
  }

  public getItems(isAuthed: boolean): SidebarNavItem[] {
    const items: SidebarNavItem[] = []
    const authed = isAuthed

    if (authed) {
      // Dashboard section for authenticated users
      items.push(
        {
          id: "home",
          label: "Home",
          href: "/",
          icon: Home,
          section: "dashboard",
          isActive: (p) => this.isHome(p),
        },
        {
          id: "ai-picks",
          label: "Intelligence Overview",
          href: "/app",
          icon: Zap,
          section: "dashboard",
          isActive: (p) => this.isBuild(p),
        },
        {
          id: "games",
          label: "Matchup Intelligence",
          href: "/analysis",
          icon: Calendar,
          section: "dashboard",
          isActive: (p) => this.isGames(p),
        },
        {
          id: "insights",
          label: "Insights",
          href: "/analytics",
          icon: BarChart3,
          section: "dashboard",
          isActive: (p) => this.isInsights(p),
        },
        {
          id: "odds-heatmap",
          label: "Odds Heatmap",
          href: "/tools/odds-heatmap",
          icon: Map,
          section: "dashboard",
          isActive: (p) => this.isOddsHeatmap(p),
        },
        {
          id: "upset-finder",
          label: "Upset Finder",
          href: "/tools/upset-finder",
          icon: AlertTriangle,
          section: "dashboard",
          isActive: (p) => this.isUpsetFinder(p),
        },
        {
          id: "leaderboards",
          label: "Performance Rankings",
          href: "/leaderboards",
          icon: Trophy,
          section: "dashboard",
          isActive: (p) => this.isLeaderboards(p),
        },
        // Account section
        {
          id: "profile",
          label: "Profile",
          href: "/profile",
          icon: User,
          section: "account",
          isActive: (p) => this.isProfile(p),
        },
        {
          id: "usage",
          label: "Usage",
          href: "/usage",
          icon: Activity,
          section: "account",
          isActive: (p) => this.isUsage(p),
        },
        {
          id: "billing",
          label: "Billing",
          href: "/billing",
          icon: CreditCard,
          section: "account",
          isActive: (p) => this.isBilling(p),
        },
        {
          id: "settings",
          label: "Settings",
          href: "/settings",
          icon: Settings,
          section: "account",
          isActive: (p) => this.isSettings(p),
        },
      )
    } else {
      // Public users - limited navigation
      items.push(
        {
          id: "home",
          label: "Home",
          href: "/",
          icon: Home,
          section: "dashboard",
          isActive: (p) => this.isHome(p),
        },
        {
          id: "games",
          label: "Game Analytics",
          href: "/analysis",
          icon: Calendar,
          section: "dashboard",
          isActive: (p) => this.isGames(p),
        },
        {
          id: "leaderboards",
          label: "Leaderboards",
          href: "/leaderboards",
          icon: Trophy,
          section: "dashboard",
          isActive: (p) => this.isLeaderboards(p),
        },
      )
    }

    this.validateSupportHighlightHandlers()
    items.push(...buildSupportItems(authed, (id) => this.getSupportIsActive(id)))

    return items
  }

  public getSectionLabel(section: SidebarNavSection): string {
    switch (section) {
      case "dashboard":
        return "INTELLIGENCE"
      case "account":
        return "ACCOUNT"
      case "support":
        return "SUPPORT"
      default:
        return ""
    }
  }

  public getItemsBySection(isAuthed: boolean, section: SidebarNavSection): SidebarNavItem[] {
    return this.getItems(isAuthed).filter((item) => item.section === section)
  }

  private normalize(pathname: string): string {
    const raw = String(pathname || "/").trim()
    if (!raw) return "/"
    const withLeading = raw.startsWith("/") ? raw : `/${raw}`
    const withoutTrailing = withLeading.replace(/\/+$/, "")
    return withoutTrailing || "/"
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
    if (p === "/tools" || p.startsWith("/tools/")) {
      if (p === "/tools/odds-heatmap" || p.startsWith("/tools/odds-heatmap/")) return false
      if (p === "/tools/upset-finder" || p.startsWith("/tools/upset-finder/")) return false
      return true
    }
    if (p.startsWith("/social") || p === "/social") return true
    return p.startsWith("/parlays/history")
  }

  private isOddsHeatmap(pathname: string): boolean {
    const p = this.normalize(pathname)
    return p === "/tools/odds-heatmap" || p.startsWith("/tools/odds-heatmap/")
  }

  private isUpsetFinder(pathname: string): boolean {
    const p = this.normalize(pathname)
    return p === "/tools/upset-finder" || p.startsWith("/tools/upset-finder/")
  }

  private isLeaderboards(pathname: string): boolean {
    const p = this.normalize(pathname)
    return p === "/leaderboards" || p.startsWith("/leaderboards/") || p === "/leaderboard" || p.startsWith("/leaderboard/")
  }

  private isProfile(pathname: string): boolean {
    const p = this.normalize(pathname)
    return p === "/profile" || p.startsWith("/profile/")
  }

  private isUsage(pathname: string): boolean {
    const p = this.normalize(pathname)
    return p === "/usage" || p.startsWith("/usage/")
  }

  private isBilling(pathname: string): boolean {
    const p = this.normalize(pathname)
    return p === "/billing" || p.startsWith("/billing/")
  }

  private isSettings(pathname: string): boolean {
    const p = this.normalize(pathname)
    return p === "/settings" || p.startsWith("/settings/")
  }

  /** Map each Support item id to its highlight predicate. Used so new Support items cannot ship without a handler. */
  private readonly supportActiveMap: Record<string, (pathname: string) => boolean> = {
    help: (p) => this.isHelp(p),
    "development-news": (p) => this.isDevelopmentNews(p),
    feedback: (p) => this.isFeedback(p),
  }

  private getSupportIsActive(id: string): (pathname: string) => boolean {
    return (p) => this.supportActiveMap[id]?.(p) ?? false
  }

  /** DEV-only: warn if any Support item id is missing from supportActiveMap. */
  private validateSupportHighlightHandlers(): void {
    if (typeof process === "undefined" || process.env.NODE_ENV !== "development") return
    const ids = [
      ...SUPPORT_BASE_ITEMS.map((item) => item.id),
      ...SUPPORT_AUTH_ONLY_ITEMS.map((item) => item.id),
    ]
    const map = this.supportActiveMap
    for (const id of ids) {
      if (!(id in map) || typeof map[id] !== "function") {
        console.warn(`[SidebarNavManager] Missing highlight handler for support item: ${id}`)
      }
    }
  }

  private isHelp(pathname: string): boolean {
    const p = this.normalize(pathname)
    return p === "/tutorial" || p.startsWith("/tutorial/")
  }

  private isFeedback(pathname: string): boolean {
    const p = this.normalize(pathname)
    return p === "/support" || p.startsWith("/support/")
  }

  private isDevelopmentNews(pathname: string): boolean {
    const p = this.normalize(pathname)
    return p === "/development-news" || p.startsWith("/development-news/")
  }
}
