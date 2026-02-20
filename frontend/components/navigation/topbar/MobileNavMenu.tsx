"use client"

import { useState, useEffect, useMemo } from "react"
import { createPortal } from "react-dom"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { X } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"

import { useAuth } from "@/lib/auth-context"
import { SidebarNavManager } from "@/lib/navigation/SidebarNavManager"
import { cn } from "@/lib/utils"

export type MobileNavMenuProps = {
  isOpen: boolean
  onClose: () => void
  onSignOut: () => Promise<void>
  onGenerate?: () => void
}

export function MobileNavMenu({ isOpen, onClose, onSignOut }: MobileNavMenuProps) {
  const pathname = usePathname() || "/"
  const { user } = useAuth()
  const manager = useMemo(() => new SidebarNavManager(), [])
  const isAuthed = Boolean(user)
  const sections = manager.getSections(isAuthed)

  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  useEffect(() => {
    if (!mounted) return
    if (isOpen) document.body.style.overflow = "hidden"
    else document.body.style.overflow = ""
    return () => {
      document.body.style.overflow = ""
    }
  }, [isOpen, mounted])

  if (!mounted) return null

  const content = (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[9998] md:hidden"
            onClick={onClose}
            aria-hidden="true"
          />

          {/* Menu Panel — same nav as desktop sidebar (SidebarNavManager) */}
          <motion.div
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed left-0 top-0 h-[100dvh] w-80 max-w-[85vw] bg-black/95 backdrop-blur-xl border-r border-white/10 z-[9999] md:hidden overflow-y-auto"
          >
            <div className="flex flex-col h-full">
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-white/10">
                <h2 className="text-lg font-bold text-white">Menu</h2>
                <button
                  onClick={onClose}
                  className="min-h-[44px] min-w-[44px] rounded-xl text-white/80 hover:bg-white/10 transition-colors flex items-center justify-center"
                  aria-label="Close menu"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>

              {/* Navigation by section (matches desktop sidebar) */}
              <nav className="flex-1 p-4 overflow-y-auto space-y-6" aria-label="Mobile navigation">
                {sections.map((section) => {
                  const sectionItems = manager.getItemsBySection(isAuthed, section)
                  if (sectionItems.length === 0) return null
                  const sectionLabel = manager.getSectionLabel(section)
                  return (
                    <div key={section}>
                      <p className="px-4 mb-2 text-xs font-semibold uppercase tracking-wider text-white/50">
                        {sectionLabel}
                      </p>
                      <div className="space-y-1">
                        {sectionItems.map((item) => {
                          const active = item.isActive(pathname)
                          return (
                            <Link
                              key={item.id}
                              href={item.href}
                              onClick={onClose}
                              aria-current={active ? "page" : undefined}
                              className={cn(
                                "block rounded-lg px-4 py-3 text-base font-semibold transition-colors",
                                "min-h-[44px] flex items-center gap-3",
                                active
                                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                                  : "text-white/70 hover:bg-white/10 hover:text-white"
                              )}
                            >
                              <item.icon className="h-5 w-5 shrink-0 text-current" />
                              {item.label}
                            </Link>
                          )
                        })}
                      </div>
                    </div>
                  )
                })}
                {!user && (
                  <div className="pt-2">
                    <Link
                      href="/auth/login"
                      onClick={onClose}
                      className={cn(
                        "block rounded-lg px-4 py-3 text-base font-semibold transition-colors",
                        "min-h-[44px] flex items-center",
                        pathname === "/auth/login" || pathname === "/auth/signup"
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                          : "text-white/70 hover:bg-white/10 hover:text-white"
                      )}
                    >
                      Sign In
                    </Link>
                  </div>
                )}
              </nav>

              {/* Footer: Sign Out (authed) or CTA (guest) */}
              <div className="p-4 border-t border-white/10 space-y-2">
                {user && (
                  <button
                    onClick={async () => {
                      await onSignOut()
                      onClose()
                    }}
                    className="block w-full rounded-lg px-4 py-3 text-base font-semibold text-left text-white/70 hover:bg-white/10 hover:text-white transition-colors"
                  >
                    Sign Out
                  </button>
                )}
                {!user && (
                  <div className="space-y-2">
                    <Link
                      href="/auth/login"
                      onClick={onClose}
                      className="block w-full rounded-lg px-4 py-3 text-base font-semibold text-center bg-white/10 text-white hover:bg-white/20 transition-colors"
                    >
                      Sign In
                    </Link>
                    <Link
                      href="/auth/signup"
                      onClick={onClose}
                      className="block w-full rounded-lg px-4 py-3 text-base font-semibold text-center bg-emerald-500 text-black hover:bg-emerald-400 transition-colors"
                    >
                      Create Account
                    </Link>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )

  return createPortal(content, document.body)
}

export default MobileNavMenu

