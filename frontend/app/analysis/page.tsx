import { Metadata } from "next"
import GameAnalysisHubClient from "./GameAnalysisHubClient"

function resolveSiteUrl(): string {
  const raw = process.env.NEXT_PUBLIC_SITE_URL || "https://parlaygorilla.com"
  const withProto = raw.includes("://") ? raw : `https://${raw}`
  return withProto.replace(/\/+$/, "")
}

const SITE_URL = resolveSiteUrl()

export const metadata: Metadata = {
  title: "Game Analysis & Predictions | Parlay Gorilla",
  description: "Expert AI-powered game breakdowns, predictions, and betting picks for NFL, NBA, MLB, NHL, and Soccer. Free daily analysis with best bets and parlay recommendations.",
  keywords: "sports betting analysis, NFL predictions, NBA picks, MLB betting, NHL predictions, soccer predictions, best bets, parlay picks, game analysis, betting tips",
  openGraph: {
    title: "Game Analysis & Predictions | Parlay Gorilla",
    description: "Expert AI-powered game breakdowns, predictions, and betting picks for NFL, NBA, MLB, NHL, and Soccer.",
    type: "website",
    url: "/analysis",
  },
  twitter: {
    card: "summary_large_image",
    title: "Game Analysis & Predictions | Parlay Gorilla",
    description: "Expert AI-powered game breakdowns, predictions, and betting picks for NFL, NBA, MLB, NHL, and Soccer.",
  },
  alternates: {
    canonical: "/analysis",
  },
}

// JSON-LD structured data for the analysis listing page
const structuredData = {
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  name: "Game Analysis & Predictions",
  description: "Expert AI-powered game breakdowns, predictions, and betting picks for NFL, NBA, MLB, NHL, and Soccer.",
  publisher: {
    "@type": "Organization",
    name: "Parlay Gorilla",
    url: SITE_URL,
  },
  mainEntity: {
    "@type": "ItemList",
    itemListElement: [
      {
        "@type": "ListItem",
        position: 1,
        item: {
          "@type": "WebPage",
          name: "NFL Game Analysis",
          description: "Expert NFL predictions and betting analysis",
        },
      },
      {
        "@type": "ListItem",
        position: 2,
        item: {
          "@type": "WebPage",
          name: "NBA Game Analysis",
          description: "Expert NBA predictions and betting analysis",
        },
      },
      {
        "@type": "ListItem",
        position: 3,
        item: {
          "@type": "WebPage",
          name: "MLB Game Analysis",
          description: "Expert MLB predictions and betting analysis",
        },
      },
      {
        "@type": "ListItem",
        position: 4,
        item: {
          "@type": "WebPage",
          name: "NHL Game Analysis",
          description: "Expert NHL predictions and betting analysis",
        },
      },
      {
        "@type": "ListItem",
        position: 5,
        item: {
          "@type": "WebPage",
          name: "Soccer Game Analysis",
          description: "Expert soccer predictions and betting analysis",
        },
      },
    ],
  },
}

export default function AnalysisPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
      <GameAnalysisHubClient />
    </>
  )
}
