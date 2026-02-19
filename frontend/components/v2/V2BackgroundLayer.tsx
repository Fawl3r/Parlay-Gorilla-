'use client'

import { memo } from 'react'
import { usePathname } from 'next/navigation'
import { getV2BackgroundForPath } from '@/lib/v2/backgrounds'

/**
 * Full-page background layer for V2: same imagery as V1 per route.
 * Memoized so it only re-renders when pathname changes.
 */
function V2BackgroundLayerInner() {
  const pathname = usePathname()
  const path = pathname ?? '/v2'
  if (path === '/v2') return null
  const config = getV2BackgroundForPath(path)
  return (
    <div
      className="v2-bg-layer fixed inset-0 -z-10 overflow-hidden pointer-events-none bg-[#0A0F0A]"
      aria-hidden
    >
      {/* Background image only when set (landing uses no image to avoid load/paint) */}
      {config.imageUrl ? (
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: `url('${config.imageUrl}')` }}
        />
      ) : null}
      {/* Dark overlay for readability (0 when no image) */}
      {config.overlayOpacity > 0 ? (
        <div
          className="absolute inset-0 bg-black"
          style={{ opacity: config.overlayOpacity }}
        />
      ) : null}
      {/* Optional subtle grid (app pages only; no animated scanline per Design Director) */}
      {config.pattern === 'grid' && (
        <div
          className="absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage: `linear-gradient(rgba(0, 255, 94, 0.4) 1px, transparent 1px),
                             linear-gradient(90deg, rgba(0, 255, 94, 0.4) 1px, transparent 1px)`,
            backgroundSize: '48px 48px',
          }}
        />
      )}
    </div>
  )
}

export const V2BackgroundLayer = memo(V2BackgroundLayerInner)
