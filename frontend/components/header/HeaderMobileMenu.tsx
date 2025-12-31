"use client"

import { AnimatePresence, motion } from "framer-motion"
import Link from "next/link"
import { BarChart3, Book, CreditCard, Crown, User, Users, Rss } from "lucide-react"

type HeaderMobileMenuProps = {
  isOpen: boolean
  userEmail: string | null
  loading: boolean
  isPremium: boolean
  onClose: () => void
  onSignOut: () => void
  onSignIn: () => void
  onGetStarted: () => void
}

export function HeaderMobileMenu({
  isOpen,
  userEmail,
  loading,
  isPremium,
  onClose,
  onSignOut,
  onSignIn,
  onGetStarted,
}: HeaderMobileMenuProps) {
  const isAuthed = Boolean(userEmail)

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
          className="border-t border-[#00DD55]/20 md:hidden bg-[#0A0F0A] overflow-hidden"
        >
          <motion.div
            initial={{ y: -20 }}
            animate={{ y: 0 }}
            exit={{ y: -20 }}
            transition={{ duration: 0.3, delay: 0.1 }}
            className="container space-y-1 px-4 py-4"
          >
            {isAuthed ? (
              <>
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.05 }}>
                  <Link
                    href="/"
                    className="block px-3 py-2.5 text-sm font-medium text-white/60 rounded-lg transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10"
                    onClick={onClose}
                  >
                    Home
                  </Link>
                </motion.div>
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }}>
                  <Link
                    href="/analysis"
                    className="block px-3 py-2.5 text-sm font-medium text-white/60 rounded-lg transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10"
                    onClick={onClose}
                  >
                    Game Analytics
                  </Link>
                </motion.div>
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.15 }}>
                  <Link
                    href="/app"
                    className="block px-3 py-2.5 text-sm font-medium text-white/60 rounded-lg transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10"
                    onClick={onClose}
                  >
                    Gorilla Dashboard
                  </Link>
                </motion.div>
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.155 }}>
                  <Link
                    href="/usage"
                    className="block px-3 py-2.5 text-sm font-medium text-white/60 rounded-lg transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10 flex items-center gap-2"
                    onClick={onClose}
                  >
                    <BarChart3 className="h-4 w-4" />
                    Usage &amp; Performance
                  </Link>
                </motion.div>
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.16 }}>
                  <Link
                    href="/billing"
                    className="block px-3 py-2.5 text-sm font-medium text-white/60 rounded-lg transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10 flex items-center gap-2"
                    onClick={onClose}
                  >
                    <CreditCard className="h-4 w-4" />
                    Plan &amp; Billing
                  </Link>
                </motion.div>
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.18 }}>
                  <Link
                    href="/pg-101"
                    className="block px-3 py-2.5 text-sm font-medium text-white/60 rounded-lg transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10 flex items-center gap-2"
                    onClick={onClose}
                  >
                    <Book className="h-4 w-4" />
                    PG-101
                  </Link>
                </motion.div>
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.185 }}>
                  <Link
                    href="/tutorial"
                    className="block px-3 py-2.5 text-sm font-medium text-white/60 rounded-lg transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10"
                    onClick={onClose}
                  >
                    Tutorial
                  </Link>
                </motion.div>
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.19 }}>
                  <Link
                    href="/development-news"
                    className="block px-3 py-2.5 text-sm font-medium text-white/60 rounded-lg transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10 flex items-center gap-2"
                    onClick={onClose}
                  >
                    <Rss className="h-4 w-4" />
                    Development News
                  </Link>
                </motion.div>
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}>
                  <Link
                    href="/affiliates"
                    className="block px-3 py-2.5 text-sm font-medium text-white/60 rounded-lg transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10 flex items-center gap-2"
                    onClick={onClose}
                  >
                    <Users className="h-4 w-4" />
                    Affiliate Program
                  </Link>
                </motion.div>
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.225 }}>
                  <div className="border-t border-gray-800 dark:border-white/10 my-2" />
                </motion.div>
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.25 }}>
                  <Link
                    href="/pricing"
                    className="block px-3 py-2.5 text-sm font-medium text-[#00DD55] rounded-lg transition-all hover:text-[#22DD66] hover:bg-[#00DD55]/10 flex items-center gap-2"
                    onClick={onClose}
                  >
                    <Crown className="h-4 w-4" />
                    {isPremium ? "Manage Subscription" : "Upgrade Subscription"}
                  </Link>
                </motion.div>
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.27 }}>
                  <Link
                    href="/tools/upset-finder"
                    className="block px-3 py-2.5 text-sm font-medium text-white/60 rounded-lg transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10"
                    onClick={onClose}
                  >
                    Upset Finder
                  </Link>
                </motion.div>
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.29 }}>
                  <Link
                    href="/tools/odds-heatmap"
                    className="block px-3 py-2.5 text-sm font-medium text-white/60 rounded-lg transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10"
                    onClick={onClose}
                  >
                    Odds Heatmap
                  </Link>
                </motion.div>
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.33 }}>
                  <Link
                    href="/parlays/history"
                    className="block px-3 py-2.5 text-sm font-medium text-white/60 rounded-lg transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10"
                    onClick={onClose}
                  >
                    History
                  </Link>
                </motion.div>
              </>
            ) : (
              <>
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }}>
                  <Link
                    href="/sports"
                    className="block px-3 py-2.5 text-sm font-medium text-white/60 rounded-lg transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10"
                    onClick={onClose}
                  >
                    Sports
                  </Link>
                </motion.div>
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.15 }}>
                  <Link
                    href="/#features"
                    className="block px-3 py-2.5 text-sm font-medium text-white/60 rounded-lg transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10"
                    onClick={onClose}
                  >
                    Features
                  </Link>
                </motion.div>
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}>
                  <Link
                    href="/analysis"
                    className="block px-3 py-2.5 text-sm font-medium text-white/60 rounded-lg transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10"
                    onClick={onClose}
                  >
                    Analysis
                  </Link>
                </motion.div>
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.22 }}>
                  <Link
                    href="/pg-101"
                    className="block px-3 py-2.5 text-sm font-medium text-white/60 rounded-lg transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10 flex items-center gap-2"
                    onClick={onClose}
                  >
                    <Book className="h-4 w-4" />
                    PG-101
                  </Link>
                </motion.div>
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.225 }}>
                  <Link
                    href="/tutorial"
                    className="block px-3 py-2.5 text-sm font-medium text-white/60 rounded-lg transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10"
                    onClick={onClose}
                  >
                    Tutorial
                  </Link>
                </motion.div>
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.23 }}>
                  <Link
                    href="/development-news"
                    className="block px-3 py-2.5 text-sm font-medium text-white/60 rounded-lg transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10 flex items-center gap-2"
                    onClick={onClose}
                  >
                    <Rss className="h-4 w-4" />
                    Development News
                  </Link>
                </motion.div>
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.24 }}>
                  <Link
                    href="/affiliates"
                    className="block px-3 py-2.5 text-sm font-medium text-white/60 rounded-lg transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10 flex items-center gap-2"
                    onClick={onClose}
                  >
                    <Users className="h-4 w-4" />
                    Affiliates
                  </Link>
                </motion.div>
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.25 }}>
                  <Link
                    href="/pricing"
                    className="block px-3 py-2.5 text-sm font-medium text-[#00DD55] rounded-lg transition-all hover:text-[#22DD66] hover:bg-[#00DD55]/10 flex items-center gap-2"
                    onClick={onClose}
                  >
                    <Crown className="h-4 w-4" />
                    Pricing
                  </Link>
                </motion.div>
              </>
            )}

            <div className="flex flex-col gap-2 pt-4 border-t border-white/10">
              {!loading && isAuthed ? (
                <>
                  <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.25 }}>
                    <Link
                      href="/profile"
                      className="flex items-center gap-2 text-sm text-white/60 px-3 py-2 hover:text-[#00DD55] transition-colors"
                      onClick={onClose}
                    >
                      <User className="h-4 w-4" />
                      <span className="truncate">{userEmail}</span>
                    </Link>
                  </motion.div>
                  <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}>
                    <button
                      className="w-full px-4 py-2.5 text-sm font-medium text-red-400 border border-red-500/30 rounded-lg hover:bg-red-500/10 transition-all"
                      onClick={onSignOut}
                    >
                      Sign Out
                    </button>
                  </motion.div>
                </>
              ) : (
                <>
                  <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.25 }}>
                    <button
                      className="w-full px-4 py-2.5 text-sm font-medium text-white/60 border border-[#00DD55]/50 rounded-lg hover:border-[#22DD66] hover:text-[#00DD55] transition-all"
                      onClick={onSignIn}
                    >
                      Sign In
                    </button>
                  </motion.div>
                  <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}>
                    <button
                      className="w-full px-4 py-2.5 text-sm font-bold text-black bg-[#00DD55] rounded-lg hover:bg-[#22DD66] transition-all"
                      style={{
                        boxShadow: "0 0 6px #00DD55, 0 0 12px #00BB44",
                      }}
                      onClick={onGetStarted}
                    >
                      Get Started
                    </button>
                  </motion.div>
                </>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}


