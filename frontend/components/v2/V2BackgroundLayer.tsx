'use client'

import { usePathname } from 'next/navigation'
import { getV2BackgroundForPath } from '@/lib/v2/backgrounds'

/**
 * Full-page background layer for V2: same imagery as V1 per route.
 * Uses CSS background-image (no <Image>) for full-page cover.
 * Optional subtle scanline/grid; does not cause horizontal scroll.
 */
export function V2BackgroundLayer() {
  const pathname = usePathname()
  const path = pathname ?? '/v2'
  const config = getV2BackgroundForPath(path)

  return (
    <div
      className="fixed inset-0 -z-10 overflow-hidden pointer-events-none bg-[#0A0F0A]"
      aria-hidden
    >
      {/* Background image — cover, centered */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{
          backgroundImage: `url('${config.imageUrl}')`,
        }}
      />
      {/* Dark overlay for readability */}
      <div
        className="absolute inset-0 bg-black"
        style={{ opacity: config.overlayOpacity }}
      />
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
