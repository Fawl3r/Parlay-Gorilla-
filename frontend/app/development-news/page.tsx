"use client"

import { motion } from "framer-motion"
import Image from "next/image"
import Link from "next/link"
import { ArrowRight, Rss, Sparkles } from "lucide-react"
import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import { SportBackground } from "@/components/games/SportBackground"

type NewsItem = {
  date: string
  title: string
  summary: string
  highlights: string[]
}

const NEWS: NewsItem[] = [
  {
    date: "Jan 2026",
    title: "Billing page improvements",
    summary:
      "We've streamlined the Plan & Billing page to make it easier to choose the right subscription or purchase credits.",
    highlights: [
      "Lifetime upgrade option is now available on the billing page when logged in.",
      "Subscription plans and credit packs are now clearly separated into their own sections.",
      "All payment buttons now correctly redirect to Stripe checkout for a smooth purchase experience.",
      "Updated pricing: Monthly $39.99, Annual $399.99, Lifetime $499.99.",
    ],
  },
  {
    date: "Dec 2025",
    title: "Shareable parlays (with likes)",
    summary:
      "You can now share a parlay link with friends and quickly see simple engagement like likes and views.",
    highlights: [
      "One share link that works on desktop and mobile.",
      "Optional note + AI summary included on the shared parlay page (when available).",
      "Tap the heart to like a shared parlay and see the like count update.",
    ],
  },
  {
    date: "Dec 2025",
    title: "Parlay History is live",
    summary:
      "Track your past parlays in one place and review how each slip (and leg) performed.",
    highlights: [
      "Quick stats for hits, misses, pending, and hit rate.",
      "Expand a parlay to scan every leg in seconds.",
      "Jump into the full analysis view when you want the details.",
    ],
  },
  {
    date: "Dec 2025",
    title: "Gorilla Upset Finder (Premium)",
    summary:
      "Find plus-money underdogs where the model sees a meaningful edge — with filters that keep the list focused.",
    highlights: [
      "Filter by sport, risk tier, and minimum edge.",
      "NFL week selector so you can research the slate you care about.",
      "Reasoning notes included to help explain the signal (in plain English).",
    ],
  },
  {
    date: "Dec 2025",
    title: "Your Profile got smarter",
    summary:
      "Your profile now brings stats, badges, and billing into one clean hub so you can see progress at a glance.",
    highlights: [
      "Usage stats so you understand how you’re using the app over time.",
      "Badges for milestones as you build and analyze.",
      "Subscription + billing history in one place.",
    ],
  },
  {
    date: "Dec 2025",
    title: "Easier bug reporting (so we can fix things faster)",
    summary:
      "Reporting an issue is now a simple form — with helpful page context captured automatically.",
    highlights: [
      "Choose severity so urgent issues get prioritized.",
      "Optional steps/expected/actual fields to reduce back-and-forth.",
      "We capture page path + URL (without secrets) to speed up triage.",
    ],
  },
  {
    date: "Dec 2025",
    title: "New: Click-by-click Tutorial",
    summary:
      "A guided tutorial helps new users understand where to click and what the key numbers mean.",
    highlights: [
      "Quick Start section to generate your first parlay fast.",
      "Plain-English glossary for hit probability, confidence, and risk profiles.",
      "Troubleshooting tips for timeouts and empty slates.",
    ],
  },
]

function NewsCard({ item, index }: { item: NewsItem; index: number }) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.08 }}
      className="relative rounded-2xl bg-black/25 border border-white/10 backdrop-blur-xl overflow-hidden"
    >
      {/* Accent glow */}
      <div className="absolute inset-0 opacity-40 pointer-events-none">
        <div className="absolute -top-24 -left-24 h-56 w-56 rounded-full bg-emerald-500/20 blur-3xl" />
        <div className="absolute -bottom-24 -right-24 h-56 w-56 rounded-full bg-cyan-500/15 blur-3xl" />
      </div>

      <div className="relative p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-3">
          <div className="inline-flex items-center gap-2 text-xs font-semibold text-emerald-300">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            {item.date}
          </div>
        </div>

        <h2 className="text-xl md:text-2xl font-bold text-white mb-2">{item.title}</h2>
        <p className="text-gray-300/90 text-sm leading-relaxed mb-4">{item.summary}</p>

        <ul className="space-y-2">
          {item.highlights.map((h) => (
            <li key={h} className="flex gap-3 text-sm text-gray-200/90">
              <span className="mt-2 w-1.5 h-1.5 rounded-full bg-emerald-400 flex-shrink-0" />
              <span>{h}</span>
            </li>
          ))}
        </ul>
      </div>
    </motion.article>
  )
}

