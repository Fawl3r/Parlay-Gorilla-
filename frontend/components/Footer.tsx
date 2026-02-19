"use client"

import { Fragment } from "react"
import Link from "next/link"
import { Twitter, Instagram, Youtube } from "lucide-react"
import { ParlayGorillaLogo } from "./ParlayGorillaLogo"
import { usePathname } from "next/navigation"
import { getVersionString } from "@/lib/constants/appVersion"

export function Footer() {
  const pathname = usePathname()
  const reportBugHref = `/report-bug${pathname ? `?from=${encodeURIComponent(pathname)}` : ""}`
  const supportEmail = "contact@f3ai.dev"

  const quickLinks: Array<{ href: string; label: string; className?: string }> = [
    { href: "/support", label: "Contact" },
    { href: "/tutorial", label: "Tutorial" },
    { href: reportBugHref, label: "Report a bug" },
    { href: "/development-news", label: "Development News" },
    { href: "/pricing", label: "Pricing" },
    { href: "/privacy", label: "Privacy" },
    { href: "/terms", label: "Terms" },
    { href: "/refunds", label: "Refunds" },
    { href: "/disclaimer", label: "Disclaimer" },
    { href: "/admin/login", label: "Admin Login", className: "text-[10px]" },
  ]

  return (
    <footer className="w-full">
      {/* Main Footer Section - Compact Design */}
      <div className="bg-[#0A0F0A] border-t-2 border-[#00FF5E]/30">
        <div className="container mx-auto px-4 py-6">
          {/* Top Row - Branding, Links, Social */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            {/* Left - Branding */}
            <div className="flex items-center gap-2">
              <ParlayGorillaLogo size="sm" showText={false} />
              <div className="flex flex-col">
                <span 
                  className="text-sm font-black text-[#00FF5E]"
                  style={{
                    filter: 'drop-shadow(0 0 6px #00FF5E) drop-shadow(0 0 12px #00CC4B)'
                  }}
                >
                  Parlay Gorilla
                </span>
                <span className="text-[9px] text-white/60 tracking-wide">AI PARLAY ENGINE</span>
              </div>
            </div>

            {/* Middle - Quick Links */}
            <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-xs">
              {quickLinks.map((item, idx) => (
                <Fragment key={`${item.href}:${item.label}`}>
                  <Link
                    href={item.href}
                    className={[
                      "text-white/60 hover:text-[#00FF5E] transition-colors",
                      item.className ?? "",
                    ].join(" ")}
                  >
                    {item.label}
                  </Link>
                  {idx < quickLinks.length - 1 ? <span className="text-white/40">•</span> : null}
                </Fragment>
              ))}
            </div>

            {/* Right - Social Icons */}
            <div className="flex items-center justify-end gap-2">
              <a
                href="https://youtube.com/@parlaygorilla"
                target="_blank"
                rel="noopener noreferrer"
                className="w-8 h-8 rounded-full border border-[#00FF5E]/50 bg-[#00FF5E]/10 flex items-center justify-center text-white hover:bg-[#00FF5E]/20 hover:border-[#00FF5E] transition-all"
                aria-label="YouTube"
              >
                <Youtube className="h-4 w-4" />
              </a>
              <a
                href="https://twitter.com/parlaygorilla"
                target="_blank"
                rel="noopener noreferrer"
                className="w-8 h-8 rounded-full border border-[#00FF5E]/50 bg-[#00FF5E]/10 flex items-center justify-center text-white hover:bg-[#00FF5E]/20 hover:border-[#00FF5E] transition-all"
                aria-label="Twitter/X"
              >
                <Twitter className="h-4 w-4" />
              </a>
              <a
                href="https://instagram.com/parlaygorilla"
                target="_blank"
                rel="noopener noreferrer"
                className="w-8 h-8 rounded-full border border-[#00FF5E]/50 bg-[#00FF5E]/10 flex items-center justify-center text-white hover:bg-[#00FF5E]/20 hover:border-[#00FF5E] transition-all"
                aria-label="Instagram"
              >
                <Instagram className="h-4 w-4" />
              </a>
            </div>
          </div>

          {/* Middle Row - Security Badges & 18+ Warning */}
          <div className="flex flex-wrap items-center justify-between gap-4 mb-4 pb-4 border-b border-white/10">
            {/* Security Badges */}
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-1.5 px-2.5 py-1 bg-white/5 rounded border border-white/10">
                <div className="w-4 h-4 bg-[#00FF5E] rounded flex items-center justify-center">
                  <svg className="w-2.5 h-2.5 text-black" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                  </svg>
                </div>
                <span className="text-[10px] font-medium text-white">SSL</span>
              </div>
              <div className="flex items-center gap-1.5 px-2.5 py-1 bg-white/5 rounded border border-blue-500/30">
                <div className="w-4 h-4 bg-blue-600 rounded flex items-center justify-center">
                  <svg className="w-2.5 h-2.5 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
                <span className="text-[10px] font-medium text-white">GDPR</span>
              </div>
              <div className="flex items-center gap-1.5 px-2.5 py-1 bg-white/5 rounded border border-amber-500/30">
                <div className="w-4 h-4 bg-amber-500 rounded flex items-center justify-center">
                  <svg className="w-2.5 h-2.5 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                </div>
                <span className="text-[10px] font-medium text-white">Responsible Gaming</span>
              </div>
            </div>

            {/* 18+ Warning - Compact */}
            <div className="flex items-center gap-2 px-3 py-1.5 bg-[#00FF5E]/20 border border-[#00FF5E]/50 rounded backdrop-blur-sm">
              <span className="text-lg font-black text-white">18+</span>
              <span className="text-[10px] text-white">
                18+ | Analytics & Research Only | No Wagering
              </span>
            </div>
          </div>

          {/* Authority footer line */}
          <div className="mb-3 pb-3 border-b border-white/10">
            <p className="text-[10px] text-white/45 tracking-wide">
              Parlay Gorilla Intelligence Platform · AI-Driven Sports Analysis System
            </p>
          </div>

          {/* Bottom Row - Copyright & Legal */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
            <div className="flex flex-col gap-1">
              <p className="text-xs text-white/60">
                Copyright © 2026 - 2027 F3 AI Labs. All Rights Reserved.
              </p>
              <p className="text-xs text-white/70 font-medium">
                Parlay Gorilla™ is a product of{" "}
                <span className="text-[#00FF5E] font-semibold">F3 AI Labs</span>
              </p>
              <p className="text-[11px] text-white/60">
                Support:{" "}
                <a
                  href={`mailto:${supportEmail}`}
                  className="text-[#00FF5E] hover:text-[#22FF6E] hover:underline font-semibold"
                >
                  {supportEmail}
                </a>
              </p>
              <p className="text-[10px] text-white/50 mt-1">
                Parlay Gorilla • {getVersionString()}
              </p>
            </div>
            <p className="text-[10px] text-white/60 leading-tight max-w-2xl text-right md:text-left">
              <strong className="text-white">Disclaimer:</strong> Parlay Gorilla is an AI-powered sports analysis & research tool. We do not accept bets or facilitate wagering. All scenarios are hypothetical and for informational/entertainment purposes only. Not a sportsbook. Not affiliated with any sportsbook.{" "}
              <Link href="/disclaimer" className="text-[#00FF5E] hover:text-[#22FF6E] hover:underline">
                Read full disclaimer
              </Link>
              .{" "}
              Parlay Gorilla is not affiliated with, endorsed by, or associated with the NFL, NBA, MLB, NHL, NCAA, or any professional sports league or team.
              Team names and abbreviations are used solely for identification purposes.{" "}
              <a 
                href="https://www.ncpgambling.org" 
                target="_blank"
                rel="noopener noreferrer"
                className="text-[#00FF5E] hover:text-[#22FF6E] hover:underline"
              >
                ncpgambling.org
              </a>
              {" "}or{" "}
              <a 
                href="tel:1-800-522-4700" 
                className="text-[#00FF5E] hover:text-[#22FF6E] hover:underline"
              >
                1-800-522-4700
              </a>
            </p>
          </div>
        </div>
      </div>
    </footer>
  )
}
