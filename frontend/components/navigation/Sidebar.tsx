"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { ChevronLeft, ChevronRight } from "lucide-react"

import { useAuth } from "@/lib/auth-context"
import { SidebarNavManager, type SidebarNavSection } from "@/lib/navigation/SidebarNavManager"
import { ParlayGorillaLogo } from "@/components/ParlayGorillaLogo"
import { AvatarMenuDropdown } from "@/components/navigation/topbar/AvatarMenuDropdown"
import { useSidebar } from "@/lib/contexts/SidebarContext"
import { cn } from "@/lib/utils"

export function Sidebar() {
  const pathname = usePathname() || "/"
  const { user, signOut } = useAuth()
  const { isCollapsed, setIsCollapsed } = useSidebar()
  const manager = new SidebarNavManager()
  const isAuthed = Boolean(user)

  const sections = manager.getSections(isAuthed)
  const items = manager.getItems(isAuthed)

  const toggleCollapse = () => {
    setIsCollapsed((prev) => !prev)
  }

  return (
    <motion.aside
      initial={false}
      animate={{
        width: isCollapsed ? 64 : 240,
      }}
      transition={{
        duration: 0.2,
        ease: [0.4, 0, 0.2, 1],
      }}
      className={cn(
        "sticky top-0 h-screen z-40 flex-shrink-0",
        "bg-[rgba(26,26,31,0.8)] backdrop-blur-xl",
        "border-r border-white/10",
        "flex flex-col",
        "overflow-hidden"
      )}
    >
      {/* Header with Logo and User */}
      <div className="flex items-center justify-between p-4 border-b border-white/10 min-h-[64px]">
        <AnimatePresence mode="wait">
          {!isCollapsed ? (
            <motion.div
              key="logo-expanded"
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.2 }}
              className="flex items-center gap-3 min-w-0"
            >
              <Link href="/" className="shrink-0">
                <ParlayGorillaLogo size="sm" showText={false} />
              </Link>
              {user && (
                <div className="flex items-center gap-2 min-w-0">
                  <AvatarMenuDropdown
                    userEmail={user.email ?? null}
                    onSignOut={signOut}
                    className="shrink-0"
                  />
                  <span className="text-sm font-medium text-white/90 truncate">
                    {user.email?.split("@")[0] || "User"}
                  </span>
                </div>
              )}
            </motion.div>
          ) : (
            <motion.div
              key="logo-collapsed"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="flex justify-center w-full"
            >
              <Link href="/">
                <ParlayGorillaLogo size="sm" showText={false} />
              </Link>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-6">
        <AnimatePresence>
          {sections.map((section, sectionIndex) => {
            const sectionItems = items.filter((item) => item.section === section)
            if (sectionItems.length === 0) return null

            return (
              <motion.div
                key={section}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: sectionIndex * 0.1 }}
              >
                {/* Section Header */}
                {!isCollapsed && (
                  <motion.h3
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="px-3 mb-2 text-[11px] font-semibold uppercase tracking-[0.5px] text-white/40"
                  >
                    {manager.getSectionLabel(section)}
                  </motion.h3>
                )}

                {/* Section Items */}
                <div className="space-y-1">
                  {sectionItems.map((item, itemIndex) => {
                    const isActive = item.isActive(pathname)
                    const Icon = item.icon

                    return (
                      <SidebarNavItem
                        key={item.id}
                        item={item}
                        isActive={isActive}
                        isCollapsed={isCollapsed}
                        delay={itemIndex * 0.05}
                      />
                    )
                  })}
                </div>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </nav>

      {/* Collapse Toggle Button */}
      <div className="p-2 border-t border-white/10">
        <motion.button
          onClick={toggleCollapse}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className={cn(
            "w-full flex items-center justify-center gap-2 p-2 rounded-lg",
            "text-white/70 hover:text-white hover:bg-white/10",
            "transition-colors"
          )}
          aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4" />
              <span className="text-sm font-medium">Collapse</span>
            </>
          )}
        </motion.button>
      </div>
    </motion.aside>
  )
}

type SidebarNavItemProps = {
  item: {
    id: string
    label: string
    href: string
    icon: React.ComponentType<{ className?: string }>
  }
  isActive: boolean
  isCollapsed: boolean
  delay: number
}

function SidebarNavItem({ item, isActive, isCollapsed, delay }: SidebarNavItemProps) {
  const Icon = item.icon

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay }}
    >
      <Link
        href={item.href}
        className={cn(
          "relative flex items-center gap-3 px-3 py-2.5 rounded-lg",
          "text-sm font-medium transition-all duration-200",
          "group",
          isActive
            ? "text-emerald-400 bg-emerald-500/10"
            : "text-white/70 hover:text-white hover:bg-white/5"
        )}
      >
        {/* Active indicator background */}
        {isActive && (
          <motion.div
            layoutId="sidebar-active-bg"
            className="absolute inset-0 rounded-lg bg-gradient-to-r from-emerald-500/20 to-emerald-500/10 border border-emerald-500/20"
            transition={{
              duration: 0.2,
              ease: [0.4, 0, 0.2, 1],
            }}
          />
        )}

        {/* Icon */}
        <motion.div
          className="relative z-10 shrink-0"
          whileHover={{ scale: 1.02 }}
          transition={{ duration: 0.15, ease: "easeOut" }}
        >
          <Icon className={cn("h-5 w-5", isActive && "text-emerald-400")} />
        </motion.div>

        {/* Label */}
        <AnimatePresence>
          {!isCollapsed && (
            <motion.span
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: "auto" }}
              exit={{ opacity: 0, width: 0 }}
              transition={{ duration: 0.2 }}
              className="relative z-10 truncate"
            >
              {item.label}
            </motion.span>
          )}
        </AnimatePresence>

        {/* Hover glow effect */}
        <motion.div
          className="absolute inset-0 rounded-lg bg-emerald-500/0 group-hover:bg-emerald-500/5"
          transition={{ duration: 0.2 }}
        />
      </Link>
    </motion.div>
  )
}
