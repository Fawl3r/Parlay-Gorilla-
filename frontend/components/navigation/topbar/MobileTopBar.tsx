"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Menu } from "lucide-react"

import { useAuth } from "@/lib/auth-context"
import { NavLabelResolver } from "@/lib/navigation/NavLabelResolver"
import { ParlayGorillaLogo } from "@/components/ParlayGorillaLogo"
import { MobileNavMenu } from "./MobileNavMenu"
import { cn } from "@/lib/utils"

export type MobileTopBarProps = {
  pathname: string
  className?: string
  onSignOut?: () => Promise<void>
  onGenerate?: () => void
}

export function MobileTopBar({ pathname, className, onSignOut, onGenerate }: MobileTopBarProps) {
  const router = useRouter()
  const { user, signOut } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)

  const resolver = new NavLabelResolver()
  const title = resolver.getTitle(pathname)
  const showBack = resolver.shouldShowBack(pathname)

  const fallbackHref = user ? "/app" : "/"
  const homeHref = "/"
  const handleSignOut = onSignOut || signOut

  return (
    <>
      <div className={cn("md:hidden h-16 flex items-center gap-2 px-2", className)}>
        <div className="shrink-0 flex items-center gap-2">
          {/* Hamburger Menu Button */}
          <button
            type="button"
            onClick={() => setMenuOpen(true)}
            className={cn(
              "min-h-[44px] min-w-[44px] rounded-xl",
              "text-white/80 hover:bg-white/10 transition-colors flex items-center justify-center"
            )}
            aria-label="Open menu"
          >
            <Menu className="h-6 w-6" />
          </button>
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
        </div>

        <div className="flex-1 flex items-center justify-center px-2">
          {title === "Parlay Gorilla" ? (
            <Link href={homeHref} className="flex items-center gap-2" aria-label="Parlay Gorilla">
              <ParlayGorillaLogo size="sm" showText={true} />
            </Link>
          ) : (
            <span className="text-sm font-black text-white truncate">{title}</span>
          )}
        </div>

        {/* Right spacer: keep title centered */}
        <div className="shrink-0 w-[44px]" aria-hidden="true" />
      </div>

      {/* Mobile Navigation Menu */}
      <MobileNavMenu
        isOpen={menuOpen}
        onClose={() => setMenuOpen(false)}
        onSignOut={handleSignOut}
        onGenerate={onGenerate}
      />
    </>
  )
}

export default MobileTopBar


