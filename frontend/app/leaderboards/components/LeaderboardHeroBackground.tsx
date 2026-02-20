"use client"

import type { ReactNode } from "react"

const BG_SRC = "/images/leaderboards/leaderboards-bg.png"

export function LeaderboardHeroBackground({ children }: { children: ReactNode }) {
  return (
    <div className="relative min-h-[calc(100vh-4rem)] w-full overflow-hidden bg-black">
      {/* Background image layer — CSS so missing image doesn't break the page */}
      <div
        className="absolute inset-0 z-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: `url(${BG_SRC})` }}
        aria-hidden
      />

      {/* Dark gradient overlay — navbar + header readability */}
      <div
        className="absolute inset-0 z-[1] bg-gradient-to-b from-black/80 via-black/50 to-black/85 pointer-events-none"
        aria-hidden
      />

      {/* Radial spotlight behind title area */}
      <div
        className="absolute inset-0 z-[2] pointer-events-none"
        style={{
          background: "radial-gradient(ellipse 80% 40% at 50% 15%, rgba(16, 185, 129, 0.08) 0%, transparent 55%)",
        }}
        aria-hidden
      />

      {/* Soft noise overlay — low opacity to prevent banding */}
      <div
        className="absolute inset-0 z-[3] opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
        }}
        aria-hidden
      />

      {/* Content: glass foreground container */}
      <main className="relative z-10 mx-auto w-full max-w-5xl px-4 py-6">
        <div
          className="rounded-2xl border border-white/10 bg-black/30 backdrop-blur-md shadow-inner min-h-[50vh]"
          style={{ boxShadow: "inset 0 1px 0 0 rgba(255,255,255,0.05), 0 0 0 1px rgba(16, 185, 129, 0.15)" }}
        >
          {children}
        </div>
      </main>
    </div>
  )
}
