"use client"

import { useEffect, useState } from "react"
import { usePathname } from "next/navigation"
import { motion, useScroll, useMotionValueEvent } from "framer-motion"

import { DesktopTopBar } from "@/components/navigation/topbar/DesktopTopBar"
import { MobileTopBar } from "@/components/navigation/topbar/MobileTopBar"
import { useAuth } from "@/lib/auth-context"
import { StatusIndicator } from "@/components/ui/status-indicator"
import { cn } from "@/lib/utils"

export type HeaderProps = {
  onGenerate?: () => void
  hideNav?: boolean
}

export function Header({ onGenerate, hideNav = false }: HeaderProps) {
  const pathname = usePathname() || "/"
  const { user, signOut } = useAuth()
  const { scrollY } = useScroll()
  const [scrolled, setScrolled] = useState(false)

  useMotionValueEvent(scrollY, "change", (latest) => {
    setScrolled(latest > 10)
  })

  const homeHref = "/"

  return (
    <motion.header
      className={cn(
        "sticky top-0 z-50 w-full border-b transition-all duration-300",
        scrolled
          ? "bg-[rgba(10,10,15,0.85)] backdrop-blur-xl border-white/15 shadow-lg shadow-black/10"
          : "bg-[rgba(10,10,15,0.7)] backdrop-blur-lg border-white/10"
      )}
      animate={{
        backdropFilter: scrolled ? "blur(24px)" : "blur(16px)",
      }}
      transition={{ duration: 0.3 }}
    >
      <div className="container mx-auto max-w-7xl px-4">
        <div className="flex items-center justify-between h-16">
          <DesktopTopBar
            key={`desktop:${pathname}`}
            homeHref={homeHref}
            userEmail={user?.email ?? null}
            onSignOut={signOut}
            onGenerate={onGenerate}
            hideNav={hideNav}
          />
          <MobileTopBar
            key={`mobile:${pathname}`}
            pathname={pathname}
            onSignOut={signOut}
            onGenerate={onGenerate}
          />
          
          {/* Status Indicator - Desktop Only */}
          {user && (
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10">
              <StatusIndicator type="success" pulse size="sm" />
              <span className="text-xs font-medium text-white/80">Gorilla AI Online</span>
            </div>
          )}
        </div>
      </div>
    </motion.header>
  )
}

