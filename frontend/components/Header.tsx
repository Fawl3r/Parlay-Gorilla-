"use client"

import { LogOut, User, Menu, Crown } from "lucide-react"
import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { useRouter, usePathname } from "next/navigation"
import Link from "next/link"
import Image from "next/image"
import { useAuth } from "@/lib/auth-context"
import { useSubscription } from "@/lib/subscription-context"

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [dashboardMenuOpen, setDashboardMenuOpen] = useState(false)
  const router = useRouter()
  const pathname = usePathname()
  const { user, loading, signOut } = useAuth()
  const { isPremium } = useSubscription()
  const isOnDashboard = pathname?.startsWith("/app")

  // Close dashboard menu when navigating away or pathname changes
  useEffect(() => {
    setDashboardMenuOpen(false)
    setMobileMenuOpen(false)
  }, [pathname])

  const handleGetStarted = () => {
    setMobileMenuOpen(false)
    if (user) {
      router.push("/app")
    } else {
      router.push("/auth/signup")
    }
  }

  const handleSignIn = () => {
    setMobileMenuOpen(false)
    router.push("/auth/login")
  }

  const handleSignOut = async () => {
    setMobileMenuOpen(false)
    await signOut()
    router.push("/auth/login")
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b border-gray-800 dark:border-white/10 bg-gray-900/95 dark:bg-[#0a0a0f]/90 backdrop-blur-xl">
      <div className="container flex h-16 items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-3 no-underline">
          <motion.div
            className="flex items-center gap-3 cursor-pointer"
            whileHover={{ scale: 1.02 }}
            transition={{ duration: 0.2 }}
          >
            <div
              className="relative flex h-10 w-10 items-center justify-center rounded-xl overflow-hidden"
              style={{
                boxShadow: "0 4px 20px rgba(139, 92, 246, 0.4), 0 0 40px rgba(59, 130, 246, 0.3)",
              }}
            >
              <Image
                src="/logoo.png"
                alt="Parlay Gorilla Logo"
                width={40}
                height={40}
                className="object-contain"
                priority
              />
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-bold leading-tight text-transparent bg-clip-text bg-gradient-to-r from-emerald-600 dark:from-emerald-400 to-green-600 dark:to-green-400">
                Parlay Gorilla
              </span>
              <span className="text-[10px] font-medium text-gray-300 dark:text-gray-500 tracking-wide">AI PARLAY ENGINE</span>
            </div>
          </motion.div>
        </Link>

        <nav className="hidden md:flex items-center gap-6">
          {user ? (
            /* When logged in, nav links are in the hamburger menu next to theme toggle */
            null
          ) : (
            <>
              <Link
                href="/sports"
                className="text-sm font-medium text-gray-300 dark:text-gray-400 transition-all hover:text-emerald-400 dark:hover:text-emerald-400"
              >
                Sports
              </Link>
              <a
                href="/#features"
                className="text-sm font-medium text-gray-300 dark:text-gray-400 transition-all hover:text-emerald-400 dark:hover:text-emerald-400"
              >
                Features
              </a>
              <Link
                href="/analysis"
                className="text-sm font-medium text-gray-300 dark:text-gray-400 transition-all hover:text-emerald-400 dark:hover:text-emerald-400"
              >
                Analysis
              </Link>
              <Link
                href="/premium"
                className="text-sm font-medium text-emerald-400 dark:text-emerald-400 transition-all hover:text-emerald-300 dark:hover:text-emerald-300"
              >
                Premium
              </Link>
            </>
          )}
        </nav>

        <div className="flex items-center gap-2">
          {/* Hamburger Menu Button - Desktop (when logged in) */}
          {!loading && user && (
            <div className="hidden md:block relative">
              <button
                onClick={() => setDashboardMenuOpen(!dashboardMenuOpen)}
                className="p-2 rounded-lg text-gray-300 dark:text-gray-400 hover:text-emerald-400 dark:hover:text-emerald-400 hover:bg-emerald-500/10 transition-all"
                aria-label="Toggle menu"
              >
                <Menu className="h-5 w-5" />
              </button>
              
              <AnimatePresence>
                {dashboardMenuOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.2 }}
                    className="absolute top-full right-0 mt-2 w-56 bg-gray-900 dark:bg-[#0a0a0f] border border-gray-800 dark:border-white/10 rounded-lg shadow-xl overflow-hidden z-50"
                    onMouseLeave={() => setDashboardMenuOpen(false)}
                  >
                    <Link
                      href="/"
                      className="block px-4 py-2.5 text-sm font-medium text-gray-300 dark:text-gray-400 transition-all hover:text-emerald-400 dark:hover:text-emerald-400 hover:bg-emerald-500/10"
                      onClick={() => setDashboardMenuOpen(false)}
                    >
                      Home
                    </Link>
                    <Link
                      href="/analysis"
                      className="block px-4 py-2.5 text-sm font-medium text-gray-300 dark:text-gray-400 transition-all hover:text-emerald-400 dark:hover:text-emerald-400 hover:bg-emerald-500/10"
                      onClick={() => setDashboardMenuOpen(false)}
                    >
                      Game Analytics
                    </Link>
                        <Link
                          href="/app"
                          className="block px-4 py-2.5 text-sm font-medium text-gray-300 dark:text-gray-400 transition-all hover:text-emerald-400 dark:hover:text-emerald-400 hover:bg-emerald-500/10"
                          onClick={() => setDashboardMenuOpen(false)}
                        >
                          Gorilla Dashboard
                        </Link>
                    <div className="border-t border-gray-800 dark:border-white/10 my-1" />
                    <Link
                      href="/pricing"
                      className="block px-4 py-2.5 text-sm font-medium text-emerald-400 dark:text-emerald-400 transition-all hover:text-emerald-300 dark:hover:text-emerald-300 hover:bg-emerald-500/10 flex items-center gap-2"
                      onClick={() => setDashboardMenuOpen(false)}
                    >
                      <Crown className="h-4 w-4" />
                      {isPremium ? "Manage Subscription" : "Upgrade Subscription"}
                    </Link>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}
          
          {!loading && user ? (
            <>
              <Link
                href="/profile"
                className="hidden md:flex items-center gap-2 text-sm text-gray-300 dark:text-gray-400 hover:text-emerald-400 dark:hover:text-emerald-400 transition-colors"
              >
                <User className="h-4 w-4" />
                <span className="max-w-[120px] truncate">{user.email}</span>
              </Link>
              <button
                className="hidden md:inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-300 dark:text-gray-400 border border-gray-700 dark:border-white/10 rounded-lg hover:border-red-500/50 hover:text-red-400 dark:hover:text-red-400 transition-all"
                onClick={handleSignOut}
              >
                <LogOut className="h-4 w-4" />
                Sign Out
              </button>
            </>
          ) : (
            <>
              <button
                className="hidden md:inline-flex px-4 py-2 text-sm font-medium text-gray-300 dark:text-gray-300 border border-gray-700 dark:border-white/10 rounded-lg hover:border-emerald-500/50 hover:text-emerald-400 dark:hover:text-emerald-400 transition-all"
                onClick={handleSignIn}
              >
                Sign In
              </button>
              <button
                className="hidden md:inline-flex px-4 py-2 text-sm font-bold text-white dark:text-black bg-gradient-to-r from-emerald-600 dark:from-emerald-400 to-green-600 dark:to-green-400 rounded-lg hover:from-emerald-500 dark:hover:from-emerald-300 hover:to-green-500 dark:hover:to-green-300 transition-all"
                onClick={handleGetStarted}
              >
                Get Started
              </button>
            </>
          )}
          {/* Animated Hamburger Menu Button - Mobile */}
          <button
            className="md:hidden relative p-2 w-10 h-10 flex flex-col items-center justify-center gap-1.5 group"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            <motion.span
              className="block w-6 h-0.5 bg-gray-400 group-hover:bg-emerald-400 transition-colors rounded-full"
              animate={{
                rotate: mobileMenuOpen ? 45 : 0,
                y: mobileMenuOpen ? 8 : 0,
              }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
            />
            <motion.span
              className="block w-6 h-0.5 bg-gray-400 group-hover:bg-emerald-400 transition-colors rounded-full"
              animate={{
                opacity: mobileMenuOpen ? 0 : 1,
                scale: mobileMenuOpen ? 0 : 1,
              }}
              transition={{ duration: 0.2 }}
            />
            <motion.span
              className="block w-6 h-0.5 bg-gray-400 group-hover:bg-emerald-400 transition-colors rounded-full"
              animate={{
                rotate: mobileMenuOpen ? -45 : 0,
                y: mobileMenuOpen ? -8 : 0,
              }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
            />
          </button>
        </div>
      </div>

      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="border-t border-gray-700 dark:border-white/10 md:hidden bg-gray-900 dark:bg-[#0a0a0f] overflow-hidden"
          >
            <motion.div
              initial={{ y: -20 }}
              animate={{ y: 0 }}
              exit={{ y: -20 }}
              transition={{ duration: 0.3, delay: 0.1 }}
              className="container space-y-1 px-4 py-4"
            >
              {user ? (
                <>
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.05 }}
                  >
                    <Link
                      href="/"
                      className="block px-3 py-2.5 text-sm font-medium text-gray-400 rounded-lg transition-all hover:text-emerald-400 hover:bg-emerald-500/10"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Home
                    </Link>
                  </motion.div>
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 }}
                  >
                    <Link
                      href="/analysis"
                      className="block px-3 py-2.5 text-sm font-medium text-gray-400 rounded-lg transition-all hover:text-emerald-400 hover:bg-emerald-500/10"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Game Analytics
                    </Link>
                  </motion.div>
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.15 }}
                  >
                    <Link
                      href="/app"
                      className="block px-3 py-2.5 text-sm font-medium text-gray-400 rounded-lg transition-all hover:text-emerald-400 hover:bg-emerald-500/10"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Gorilla Dashboard
                    </Link>
                  </motion.div>
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 }}
                  >
                    <div className="border-t border-gray-800 dark:border-white/10 my-2" />
                  </motion.div>
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.25 }}
                  >
                    <Link
                      href="/pricing"
                      className="block px-3 py-2.5 text-sm font-medium text-emerald-400 rounded-lg transition-all hover:text-emerald-300 hover:bg-emerald-500/10 flex items-center gap-2"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      <Crown className="h-4 w-4" />
                      {isPremium ? "Manage Subscription" : "Upgrade Subscription"}
                    </Link>
                  </motion.div>
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.25 }}
                  >
                    <Link
                      href="/tools/odds-heatmap"
                      className="block px-3 py-2.5 text-sm font-medium text-gray-400 rounded-lg transition-all hover:text-emerald-400 hover:bg-emerald-500/10"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Odds Heatmap
                    </Link>
                  </motion.div>
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 }}
                  >
                    <Link
                      href="/parlays/history"
                      className="block px-3 py-2.5 text-sm font-medium text-gray-400 rounded-lg transition-all hover:text-emerald-400 hover:bg-emerald-500/10"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      History
                    </Link>
                  </motion.div>
                </>
              ) : (
                <>
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 }}
                  >
                    <Link
                      href="/sports"
                      className="block px-3 py-2.5 text-sm font-medium text-gray-400 rounded-lg transition-all hover:text-emerald-400 hover:bg-emerald-500/10"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Sports
                    </Link>
                  </motion.div>
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.15 }}
                  >
                    <a
                      href="/#features"
                      className="block px-3 py-2.5 text-sm font-medium text-gray-400 rounded-lg transition-all hover:text-emerald-400 hover:bg-emerald-500/10"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Features
                    </a>
                  </motion.div>
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 }}
                  >
                    <Link
                      href="/analysis"
                      className="block px-3 py-2.5 text-sm font-medium text-gray-400 rounded-lg transition-all hover:text-emerald-400 hover:bg-emerald-500/10"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Analysis
                    </Link>
                  </motion.div>
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.25 }}
                  >
                    <Link
                      href="/premium"
                      className="block px-3 py-2.5 text-sm font-medium text-emerald-400 rounded-lg transition-all hover:text-emerald-300 hover:bg-emerald-500/10"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      🦍 Premium
                    </Link>
                  </motion.div>
                </>
              )}
              <div className="flex flex-col gap-2 pt-4 border-t border-white/10">
                {!loading && user ? (
                  <>
                    <motion.div
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.25 }}
                    >
                      <Link
                        href="/profile"
                        className="flex items-center gap-2 text-sm text-gray-400 px-3 py-2 hover:text-emerald-400 transition-colors"
                        onClick={() => setMobileMenuOpen(false)}
                      >
                        <User className="h-4 w-4" />
                        <span className="truncate">{user.email}</span>
                      </Link>
                    </motion.div>
                    <motion.div
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.3 }}
                    >
                      <button
                        className="w-full px-4 py-2.5 text-sm font-medium text-red-400 border border-red-500/30 rounded-lg hover:bg-red-500/10 transition-all"
                        onClick={handleSignOut}
                      >
                        Sign Out
                      </button>
                    </motion.div>
                  </>
                ) : (
                  <>
                    <motion.div
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.25 }}
                    >
                      <button
                        className="w-full px-4 py-2.5 text-sm font-medium text-gray-300 border border-white/10 rounded-lg hover:border-emerald-500/50 transition-all"
                        onClick={handleSignIn}
                      >
                        Sign In
                      </button>
                    </motion.div>
                    <motion.div
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.3 }}
                    >
                      <button
                        className="w-full px-4 py-2.5 text-sm font-bold text-black bg-gradient-to-r from-emerald-400 to-green-400 rounded-lg hover:from-emerald-300 hover:to-green-300 transition-all"
                        onClick={handleGetStarted}
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
    </header>
  )
}

