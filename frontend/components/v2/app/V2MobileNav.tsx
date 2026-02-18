/**
 * V2 Mobile Bottom Navigation
 * Sharp, minimal bottom nav with sliding indicator
 */

'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

export function V2MobileNav() {
  const pathname = usePathname()

  const navItems = [
    { href: '/v2/app/builder', label: 'Build', icon: '▶' },
    { href: '/v2/app', label: 'Picks', icon: '■' },
    { href: '/v2/app/analytics', label: 'Stats', icon: '▲' },
    { href: '/v2/app/settings', label: 'Settings', icon: '▼' },
  ]

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-[rgba(26,26,31,0.95)] backdrop-blur-[20px] border-t border-[rgba(255,255,255,0.08)]">
      <div className="grid grid-cols-4 min-h-[56px] relative">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`
                flex flex-col items-center justify-center gap-0.5 min-h-[44px]
                v2-transition-colors relative
                ${isActive ? 'text-[#00FF5E]' : 'text-white/50'}
              `}
            >
              {isActive && (
                <div className="absolute top-0 left-0 right-0 h-0.5 bg-[#00FF5E] v2-animate-fade-in" />
              )}
              <span className="text-sm">{item.icon}</span>
              <span className="text-xs font-bold uppercase tracking-wider">{item.label}</span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
