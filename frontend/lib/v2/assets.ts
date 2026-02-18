/**
 * V2 ASSET MAP
 * Central source of truth for all V2 imagery
 * References existing assets in /public
 */

// Brand Assets
export const BRAND_ASSETS = {
  logo: {
    primary: '/parlay-gorilla.png.webp',
    fallback: '/gorilla.png',
    icon: '/favicon.png',
    source: '/gorilla-logo-source.png',
  },
}

// Hero Sport Images
export const HERO_SPORTS = {
  football: '/images/gorilla-football.png',
  basketball: '/images/gorilla-basketball.png',
  hockey: '/images/gorilla-hockey.png',
  baseball: '/images/gorilla-baseball.png',
}

// Background Textures
export const BACKGROUNDS = {
  primary: '/images/LRback.png',
  secondary: '/images/devback.png',
  home: '/images/Home page.png',
}

// Sport Icons
export const SPORT_ICONS = {
  mlb: '/images/MLB.png',
  mma: '/images/MMA.png',
  nba: '/images/basketbal.png',
}

// Utility: Get fallback if asset missing
export function getAssetOrFallback(asset: string, fallback: string): string {
  return asset || fallback
}

// Utility: Get random sport hero
export function getRandomSportHero(): string {
  const heroes = Object.values(HERO_SPORTS)
  return heroes[Math.floor(Math.random() * heroes.length)]
}
