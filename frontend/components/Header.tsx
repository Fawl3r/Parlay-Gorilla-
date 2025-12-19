"use client"

import { LogOut, User, Menu, Crown, Users, Book, Rss } from "lucide-react"
import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { useRouter, usePathname } from "next/navigation"
import Link from "next/link"
import { useAuth } from "@/lib/auth-context"
import { useSubscription } from "@/lib/subscription-context"
import { ParlayGorillaLogo } from "./ParlayGorillaLogo"
import { DashboardMenuDropdown } from "@/components/header/DashboardMenuDropdown"
import { HeaderMobileMenu } from "@/components/header/HeaderMobileMenu"

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [dashboardMenuOpen, setDashboardMenuOpen] = useState(false)
  const router = useRouter()
  const pathname = usePathname()
  const { user, loading, signOut } = useAuth()
  const { isPremium } = useSubscription()

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
    <header className="sticky top-0 z-50 w-full border-b border-[#00DD55]/20 bg-[#0A0F0A]/95 backdrop-blur-xl">
      <div className="container flex h-16 items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-3 no-underline">
          <motion.div
            whileHover={{ scale: 1.02 }}
            transition={{ duration: 0.2 }}
          >
            <ParlayGorillaLogo size="md" />
          </motion.div>
        </Link>

        <nav className="hidden md:flex items-center gap-6">
          {user ? (
            <>
              <Link
                href="/"
                className="text-sm font-medium text-white/60 transition-all hover:text-[#00DD55]"
              >
                Home
              </Link>
              <Link
                href="/analysis"
                className="text-sm font-medium text-white/60 transition-all hover:text-[#00DD55]"
              >
                Game Analytics
              </Link>
              <Link
                href="/pg-101"
                className="text-sm font-medium text-white/60 transition-all hover:text-[#00DD55] flex items-center gap-1"
              >
                <Book className="h-4 w-4" />
                PG-101
              </Link>
              <Link
                href="/tutorial"
                className="text-sm font-medium text-white/60 transition-all hover:text-[#00DD55]"
              >
                Tutorial
              </Link>
              <Link
                href="/development-news"
                className="text-sm font-medium text-white/60 transition-all hover:text-[#00DD55] flex items-center gap-1"
              >
                <Rss className="h-4 w-4" />
                Development News
              </Link>
              <Link
                href="/app"
                className="text-sm font-medium text-white/60 transition-all hover:text-[#00DD55]"
              >
                Gorilla Dashboard
              </Link>
              <Link
                href="/affiliates"
                className="text-sm font-medium text-white/60 transition-all hover:text-[#00DD55] flex items-center gap-1"
              >
                <Users className="h-4 w-4" />
                Affiliates
              </Link>
            </>
          ) : (
            <>
              <Link
                href="/sports"
                className="text-sm font-medium text-white/60 transition-all hover:text-[#00DD55]"
              >
                Sports
              </Link>
              <Link
                href="/#features"
                className="text-sm font-medium text-white/60 transition-all hover:text-[#00DD55]"
              >
                Features
              </Link>
              <Link
                href="/analysis"
                className="text-sm font-medium text-white/60 transition-all hover:text-[#00DD55]"
              >
                Analysis
              </Link>
              <Link
                href="/pg-101"
                className="text-sm font-medium text-white/60 transition-all hover:text-[#00DD55] flex items-center gap-1"
              >
                <Book className="h-4 w-4" />
                PG-101
              </Link>
              <Link
                href="/tutorial"
                className="text-sm font-medium text-white/60 transition-all hover:text-[#00DD55]"
              >
                Tutorial
              </Link>
              <Link
                href="/development-news"
                className="text-sm font-medium text-white/60 transition-all hover:text-[#00DD55] flex items-center gap-1"
              >
                <Rss className="h-4 w-4" />
                Development News
              </Link>
              <Link
                href="/affiliates"
                className="text-sm font-medium text-white/60 transition-all hover:text-[#00DD55] flex items-center gap-1"
              >
                <Users className="h-4 w-4" />
                Affiliates
              </Link>
              <Link
                href="/pricing"
                className="text-sm font-medium text-[#00DD55] transition-all hover:text-[#22DD66] flex items-center gap-1"
              >
                <Crown className="h-4 w-4" />
                Pricing
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
                className="p-2 rounded-lg text-white/60 hover:text-[#00DD55] hover:bg-[#00DD55]/10 transition-all"
                aria-label="Toggle menu"
              >
                <Menu className="h-5 w-5" />
              </button>
              
              <DashboardMenuDropdown
                isOpen={dashboardMenuOpen}
                isPremium={isPremium}
                onClose={() => setDashboardMenuOpen(false)}
              />
            </div>
          )}
          
          {!loading && user ? (
            <>
              <Link
                href="/profile"
                className="hidden md:flex items-center gap-2 text-sm text-white/60 hover:text-[#00DD55] transition-colors"
              >
                <User className="h-4 w-4" />
                <span className="max-w-[120px] truncate">{user.email}</span>
              </Link>
              <button
                className="hidden md:inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white/60 border border-white/10 rounded-lg hover:border-red-500/50 hover:text-red-400 transition-all"
                onClick={handleSignOut}
              >
                <LogOut className="h-4 w-4" />
                Sign Out
              </button>
            </>
          ) : (
            <>
              <button
                className="hidden md:inline-flex px-4 py-2 text-sm font-medium text-white/60 border border-[#00DD55]/50 rounded-lg hover:border-[#22DD66] hover:text-[#00DD55] transition-all"
                onClick={handleSignIn}
              >
                Sign In
              </button>
              <button
                className="hidden md:inline-flex px-4 py-2 text-sm font-bold text-black bg-[#00DD55] rounded-lg hover:bg-[#22DD66] transition-all"
                style={{
                  boxShadow: '0 0 6px #00DD55, 0 0 12px #00BB44'
                }}
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
              className="block w-6 h-0.5 bg-white/60 group-hover:bg-[#00DD55] transition-colors rounded-full"
              animate={{
                rotate: mobileMenuOpen ? 45 : 0,
                y: mobileMenuOpen ? 8 : 0,
              }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
            />
            <motion.span
              className="block w-6 h-0.5 bg-white/60 group-hover:bg-[#00DD55] transition-colors rounded-full"
              animate={{
                opacity: mobileMenuOpen ? 0 : 1,
                scale: mobileMenuOpen ? 0 : 1,
              }}
              transition={{ duration: 0.2 }}
            />
            <motion.span
              className="block w-6 h-0.5 bg-white/60 group-hover:bg-[#00DD55] transition-colors rounded-full"
              animate={{
                rotate: mobileMenuOpen ? -45 : 0,
                y: mobileMenuOpen ? -8 : 0,
              }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
            />
          </button>
        </div>
      </div>

      <HeaderMobileMenu
        isOpen={mobileMenuOpen}
        userEmail={user?.email ?? null}
        loading={loading}
        isPremium={isPremium}
        onClose={() => setMobileMenuOpen(false)}
        onSignOut={handleSignOut}
        onSignIn={handleSignIn}
        onGetStarted={handleGetStarted}
      />
    </header>
  )
}

