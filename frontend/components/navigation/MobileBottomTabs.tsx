"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { BarChart3, Home, Layers, Search, User } from "lucide-react"
import type { ComponentType } from "react"

import { cn } from "@/lib/utils"

type Tab = {
  href: string
  label: string
  Icon: ComponentType<{ className?: string }>
  isActive: (pathname: string) => boolean
}

const tabs: Tab[] = [
  {
    href: "/",
    label: "Home",
    Icon: Home,
    isActive: (p) => p === "/",
  },
  {
    href: "/app",
    label: "AI Picks",
    Icon: Layers,
    isActive: (p) => p === "/app" || p.startsWith("/app/"),
  },
  {
    href: "/analysis",
    label: "Games",
    Icon: Search,
    isActive: (p) => p === "/analysis" || p.startsWith("/analysis/"),
  },
  {
    href: "/analytics",
    label: "Insights",
    Icon: BarChart3,
    isActive: (p) => p === "/analytics" || p.startsWith("/analytics/"),
  },
  {
    href: "/profile",
    label: "Account",
    Icon: User,
    isActive: (p) => p === "/profile" || p.startsWith("/profile/"),
  },
]

export function MobileBottomTabs() {
  const pathname = usePathname() || ""

  return (
    <nav
      className={cn(
        "fixed bottom-0 left-0 right-0 z-50 md:hidden",
        "border-t border-white/10 bg-black/70 backdrop-blur-xl",
        "pb-[calc(env(safe-area-inset-bottom,0px)+8px)]"
      )}
      aria-label="Primary navigation"
      data-testid="mobile-bottom-tabs"
    >
      <div className="mx-auto w-full max-w-3xl px-3 pt-2">
        <div className="grid grid-cols-5 gap-1">
          {tabs.map((t) => {
            const active = t.isActive(pathname)
            return (
              <Link
                key={t.href}
                href={t.href}
                className={cn(
                  "min-h-[44px] rounded-xl px-1 py-2",
                  "flex flex-col items-center justify-center gap-1",
                  "transition-colors",
                  active ? "bg-emerald-500 text-black" : "text-gray-200/80 hover:bg-white/10 hover:text-white"
                )}
                aria-current={active ? "page" : undefined}
              >
                <t.Icon className={cn("h-5 w-5", active ? "text-black" : "text-emerald-300")} />
                <span className={cn("text-[11px] font-bold leading-none", active ? "text-black" : "text-gray-200")}>
                  {t.label}
                </span>
              </Link>
            )
          })}
        </div>
      </div>
    </nav>
  )
}

export default MobileBottomTabs


