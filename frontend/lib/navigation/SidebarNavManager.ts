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
} from "lucide-react"

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

    if (isAuthed) {
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
        // Support section
        {
          id: "help",
          label: "Help",
          href: "/tutorial",
          icon: HelpCircle,
          section: "support",
          isActive: (p) => this.isHelp(p),
        },
        {
          id: "feedback",
          label: "Feedback",
          href: "/support",
          icon: MessageSquare,
          section: "support",
          isActive: (p) => this.isFeedback(p),
        }
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
        {
          id: "help",
          label: "Help",
          href: "/tutorial",
          icon: HelpCircle,
          section: "support",
          isActive: (p) => this.isHelp(p),
        }
      )
    }

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
    if (p.startsWith("/tools/") || p === "/tools") return true
    if (p.startsWith("/social") || p === "/social") return true
    return p.startsWith("/parlays/history")
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

  private isHelp(pathname: string): boolean {
    const p = this.normalize(pathname)
    return p === "/tutorial" || p.startsWith("/tutorial/")
  }

  private isFeedback(pathname: string): boolean {
    const p = this.normalize(pathname)
    return p === "/support" || p.startsWith("/support/")
  }
}
