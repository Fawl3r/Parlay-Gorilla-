/**
 * V2 Top Bar
 * Sharp, minimal top bar with premium button
 */

'use client'

import Link from 'next/link'

export function V2TopBar() {
  return (
    <header className="sticky top-0 z-40 bg-[#0A0F0A]/95 backdrop-blur-[10px] border-b border-[rgba(255,255,255,0.08)]">
      <div className="flex items-center justify-between h-14 px-4 lg:px-5">
        {/* Mobile logo */}
        <Link href="/v2" className="lg:hidden flex items-center gap-2">
          <div className="w-7 h-7 bg-[#00FF5E] flex items-center justify-center text-black font-bold text-xs rounded-lg">
            PG
          </div>
          <span className="font-bold text-white text-sm">PG</span>
        </Link>

        {/* Desktop title */}
        <div className="hidden lg:block">
          <h1 className="text-base font-bold text-white">Dashboard</h1>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button className="min-h-[44px] px-4 py-2.5 bg-[#00FF5E] hover:bg-[#22FF6E] text-black font-bold text-sm rounded-lg v2-transition-colors v2-press-scale">
            Generate
          </button>
        </div>
      </div>
    </header>
  )
}
