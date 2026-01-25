"use client"

import { useEffect, useState } from "react"
import { usePathname } from "next/navigation"
import { motion, useScroll, useMotionValueEvent } from "framer-motion"

import { DesktopTopBar } from "@/components/navigation/topbar/DesktopTopBar"
import { MobileTopBar } from "@/components/navigation/topbar/MobileTopBar"
import { useAuth } from "@/lib/auth-context"
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
      <div className="w-full px-2 sm:container sm:mx-auto sm:max-w-7xl sm:px-4">
        <div className="flex items-center justify-between h-16">
          <DesktopTopBar
            key={`desktop:${pathname}`}
            homeHref={homeHref}
            userEmail={user?.email ?? null}
            onSignOut={signOut}
            onGenerate={onGenerate}
            hideNav={hideNav}
            showStatusIndicator={!!user}
          />
          <MobileTopBar
            key={`mobile:${pathname}`}
            pathname={pathname}
            onSignOut={signOut}
            onGenerate={onGenerate}
          />
        </div>
      </div>
    </motion.header>
  )
}

