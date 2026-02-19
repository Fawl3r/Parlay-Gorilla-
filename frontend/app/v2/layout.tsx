/**
 * V2 LAYOUT
 * Isolated layout for V2 routes
 * Prevents any contamination of production UI
 * Uses same per-page backgrounds as V1 (via V2BackgroundLayer).
 */

import { ReactNode } from 'react'
import '@/styles/v2.css'
import './v2-styles.css'
import '@/lib/v2/animations.css'
import { V2BackgroundLayer } from '@/components/v2/V2BackgroundLayer'

export default function V2Layout({ children }: { children: ReactNode }) {
  return (
    <div className="v2-isolated-ui relative">
      <V2BackgroundLayer />
      <div className="v2-scroll-content">{children}</div>
    </div>
  )
}
