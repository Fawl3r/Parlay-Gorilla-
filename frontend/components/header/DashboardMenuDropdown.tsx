"use client"

import { AnimatePresence, motion } from "framer-motion"
import Link from "next/link"
import { Book, Crown, Users } from "lucide-react"

type DashboardMenuDropdownProps = {
  isOpen: boolean
  isPremium: boolean
  onClose: () => void
}

export function DashboardMenuDropdown({ isOpen, isPremium, onClose }: DashboardMenuDropdownProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
          className="absolute top-full right-0 mt-2 w-56 bg-[#0A0F0A] border border-[#00DD55]/20 rounded-lg shadow-xl overflow-hidden z-50"
          onMouseLeave={onClose}
        >
          <Link
            href="/"
            className="block px-4 py-2.5 text-sm font-medium text-white/60 transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10"
            onClick={onClose}
          >
            Home
          </Link>
          <Link
            href="/analysis"
            className="block px-4 py-2.5 text-sm font-medium text-white/60 transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10"
            onClick={onClose}
          >
            Game Analytics
          </Link>
          <Link
            href="/pg-101"
            className="block px-4 py-2.5 text-sm font-medium text-white/60 transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10 flex items-center gap-2"
            onClick={onClose}
          >
            <Book className="h-4 w-4" />
            PG-101
          </Link>
          <Link
            href="/tutorial"
            className="block px-4 py-2.5 text-sm font-medium text-white/60 transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10"
            onClick={onClose}
          >
            Tutorial
          </Link>
          <Link
            href="/app"
            className="block px-4 py-2.5 text-sm font-medium text-white/60 transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10"
            onClick={onClose}
          >
            Gorilla Dashboard
          </Link>
          <Link
            href="/social"
            className="block px-4 py-2.5 text-sm font-medium text-white/60 transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10"
            onClick={onClose}
          >
            Social Feed
          </Link>
          <Link
            href="/parlays/same-game"
            className="block px-4 py-2.5 text-sm font-medium text-white/60 transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10"
            onClick={onClose}
          >
            Same-Game Builder
          </Link>
          <Link
            href="/parlays/round-robin"
            className="block px-4 py-2.5 text-sm font-medium text-white/60 transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10"
            onClick={onClose}
          >
            Round Robin Builder
          </Link>
          <Link
            href="/parlays/teasers"
            className="block px-4 py-2.5 text-sm font-medium text-white/60 transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10"
            onClick={onClose}
          >
            Teaser Builder
          </Link>
          <Link
            href="/tools/upset-finder"
            className="block px-4 py-2.5 text-sm font-medium text-white/60 transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10"
            onClick={onClose}
          >
            Upset Finder
          </Link>
          <Link
            href="/tools/odds-heatmap"
            className="block px-4 py-2.5 text-sm font-medium text-white/60 transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10"
            onClick={onClose}
          >
            Odds Heatmap
          </Link>
          <div className="border-t border-[#00DD55]/20 my-1" />
          <Link
            href="/affiliates"
            className="block px-4 py-2.5 text-sm font-medium text-white/60 transition-all hover:text-[#00DD55] hover:bg-[#00DD55]/10 flex items-center gap-2"
            onClick={onClose}
          >
            <Users className="h-4 w-4" />
            Affiliate Program
          </Link>
          <Link
            href="/pricing"
            className="block px-4 py-2.5 text-sm font-medium text-[#00DD55] transition-all hover:text-[#22DD66] hover:bg-[#00DD55]/10 flex items-center gap-2"
            onClick={onClose}
          >
            <Crown className="h-4 w-4" />
            {isPremium ? "Manage Subscription" : "Upgrade Subscription"}
          </Link>
        </motion.div>
      )}
    </AnimatePresence>
  )
}




