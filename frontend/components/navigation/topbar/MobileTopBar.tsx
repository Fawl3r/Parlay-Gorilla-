"use client"

import { useRouter } from "next/navigation"
import Link from "next/link"

import { useAuth } from "@/lib/auth-context"
import { NavLabelResolver } from "@/lib/navigation/NavLabelResolver"
import { ParlayGorillaLogo } from "@/components/ParlayGorillaLogo"
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
  const homeHref = "/"

  return (
    <div className={cn("md:hidden h-16 flex items-center gap-2 px-2", className)}>
      <div className="shrink-0 flex items-center gap-2">
        {showBack && (
          <button
            type="button"
            onClick={() => {
              const canGoBack = typeof window !== "undefined" && window.history.length > 1
              if (canGoBack) router.back()
              else router.push(fallbackHref)
            }}
            className={cn(
              "min-h-[44px] min-w-[44px] rounded-xl",
              "text-white/80 hover:bg-white/10 transition-colors flex items-center justify-center"
            )}
            aria-label="Back"
          >
            ←
          </button>
        )}
        <Link 
          href={homeHref} 
          className="flex items-center" 
          aria-label="Home"
        >
          <ParlayGorillaLogo size="sm" showText={false} />
        </Link>
      </div>

      <div className="flex-1 text-center text-sm font-black text-white truncate px-2">{title}</div>

      {/* Right spacer: keep title centered */}
      <div className="shrink-0 w-[44px]" aria-hidden="true" />
    </div>
  )
}

export default MobileTopBar


