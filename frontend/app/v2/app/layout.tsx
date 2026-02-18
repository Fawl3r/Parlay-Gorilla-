/**
 * V2 App Shell Layout
 * Wraps all /v2/app/* pages
 */

import { ReactNode } from 'react'
import { V2DesktopSidebar } from '@/components/v2/app/V2DesktopSidebar'
import { V2MobileNav } from '@/components/v2/app/V2MobileNav'
import { V2TopBar } from '@/components/v2/app/V2TopBar'

export default function V2AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen bg-[#0A0F0A]">
      <V2DesktopSidebar />
      
      <div className="flex-1 flex flex-col">
        <V2TopBar />
        
        <main className="flex-1 pb-20 lg:pb-0">
          {children}
        </main>
      </div>

      <V2MobileNav />
    </div>
  )
}
