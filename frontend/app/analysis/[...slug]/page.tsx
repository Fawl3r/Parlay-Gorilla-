import { Metadata } from "next"
import { notFound } from "next/navigation"
import AnalysisPageClient from "./AnalysisPageClient"
import { GameAnalysisResponse } from "@/lib/api"
import { generateSchemaGraph } from "@/lib/structured-data"

type Props = {
  params: Promise<{ slug: string[] }>
}

function needsProbabilityRefresh(analysis: GameAnalysisResponse): boolean {
  const probs = analysis.analysis_content?.model_win_probability
  if (!probs) return true
  
  // Check if confidence is available and very low (might benefit from refresh)
  const aiConfidence = probs.ai_confidence
  if (aiConfidence !== undefined && aiConfidence < 20) {
    return true  // Very low confidence - might have better data now
  }
  
  // Legacy check: If both are exactly 0.5 (old analyses before model upgrade)
  const homeProb = probs.home_win_prob ?? 0.5
  const awayProb = probs.away_win_prob ?? 0.5
  if (Math.abs(homeProb - 0.5) < 0.001 && Math.abs(awayProb - 0.5) < 0.001) {
    return true
  }
  
  return false
}

async function fetchAnalysis(slugParts: string[], forceRefresh = false): Promise<GameAnalysisResponse> {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
  const sport = slugParts[0] || "nfl"
  // Get the game slug part (everything after the sport prefix)
  const gameSlug = slugParts.slice(1).join("/")

  const refreshParam = forceRefresh ? "?refresh=true" : ""
  const response = await fetch(`${API_URL}/api/analysis/${sport}/${gameSlug}${refreshParam}`, {
    next: { revalidate: forceRefresh ? 0 : 3600 }, // No cache if refreshing
    cache: forceRefresh ? "no-store" : "default",
  })

  if (!response.ok) {
    throw new Error("Analysis not found")
  }

  const analysis = await response.json()
  
  // If probabilities are 50-50 and we haven't tried refreshing yet, try once
  if (!forceRefresh && needsProbabilityRefresh(analysis)) {
    console.log("[Analysis] Detected 50-50 probabilities, requesting refresh...")
    return fetchAnalysis(slugParts, true)
  }

  return analysis
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  try {
    const { slug } = await params
    const analysis = await fetchAnalysis(slug)

    const title = analysis.seo_metadata?.title || `${analysis.matchup} Prediction & Picks`
    const description =
      analysis.seo_metadata?.description || analysis.analysis_content.opening_summary.slice(0, 160)

    return {
      title,
      description,
      keywords:
        analysis.seo_metadata?.keywords || `${analysis.matchup}, ${analysis.league}, prediction, picks, best bets`,
      openGraph: {
        title,
        description,
        type: "article",
      },
    }
  } catch {
    return {
      title: "Game Analysis",
      description: "Expert AI-powered game breakdown",
    }
  }
}

export default async function AnalysisPage({ params }: Props) {
  try {
    const { slug: slugParts } = await params
    const analysis = await fetchAnalysis(slugParts)

    // Generate comprehensive JSON-LD structured data for SEO
    // Includes: Article, SportsEvent, FAQPage schemas for featured snippet eligibility
    const structuredData = generateSchemaGraph(analysis)

    return (
      <>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
        />
        <AnalysisPageClient analysis={analysis} />
      </>
    )
  } catch (error) {
    console.error("Error loading analysis:", error)
    notFound()
  }
}

