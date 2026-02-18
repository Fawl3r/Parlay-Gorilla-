/**
 * V2 Desktop Sidebar Navigation
 * Sharp, terminal-style sidebar with animated indicators
 */

'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

export function V2DesktopSidebar() {
  const pathname = usePathname()

  const navItems = [
    { href: '/v2/app', label: 'Dashboard', icon: '■' },
    { href: '/v2/app/builder', label: 'Builder', icon: '▶' },
    { href: '/v2/app/analytics', label: 'Analytics', icon: '▲' },
    { href: '/v2/app/leaderboard', label: 'Leaderboard', icon: '●' },
    { href: '/v2/app/settings', label: 'Settings', icon: '▼' },
  ]

  return (
    <aside className="hidden lg:flex lg:flex-col lg:w-56 bg-[rgba(26,26,31,0.8)] backdrop-blur-[20px] border-r border-[rgba(255,255,255,0.08)] h-screen sticky top-0">
      {/* Logo */}
      <div className="p-5 border-b border-[rgba(255,255,255,0.08)]">
        <Link href="/v2" className="flex items-center gap-2 v2-hover-scale v2-transition-transform">
          <div className="w-8 h-8 bg-[#00FF5E] flex items-center justify-center text-black font-black text-base rounded-lg">
            PG
          </div>
          <div>
            <div className="font-black text-white text-sm uppercase tracking-tight">Parlay Gorilla</div>
            <div className="text-xs text-[#00FF5E] font-bold tracking-widest">V2</div>
          </div>
        </Link>
      </div>

      {/* Navigation with Animated Indicators */}
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`
                flex items-center gap-3 px-3 py-2.5 
                v2-transition-colors relative
                border-l-2
                ${
                  isActive
                    ? 'border-[#00FF5E] bg-[#00FF5E]/10 text-[#00FF5E] font-bold'
                    : 'border-transparent text-white/60 hover:text-white/90 hover:border-white/15 font-bold v2-hover-sweep'
                }
              `}
            >
              <span className="text-xs">{item.icon}</span>
              <span className="text-xs uppercase tracking-wider">{item.label}</span>
              {isActive && (
                <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-[#00FF5E] v2-animate-fade-in" />
              )}
            </Link>
          )
        })}
      </nav>

      {/* Account section */}
      <div className="p-3 border-t border-[rgba(255,255,255,0.08)]">
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 border border-[rgba(255,255,255,0.08)] v2-hover-sweep v2-transition-colors">
          <div className="w-6 h-6 bg-[#00FF5E] flex items-center justify-center text-black font-black text-xs rounded-lg">
            U
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs font-bold text-white truncate">Demo</div>
            <div className="text-xs text-white/50">Free</div>
          </div>
        </div>
      </div>
    </aside>
  )
}