export default function DevelopmentNewsPage() {
  return (
    <div className="min-h-screen flex flex-col relative">
      {/* Background */}
      <SportBackground imageUrl="/images/devback.png" overlay="strong" fit="cover" />

      <div className="relative z-10 min-h-screen flex flex-col">
        <Header />

        <main className="flex-1 py-10 md:py-14">
          <div className="container mx-auto px-4 max-w-6xl">
            {/* Hero */}
            <motion.section
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45 }}
              className="grid gap-8 lg:grid-cols-[1.1fr,0.9fr] items-center"
            >
              <div>
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-black/30 border border-white/10 text-gray-200 text-sm backdrop-blur">
                  <Rss className="h-4 w-4 text-emerald-400" />
                  Development News
                </div>

                <h1 className="text-4xl md:text-5xl font-black mt-4 mb-3 leading-tight">
                  <span className="text-white">What’s </span>
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
                    New
                  </span>
                </h1>

                <p className="text-gray-200/80 max-w-2xl leading-relaxed">
                  Friendly updates about improvements and new features. We keep this page non-technical and we won’t share
                  proprietary details — just what you can feel and use.
                </p>

                <div className="mt-5 flex flex-wrap gap-2">
                  <div className="inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-black/25 border border-white/10 text-gray-200 text-xs backdrop-blur">
                    <Sparkles className="h-4 w-4 text-emerald-400" />
                    Social sharing
                  </div>
                  <div className="inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-black/25 border border-white/10 text-gray-200 text-xs backdrop-blur">
                    <Sparkles className="h-4 w-4 text-cyan-300" />
                    Parlay history
                  </div>
                  <div className="inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-black/25 border border-white/10 text-gray-200 text-xs backdrop-blur">
                    <Sparkles className="h-4 w-4 text-emerald-300" />
                    Upset Finder
                  </div>
                  <div className="inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-black/25 border border-white/10 text-gray-200 text-xs backdrop-blur">
                    <Sparkles className="h-4 w-4 text-purple-300" />
                    Better feedback loop
                  </div>
                </div>

                <div className="mt-6 flex flex-wrap items-center gap-3">
                  <Link
                    href="/report-bug"
                    className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-emerald-500 text-black font-bold hover:bg-emerald-400 transition-colors"
                  >
                    Report a bug
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                  <Link
                    href="/analysis"
                    className="inline-flex items-center gap-2 px-5 py-3 rounded-xl border border-white/15 bg-black/20 text-white font-semibold hover:bg-white/10 transition-colors"
                  >
                    Browse Game Analysis
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              </div>

              {/* Hero image */}
              <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.45, delay: 0.1 }}
                className="relative"
              >
                <div className="relative aspect-[4/3] w-full overflow-hidden rounded-3xl border border-emerald-500/25 bg-black/30 backdrop-blur shadow-[0_0_40px_rgba(0,221,85,0.10)]">
                  <Image
                    src="/images/devnews.png"
                    alt="Parlay Gorilla development news"
                    fill
                    className="object-cover"
                    priority
                  />
                  <div className="absolute inset-0 bg-gradient-to-tr from-black/50 via-transparent to-black/10" />
                </div>
              </motion.div>
            </motion.section>

            {/* Updates */}
            <div className="mt-10 md:mt-12">
              <div className="flex items-end justify-between gap-4 mb-5">
                <div>
                  <h2 className="text-2xl md:text-3xl font-black text-white">Latest updates</h2>
                  <p className="text-sm text-gray-200/70 mt-1">Release notes written for users — not engineers.</p>
                </div>
                <div className="hidden md:flex items-center gap-2 text-xs text-gray-200/70">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  Updated regularly
                </div>
              </div>

              <div className="grid gap-6">
                {NEWS.map((item, idx) => (
                  <NewsCard key={`${item.date}-${item.title}`} item={item} index={idx} />
                ))}
              </div>

              <div className="mt-10 text-center text-sm text-gray-200/70">
                Want to help improve the app? Use{" "}
                <Link href="/report-bug" className="text-emerald-300 hover:text-emerald-200 hover:underline">
                  Report a bug
                </Link>{" "}
                to send feedback.
              </div>
            </div>
          </div>
        </main>

        <Footer />
      </div>
    </div>
  )
}



