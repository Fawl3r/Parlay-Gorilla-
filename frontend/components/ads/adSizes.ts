export type AdSlotSize =
  | "banner"
  | "leaderboard"
  | "rectangle"
  | "sidebar"
  | "square"
  | "mobile-banner"

export interface AdSizeConfig {
  width: number
  height: number
  mobileWidth: number
  mobileHeight: number
}

// Ad size configurations (in pixels)
export const AD_SIZE_CONFIG: Record<AdSlotSize, AdSizeConfig> = {
  banner: { width: 728, height: 90, mobileWidth: 320, mobileHeight: 50 },
  leaderboard: { width: 728, height: 90, mobileWidth: 320, mobileHeight: 100 },
  rectangle: { width: 300, height: 250, mobileWidth: 300, mobileHeight: 250 },
  sidebar: { width: 300, height: 600, mobileWidth: 300, mobileHeight: 250 },
  square: { width: 250, height: 250, mobileWidth: 250, mobileHeight: 250 },
  "mobile-banner": { width: 320, height: 50, mobileWidth: 320, mobileHeight: 50 },
}

// Tailwind sizing helpers for consistent layout
export const AD_SIZE_CLASSES: Record<AdSlotSize, string> = {
  banner: "h-[90px] max-w-[728px] mx-auto",
  leaderboard: "h-[90px] md:h-[90px] max-w-[728px] mx-auto",
  rectangle: "h-[250px] w-[300px] mx-auto",
  sidebar: "min-h-[250px] md:min-h-[600px] w-[300px]",
  square: "h-[250px] w-[250px] mx-auto",
  "mobile-banner": "h-[50px] w-[320px] mx-auto md:hidden",
}


