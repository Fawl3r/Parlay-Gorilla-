"use client"

import { ReactNode } from "react"
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

  // Only show sidebar for authenticated users on dashboard pages
  const showSidebar = Boolean(user) && shouldShowSidebar(pathname)

  return (
    <div className="min-h-screen flex relative" style={{ backgroundColor: "#0a0a0f" }}>
      {/* Sidebar */}
      {showSidebar && (
        <div className="hidden md:block">
          <Sidebar />
        </div>
      )}

      {/* Main Content Area */}
      <motion.div
        className={cn("flex-1 flex flex-col min-w-0", showSidebar && "md:ml-[240px]")}
        animate={{
          marginLeft: showSidebar ? (isCollapsed ? 64 : 240) : 0,
        }}
        transition={{
          type: "spring",
          stiffness: 300,
          damping: 30,
        }}
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
