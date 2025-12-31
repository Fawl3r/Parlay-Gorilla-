"use client"

import { useRouter } from "next/navigation"

import { useAuth } from "@/lib/auth-context"
import { NavLabelResolver } from "@/lib/navigation/NavLabelResolver"
import { cn } from "@/lib/utils"

export type MobileTopBarProps = {
  pathname: string
  className?: string
}

export function MobileTopBar({ pathname, className }: MobileTopBarProps) {
  const router = useRouter()
  const { user } = useAuth()

  const resolver = new NavLabelResolver()
  const title = resolver.getTitle(pathname)
  const showBack = resolver.shouldShowBack(pathname)

  const fallbackHref = user ? "/app" : "/"

  return (
    <div className={cn("md:hidden h-16 flex items-center", className)}>
      {showBack ? (
        <button
          type="button"
          onClick={() => {
            const canGoBack = typeof window !== "undefined" && window.history.length > 1
            if (canGoBack) router.back()
            else router.push(fallbackHref)
          }}
          className={cn(
            "shrink-0 min-h-[44px] min-w-[44px] rounded-xl",
            "text-white/80 hover:bg-white/10 transition-colors"
          )}
          aria-label="Back"
        >
          ←
        </button>
      ) : (
        <div className="shrink-0 w-[44px]" aria-hidden="true" />
      )}

      <div className="flex-1 text-center text-sm font-black text-white truncate px-2">{title}</div>

      {/* Right spacer: keep title centered (no icons/actions on mobile top bar) */}
      <div className="shrink-0 w-[44px]" aria-hidden="true" />
    </div>
  )
}

export default MobileTopBar


