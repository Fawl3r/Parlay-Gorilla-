"use client"

import { usePathname } from "next/navigation"

import { DesktopTopBar } from "@/components/navigation/topbar/DesktopTopBar"
import { MobileTopBar } from "@/components/navigation/topbar/MobileTopBar"
import { useAuth } from "@/lib/auth-context"

export type HeaderProps = {
  onGenerate?: () => void
}

export function Header({ onGenerate }: HeaderProps) {
  const pathname = usePathname() || "/"
  const { user, signOut } = useAuth()

  const homeHref = "/"

  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/10 bg-black/70 backdrop-blur-xl">
      <div className="container mx-auto max-w-7xl px-4">
        <DesktopTopBar
          key={`desktop:${pathname}`}
          homeHref={homeHref}
          userEmail={user?.email ?? null}
          onSignOut={signOut}
          onGenerate={onGenerate}
        />
        <MobileTopBar
          key={`mobile:${pathname}`}
          pathname={pathname}
          onSignOut={signOut}
          onGenerate={onGenerate}
        />
      </div>
    </header>
  )
}

