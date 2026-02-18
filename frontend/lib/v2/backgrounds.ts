/**
 * V2 per-path background map.
 * Mirrors V1 page backgrounds using existing /public images (reference only).
 * Used only by V2 layout and V2BackgroundLayer.
 */

export type V2BackgroundPattern = 'grid' | 'noise' | 'none'

export interface V2BackgroundConfig {
  imageUrl: string
  overlayOpacity: number
  pattern?: V2BackgroundPattern
}

/** Path -> background config. Design Director: overlay 0.45–0.65 for readability. */
const V2_PATH_BACKGROUNDS: Record<string, V2BackgroundConfig> = {
  '/v2': {
    imageUrl: '/images/s1back.png',
    overlayOpacity: 0.5,
    pattern: 'none',
  },
  '/v2/app': {
    imageUrl: '/images/nflll.png',
    overlayOpacity: 0.5,
    pattern: 'grid',
  },
  '/v2/app/builder': {
    imageUrl: '/images/devback.png',
    overlayOpacity: 0.5,
    pattern: 'grid',
  },
  '/v2/app/analytics': {
    imageUrl: '/images/pgbb2.png',
    overlayOpacity: 0.5,
    pattern: 'grid',
  },
  '/v2/app/leaderboard': {
    imageUrl: '/images/nflll.png',
    overlayOpacity: 0.5,
    pattern: 'grid',
  },
  '/v2/app/settings': {
    imageUrl: '/images/LRback.png',
    overlayOpacity: 0.5,
    pattern: 'grid',
  },
}

/** Fallback when path has no entry (use landing image). */
const FALLBACK: V2BackgroundConfig = {
  imageUrl: '/images/s1back.png',
  overlayOpacity: 0.5,
  pattern: 'none',
}

/** Ordered path prefixes (longest first) so /v2/app/builder matches before /v2/app. */
const PATH_PREFIXES = [
  '/v2/app/settings',
  '/v2/app/leaderboard',
  '/v2/app/analytics',
  '/v2/app/builder',
  '/v2/app',
  '/v2',
] as const

/**
 * Returns background config for a V2 pathname.
 * Use in V2 layout / V2BackgroundLayer only.
 */
export function getV2BackgroundForPath(pathname: string): V2BackgroundConfig {
  const normalized = pathname.replace(/\/$/, '') || '/v2'
  for (const prefix of PATH_PREFIXES) {
    if (normalized === prefix || normalized.startsWith(prefix + '/')) {
      return V2_PATH_BACKGROUNDS[prefix] ?? FALLBACK
    }
  }
  return FALLBACK
}
