"use client";

import type { ComponentType } from "react";
import { motion } from "framer-motion";
import Image from "next/image";
import {
  ArrowRight,
  Clock,
  DollarSign,
  Gift,
  Share2,
  ShieldCheck,
  Sparkles,
  TrendingUp,
} from "lucide-react";

type StatChipProps = {
  label: string;
  value: string;
  icon: ComponentType<{ className?: string }>;
};

function StatChip({ label, value, icon: Icon }: StatChipProps) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-black/35 px-4 py-3 backdrop-blur-md">
      <div className="h-10 w-10 rounded-xl bg-[#00DD55]/10 border border-[#00DD55]/25 flex items-center justify-center">
        <Icon className="h-5 w-5 text-[#00DD55]" />
      </div>
      <div className="text-left">
        <div className="text-xl font-black text-white leading-tight">{value}</div>
        <div className="text-xs text-white/60">{label}</div>
      </div>
    </div>
  );
}

export type AffiliateHeroSectionProps = {
  ctaText: string;
  onJoinClick: () => void;
};

export function AffiliateHeroSection({ ctaText, onJoinClick }: AffiliateHeroSectionProps) {
  return (
    <section id="hero" className="relative overflow-hidden">
      <div className="absolute inset-0">
        <Image
          src="/images/aff.png"
          alt="Parlay Gorilla affiliate program"
          fill
          priority
          className="object-cover object-center"
          sizes="100vw"
        />
        <div className="absolute inset-0 bg-black/55" />
        <div className="absolute inset-0 bg-gradient-to-b from-black/70 via-black/45 to-[#0A0F0A]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(0,221,85,0.18),transparent_55%),radial-gradient(circle_at_85%_40%,rgba(34,221,102,0.14),transparent_55%)]" />
      </div>

      <div className="container mx-auto px-4 pt-20 pb-16 md:pt-28 md:pb-24 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          {/* Left copy */}
          <div className="lg:col-span-7">
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35 }}
              className="inline-flex items-center gap-2 rounded-full border border-[#00DD55]/25 bg-black/35 px-4 py-2 backdrop-blur-md"
            >
              <Share2 className="h-4 w-4 text-[#00DD55]" />
              <span className="text-xs md:text-sm font-semibold text-emerald-200 tracking-wide">
                Affiliate Program • Earn on every upgrade
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, delay: 0.05 }}
              className="mt-6 text-4xl md:text-6xl lg:text-7xl font-black text-white leading-[1.05]"
            >
              Turn sports fans into <span className="text-neon-strong">cashflow.</span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, delay: 0.1 }}
              className="mt-5 text-lg md:text-xl text-gray-200/90 max-w-2xl leading-relaxed"
            >
              Your audience starts with{" "}
              <span className="text-emerald-200 font-semibold">2 free parlays</span>. You earn when they
              subscribe or buy credit packs—up to{" "}
              <span className="text-emerald-200 font-bold">40%</span> per sale.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, delay: 0.15 }}
              className="mt-7 flex flex-wrap gap-3"
            >
              <StatChip label="First subscription" value="Up to 40%" icon={DollarSign} />
              <StatChip label="Recurring subs" value="Up to 10%" icon={TrendingUp} />
              <StatChip label="Credit packs" value="Up to 35%" icon={Gift} />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, delay: 0.2 }}
              className="mt-8 flex flex-col sm:flex-row gap-3"
            >
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={onJoinClick}
                className="glow-neon inline-flex items-center justify-center gap-2 rounded-xl bg-[#00DD55] px-7 py-3.5 text-black font-black hover:bg-[#22DD66] transition-colors"
              >
                {ctaText}
                <ArrowRight className="h-5 w-5" />
              </motion.button>
              <a
                href="#tiers"
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-black/40 border border-white/15 px-7 py-3.5 text-white font-semibold hover:bg-black/55 transition-colors backdrop-blur-md"
              >
                View tiers
                <ArrowRight className="h-5 w-5 text-[#00DD55]" />
              </a>
            </motion.div>

            <div className="mt-7 flex flex-wrap gap-2">
              {[
                { href: "#how", label: "How it works" },
                { href: "#tiers", label: "Commission tiers" },
                { href: "#benefits", label: "Why it converts" },
              ].map((item) => (
                <a
                  key={item.href}
                  href={item.href}
                  className="rounded-full border border-white/10 bg-black/30 px-4 py-2 text-sm text-white/80 hover:text-white hover:border-[#00DD55]/30 hover:bg-black/40 transition-colors backdrop-blur-md"
                >
                  {item.label}
                </a>
              ))}
            </div>
          </div>

          {/* Right HUD */}
          <div className="lg:col-span-5">
            <motion.div
              initial={{ opacity: 0, y: 18, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.45, delay: 0.12 }}
              className="relative rounded-3xl border border-[#00DD55]/25 bg-black/45 backdrop-blur-xl p-6 overflow-hidden"
            >
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_0%,rgba(0,221,85,0.18),transparent_45%),radial-gradient(circle_at_90%_30%,rgba(34,221,102,0.12),transparent_50%)]" />
              <div className="relative">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-[#00DD55]" />
                    <div className="text-white font-black">Your affiliate toolkit</div>
                  </div>
                  <div className="text-xs text-white/60">PG</div>
                </div>

                <div className="mt-5 grid grid-cols-2 gap-3">
                  <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
                    <div className="text-[11px] uppercase tracking-wider text-white/60">Cookie</div>
                    <div className="mt-1 text-lg font-black text-white">30 days</div>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
                    <div className="text-[11px] uppercase tracking-wider text-white/60">Hold</div>
                    <div className="mt-1 text-lg font-black text-white">30 days</div>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
                    <div className="text-[11px] uppercase tracking-wider text-white/60">Payout</div>
                    <div className="mt-1 text-lg font-black text-white">PayPal / Crypto</div>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
                    <div className="text-[11px] uppercase tracking-wider text-white/60">Tracking</div>
                    <div className="mt-1 text-lg font-black text-white">Clicks + Referrals</div>
                  </div>
                </div>

                <div className="mt-5 rounded-2xl border border-white/10 bg-black/30 p-4">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-white/80">Typical monthly earnings</span>
                    <span className="text-emerald-200 font-bold">$80 → $2,000+</span>
                  </div>
                  <div className="mt-3 h-2.5 rounded-full bg-white/10 overflow-hidden">
                    <div className="h-full w-[68%] bg-gradient-to-r from-[#00DD55] to-[#22DD66] glow-neon" />
                  </div>
                  <div className="mt-3 text-xs text-white/60 flex items-center gap-2">
                    <Clock className="h-4 w-4 text-[#00DD55]" />
                    Commissions become payout-ready after the hold period.
                  </div>
                </div>

                <div className="mt-4 text-xs text-white/50 flex items-start gap-2">
                  <ShieldCheck className="h-4 w-4 text-[#00DD55] mt-0.5" />
                  <span>Tax forms may be required for payouts depending on jurisdiction and earnings.</span>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
}


