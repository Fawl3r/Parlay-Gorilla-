export type TutorialScreenshotVariant = "desktop" | "mobile"

export type TutorialScreenshotId =
  | "landing_desktop"
  | "buildControls_desktop"
  | "buildParlayResult_desktop"
  | "dashboardUpcomingGames_desktop"
  | "dashboardAiBuilder_desktop"
  | "dashboardCustomBuilderLocked_desktop"
  | "analysisHub_desktop"
  | "pricingPaywall_desktop"
  | "buildControls_mobile"
  | "dashboardUpcomingGames_mobile"

export type TutorialScreenshotAsset = {
  id: TutorialScreenshotId
  src: string
  alt: string
  width: number
  height: number
  variant: TutorialScreenshotVariant
  caption?: string
}

export class TutorialScreenshotLibrary {
  private readonly assets: Record<TutorialScreenshotId, TutorialScreenshotAsset>

  constructor(assets: Record<TutorialScreenshotId, TutorialScreenshotAsset>) {
    this.assets = assets
  }

  get(id: TutorialScreenshotId): TutorialScreenshotAsset {
    return this.assets[id]
  }
}

export const tutorialScreenshots = new TutorialScreenshotLibrary({
  landing_desktop: {
    id: "landing_desktop",
    src: "/tutorial/desktop/02-landing.png",
    alt: "Parlay Gorilla landing page with header navigation and hero section.",
    width: 1440,
    height: 900,
    variant: "desktop",
    caption: "Landing page — start here if you’re new.",
  },
  buildControls_desktop: {
    id: "buildControls_desktop",
    src: "/tutorial/desktop/03-build-controls.png",
    alt: "AI Parlay Builder controls showing sport selection, legs slider, and risk profile.",
    width: 1440,
    height: 900,
    variant: "desktop",
    caption: "AI Builder controls on /build (public).",
  },
  buildParlayResult_desktop: {
    id: "buildParlayResult_desktop",
    src: "/tutorial/desktop/04-build-result.png",
    alt: "Generated parlay result showing confidence ring, legs list, and AI summary.",
    width: 1440,
    height: 900,
    variant: "desktop",
    caption: "Example result: confidence + legs + AI notes.",
  },
  dashboardUpcomingGames_desktop: {
    id: "dashboardUpcomingGames_desktop",
    src: "/tutorial/desktop/05-dashboard-upcoming-games.png",
    alt: "Gorilla Dashboard upcoming games tab with sport tabs and games list.",
    width: 1440,
    height: 900,
    variant: "desktop",
    caption: "Dashboard → Upcoming Games (pick legs from real games).",
  },
  dashboardAiBuilder_desktop: {
    id: "dashboardAiBuilder_desktop",
    src: "/tutorial/desktop/06-dashboard-ai-builder.png",
    alt: "Gorilla Dashboard AI Builder tab showing the parlay generation UI.",
    width: 1440,
    height: 900,
    variant: "desktop",
    caption: "Dashboard → AI Builder (same engine, inside your dashboard).",
  },
  dashboardCustomBuilderLocked_desktop: {
    id: "dashboardCustomBuilderLocked_desktop",
    src: "/tutorial/desktop/07-dashboard-custom-locked.png",
    alt: "Custom Builder tab showing a premium lock overlay.",
    width: 1440,
    height: 900,
    variant: "desktop",
    caption: "Custom Builder may be locked depending on your plan.",
  },
  analysisHub_desktop: {
    id: "analysisHub_desktop",
    src: "/tutorial/desktop/08-analysis-hub.png",
    alt: "Game Analysis hub listing analyses and filters.",
    width: 1440,
    height: 900,
    variant: "desktop",
    caption: "Game Analytics hub (public).",
  },
  pricingPaywall_desktop: {
    id: "pricingPaywall_desktop",
    src: "/tutorial/desktop/09-pricing.png",
    alt: "Pricing page showing plan options and upgrade call-to-action.",
    width: 1440,
    height: 900,
    variant: "desktop",
    caption: "Pricing page (upgrade / manage subscription).",
  },
  buildControls_mobile: {
    id: "buildControls_mobile",
    src: "/tutorial/mobile/03-build-controls.png",
    alt: "AI Parlay Builder controls on mobile.",
    width: 390,
    height: 844,
    variant: "mobile",
    caption: "AI Builder controls on mobile.",
  },
  dashboardUpcomingGames_mobile: {
    id: "dashboardUpcomingGames_mobile",
    src: "/tutorial/mobile/05-dashboard-upcoming-games.png",
    alt: "Upcoming Games tab in the Gorilla Dashboard on mobile.",
    width: 390,
    height: 844,
    variant: "mobile",
    caption: "Upcoming Games on mobile.",
  },
})


