"use client"

import { motion } from "framer-motion"
import Image from "next/image"
import Link from "next/link"
import { Activity, ArrowRight, Brain, Radar, Shield, Target } from "lucide-react"

import { StatChip } from "@/app/pg-101/_components/StatChip"

export function HeroSection() {
  return (
    <section className="relative overflow-hidden">
      <div className="absolute inset-0">
        <Image
          src="/images/hero.png"
          alt="Parlay Gorilla predictive engine HUD"
          fill
          priority
          className="object-cover object-center"
          sizes="100vw"
        />
        <div className="absolute inset-0 bg-black/55" />
        <div className="absolute inset-0 bg-gradient-to-b from-black/70 via-black/45 to-[#0A0F0A]" />
      </div>

      <div className="container mx-auto px-4 pt-20 pb-14 md:pt-28 md:pb-20 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          <div className="lg:col-span-7">
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35 }}
              className="inline-flex items-center gap-2 rounded-full border border-[#00FF5E]/25 bg-black/35 px-4 py-2 backdrop-blur-md"
            >
              <Radar className="h-4 w-4 text-[#00FF5E]" />
              <span className="text-xs md:text-sm font-semibold text-emerald-200 tracking-wide">
                PG-101 • Predictive Engine Breakdown
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, delay: 0.05 }}
              className="mt-6 text-4xl md:text-6xl lg:text-7xl font-black text-white leading-[1.05]"
            >
              Stop betting the <span className="text-white/70">public.</span>
              <br />
              Start betting the <span className="text-neon-strong">math.</span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, delay: 0.1 }}
              className="mt-5 text-lg md:text-xl text-gray-200/90 max-w-2xl leading-relaxed"
            >
              Parlay Gorilla compares <span className="text-emerald-200 font-semibold">model probability</span> vs{" "}
              <span className="text-white/80">sportsbook implied probability</span> to find real edges—then builds a slip
              that fits your risk style.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, delay: 0.15 }}
              className="mt-8 flex flex-col sm:flex-row gap-3"
            >
              <Link
                href="/auth/signup"
                className="glow-neon inline-flex items-center justify-center gap-2 rounded-xl bg-[#00FF5E] px-6 py-3 text-black font-black hover:bg-[#22FF6E] transition-colors"
              >
                Get 2 Free Parlays
                <ArrowRight className="h-5 w-5" />
              </Link>
              <Link
                href="/app"
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-black/40 border border-white/15 px-6 py-3 text-white font-semibold hover:bg-black/55 transition-colors backdrop-blur-md"
              >
                Open Dashboard
                <ArrowRight className="h-5 w-5 text-[#00FF5E]" />
              </Link>
            </motion.div>

            <div className="mt-8 flex flex-wrap gap-2">
              {[
                { href: "#engine", label: "How the engine works" },
                { href: "#value", label: "Why it wins" },
                { href: "#different", label: "What’s different" },
                { href: "#onchain", label: "On-chain proof" },
              ].map((item) => (
                <a
                  key={item.href}
                  href={item.href}
                  className="rounded-full border border-white/10 bg-black/30 px-4 py-2 text-sm text-white/80 hover:text-white hover:border-[#00FF5E]/30 hover:bg-black/40 transition-colors backdrop-blur-md"
                >
                  {item.label}
                </a>
              ))}
            </div>
          </div>

          <div className="lg:col-span-5">
            <motion.div
              initial={{ opacity: 0, y: 18, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.45, delay: 0.12 }}
              className="relative rounded-3xl border border-[#00FF5E]/25 bg-black/45 backdrop-blur-xl p-6 overflow-hidden"
            >
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(0,221,85,0.18),transparent_55%),radial-gradient(circle_at_80%_60%,rgba(34,221,102,0.12),transparent_55%)]" />
              <div className="relative">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <Activity className="h-5 w-5 text-[#00FF5E]" />
                    <div className="text-white font-bold">Example Edge Scan</div>
                  </div>
                  <div className="text-xs text-white/60">LIVE DEMO</div>
                </div>

                <div className="mt-5 grid grid-cols-2 gap-3">
                  <StatChip label="Model win %" value="62%" tone="emerald" />
                  <StatChip label="Implied win %" value="54%" tone="cyan" />
                  <StatChip label="Edge" value="+8.0%" tone="emerald" />
                  <StatChip label="Confidence" value="78/100" tone="cyan" />
                </div>

                <div className="mt-6 rounded-2xl border border-white/10 bg-black/30 p-4">
                  <div className="text-xs text-white/60 uppercase tracking-wider">Edge meter</div>
                  <div className="mt-2 h-3 rounded-full bg-white/10 overflow-hidden">
                    <div className="h-full w-[72%] bg-gradient-to-r from-[#00FF5E] to-[#22FF6E] glow-neon" />
                  </div>
                  <div className="mt-3 flex items-center justify-between text-xs text-white/60">
                    <span>0%</span>
                    <span className="text-emerald-200 font-semibold">+8%</span>
                    <span>+12%</span>
                  </div>
                </div>

                <div className="mt-5 grid grid-cols-3 gap-2">
                  {[
                    { icon: Shield, label: "Risk-fit" },
                    { icon: Brain, label: "Explainable" },
                    { icon: Target, label: "EV-first" },
                  ].map((i) => (
                    <div
                      key={i.label}
                      className="rounded-2xl border border-white/10 bg-black/25 p-3 text-center"
                    >
                      <i.icon className="h-5 w-5 text-[#00FF5E] mx-auto" />
                      <div className="mt-1 text-[11px] text-white/70">{i.label}</div>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  )
}



