"use client"

import { ReactNode, useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { usePathname } from "next/navigation"

import { Sidebar } from "@/components/navigation/Sidebar"
import { Header } from "@/components/Header"
import { useAuth } from "@/lib/auth-context"
import { useSidebar } from "@/lib/contexts/SidebarContext"
import { cn } from "@/lib/utils"

type DashboardLayoutProps = {
  children: ReactNode
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = usePathname() || "/"
  const { user } = useAuth()
  const { isCollapsed } = useSidebar()
  const [isMobile, setIsMobile] = useState(true)

  // Only show sidebar for authenticated users on dashboard pages
  const showSidebar = Boolean(user) && shouldShowSidebar(pathname)

  // Detect if we're on mobile (below md breakpoint)
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768) // md breakpoint is 768px
    }
    
    checkMobile()
    window.addEventListener("resize", checkMobile)
    return () => window.removeEventListener("resize", checkMobile)
  }, [])

  return (
    <div className="min-h-screen flex relative" style={{ backgroundColor: "#0a0a0f" }}>
      {/* Sidebar — sticky so it scrolls with the page and sticks at top */}
      {showSidebar && (
        <motion.div
          className="hidden md:block flex-shrink-0"
          animate={{ width: !isMobile ? (isCollapsed ? 64 : 240) : 0 }}
          transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
        >
          <Sidebar />
        </motion.div>
      )}

      {/* Main Content Area */}
      <motion.div
        className="flex-1 flex flex-col min-w-0"
        transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
      >
        {/* Header */}
        <Header hideNav={showSidebar} />

        {/* Page Content with Transitions */}
        <AnimatePresence mode="wait">
          <motion.main
            key={pathname}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{
              duration: 0.2,
              ease: [0.4, 0, 0.2, 1],
            }}
            className="flex-1 relative z-10"
          >
            {children}
          </motion.main>
        </AnimatePresence>
      </motion.div>
    </div>
  )
}

function shouldShowSidebar(pathname: string): boolean {
  const p = pathname.toLowerCase()
  const dashboardRoutes = ["/app", "/analysis", "/analytics", "/profile", "/billing", "/usage", "/settings", "/tutorial", "/support"]
  return dashboardRoutes.some((route) => p === route || p.startsWith(`${route}/`))
}
