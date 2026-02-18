/**
 * V2 THEME — V1 Design Snapshot + V2 Sharp Overrides
 * Mirrors V1 brand (colors, glass, gradients) with edgy shape language.
 * Used ONLY by V2 components. Do not import in V1.
 */

// ============ V1 DESIGN SNAPSHOT (Brand Vibe) ============

/** Primary background — V1 #0A0F0A */
export const bg0 = '#0A0F0A'

/** Secondary background — V1 #121212 */
export const bg1 = '#121212'

/** Glass surface — V1 rgba(18,18,23,0.6) */
export const surface = 'rgba(18,18,23,0.6)'

/** Glass surface strong — V1 sidebar */
export const surfaceStrong = 'rgba(26,26,31,0.8)'

/** Glass surface subtle */
export const surfaceSubtle = 'rgba(18,18,23,0.4)'

/** Card/section background with transparency */
export const surfaceSection = 'rgba(10,15,10,0.5)'

/** Border default — V1 white/8–10 */
export const border = 'rgba(255,255,255,0.1)'

/** Border accent — V1 green */
export const borderAccent = 'rgba(0,255,94,0.4)'

/** Text primary */
export const textPrimary = '#FFFFFF'

/** Text muted — V1 white/60 */
export const textMuted = 'rgba(255,255,255,0.6)'

/** Text dim */
export const textDim = 'rgba(255,255,255,0.5)'

/** Accent — V1 logo green #00FF5E */
export const accent = '#00FF5E'

/** Accent fill — V1 #00CC4B */
export const accentFill = '#00CC4B'

/** Accent highlight — hover #22FF6E */
export const accentHighlight = '#22FF6E'

/** Accent with alpha for glows/badges */
export const accentAlpha = (a: number) => `rgba(0,255,94,${a})`

/** Overlay dark for readability */
export const overlayDark = 'rgba(0,0,0,0.3)'

/** Gradient overlay — V1 style */
export const gradientOverlay = 'linear-gradient(to bottom, rgba(0,0,0,0.4), rgba(0,0,0,0.2), rgba(0,0,0,0.4))'

/** Backdrop blur — V1, reduced ~15% for V2 (no soft glow) */
export const blurMd = '10px'
export const blurXl = '20px'

// ============ V2 SHAPE LANGUAGE (Design Director: 8px default, 12px max) ============

/** Default radius 8px; max 12px. No pills. */
export const radiusSm = '8px'
export const radiusMd = '8px'
export const radiusLg = '12px'

/** No circles: use 0 for badges that must be rectangular */
export const radiusFull = '0'

/** Card border — contrast + blur, no drop shadow */
export const cardBorder = 'rgba(255,255,255,0.08)'

// ============ SPACING (Design Director: section 24–32 desktop, 16–20 mobile) ============

export const space = {
  1: '4px',
  2: '8px',
  3: '12px',
  4: '16px',
  5: '20px',
  6: '24px',
  8: '32px',
  10: '40px',
  12: '48px',
  16: '64px',
  20: '80px',
  24: '96px',
} as const

/** Section padding: desktop 24–32px, mobile 16–20px */
export const sectionPaddingDesktop = '24px'
export const sectionPaddingMobile = '16px'

// ============ TYPOGRAPHY ============

export const font = {
  heading: 'font-black tracking-tight',
  headingTight: 'font-black tracking-tighter uppercase',
  label: 'text-xs font-bold uppercase tracking-widest text-[var(--v2-text-muted)]',
  body: 'text-sm',
  bodyMuted: 'text-sm text-[var(--v2-text-muted)]',
  mono: 'font-mono tabular-nums',
  number: 'font-black tabular-nums',
} as const

// ============ CSS CUSTOM PROPERTIES (for v2.css) ============

export const cssVars = {
  '--v2-bg0': bg0,
  '--v2-bg1': bg1,
  '--v2-surface': surface,
  '--v2-surface-strong': surfaceStrong,
  '--v2-border': border,
  '--v2-card-border': cardBorder,
  '--v2-border-accent': borderAccent,
  '--v2-text-primary': textPrimary,
  '--v2-text-muted': textMuted,
  '--v2-accent': accent,
  '--v2-accent-fill': accentFill,
  '--v2-accent-highlight': accentHighlight,
  '--v2-radius-sm': radiusSm,
  '--v2-radius-md': radiusMd,
  '--v2-radius-lg': radiusLg,
  '--v2-section-padding-desktop': sectionPaddingDesktop,
  '--v2-section-padding-mobile': sectionPaddingMobile,
  '--v2-blur-md': blurMd,
  '--v2-blur-xl': blurXl,
} as const
