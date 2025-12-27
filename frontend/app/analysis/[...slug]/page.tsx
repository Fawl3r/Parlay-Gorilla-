import { Metadata } from "next"
import Link from "next/link"
import { headers } from "next/headers"
import AnalysisPageClient from "./AnalysisPageClient"
import type { GameAnalysisResponse } from "@/lib/api"
import { generateSchemaGraph } from "@/lib/structured-data"
import { AnalysisContentNormalizer } from "@/lib/analysis/AnalysisContentNormalizer"
import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import { SPORT_BACKGROUNDS } from "@/components/games/gamesConfig"
import { SportBackground } from "@/components/games/SportBackground"
import { AlertCircle, ArrowLeft } from "lucide-react"

type Props = {
  params: Promise<{ slug: string[] }> | { slug: string[] }
  searchParams?: Promise<Record<string, string | string[] | undefined>> | Record<string, string | string[] | undefined>
}

async function getRequestOrigin(): Promise<string> {
  const h = await headers()
  const forwardedProto = h.get("x-forwarded-proto")
  const forwardedHost = h.get("x-forwarded-host")
  const host = forwardedHost || h.get("host")

  if (host) {
    const proto =
      forwardedProto ||
      (host.includes("localhost") || host.startsWith("127.") ? "http" : "https")
    return `${proto}://${host}`
  }

  return process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"
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

function needsTrendsRefresh(analysis: GameAnalysisResponse): boolean {
  const ats = analysis.analysis_content?.ats_trends
  const totals = analysis.analysis_content?.totals_trends

  const trendStrings = [
    ats?.home_team_trend,
    ats?.away_team_trend,
    totals?.home_team_trend,
    totals?.away_team_trend,
  ]
    .filter((value): value is string => typeof value === "string" && value.trim().length > 0)
    .map((value) => value.trim())

  if (trendStrings.length === 0) return false

  // Detect impossible percentages (historical bug: "10000.0% cover rate")
  const joined = trendStrings.join(" ")
  const pctRegex = /(\d+(?:\.\d+)?)%/g
  let match: RegExpExecArray | null
  while ((match = pctRegex.exec(joined)) !== null) {
    const pct = Number.parseFloat(match[1])
    if (Number.isFinite(pct) && pct > 100.0001) return true
  }

  // Detect mismatched availability: one side has digits, the other says "not currently available"
  const missingPhrase = "not currently available"
  const normalize = (s: string) => s.toLowerCase()
  const hasDigits = (s: string) => /\d/.test(s)
  const isMissing = (s: string) => normalize(s).includes(missingPhrase)
  const hasData = (s: string) => hasDigits(s) && !isMissing(s)

  const homeAts = typeof ats?.home_team_trend === "string" ? ats.home_team_trend : ""
  const awayAts = typeof ats?.away_team_trend === "string" ? ats.away_team_trend : ""
  const homeTot = typeof totals?.home_team_trend === "string" ? totals.home_team_trend : ""
  const awayTot = typeof totals?.away_team_trend === "string" ? totals.away_team_trend : ""

  const mismatched = (home: string, away: string) => {
    const homeHas = hasData(home)
    const awayHas = hasData(away)
    if (homeHas === awayHas) return false
    return (isMissing(home) && awayHas) || (isMissing(away) && homeHas)
  }

  return mismatched(homeAts, awayAts) || mismatched(homeTot, awayTot)
}

async function fetchAnalysis(slugParts: string[]): Promise<GameAnalysisResponse> {
  const sport = slugParts[0] || "nfl"
  const isNfl = sport.toLowerCase() === "nfl"
  // Get the game slug part (everything after the sport prefix)
  const gameSlug = slugParts.slice(1).join("/")

  // Construct absolute URL for server component fetch (must be absolute)
  // Use same-origin so Next.js rewrites proxy /api/* to the backend consistently.
  const origin = await getRequestOrigin()
  const apiUrl = `${origin}/api/analysis/${sport}/${gameSlug}`
  
  try {
    // Add timeout and signal for fetch to handle Cloudflare tunnel issues
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000) // 30s timeout
    
    const response = await fetch(
      apiUrl,
      isNfl
        ? {
            // NFL is already behaving correctly; keep the original long revalidate to reduce load.
            // (Other sports had an issue where caching could freeze an incomplete async full_article.)
            next: { revalidate: 172800 },
            cache: "default",
            signal: controller.signal,
          }
        : {
            // Non-NFL leagues have more frequent slates; keep the server fetch cache shorter.
            // Note: The "full_article" breakdown is generated asynchronously, and the client
            // will auto-refresh the Breakdown tab if the article isn't ready yet.
            next: { revalidate: 86400 },
            cache: "default",
            signal: controller.signal,
          }
    ).finally(() => {
      clearTimeout(timeoutId)
    })

    if (!response.ok) {
      // Log the error for debugging
      const errorText = await response.text()
      console.error(`[Analysis] Failed to fetch analysis: ${response.status} ${response.statusText}`, {
        sport,
        gameSlug,
        error: errorText,
      })
      
      // If it's a 404, throw a more descriptive error
      if (response.status === 404) {
        throw new Error(`Analysis not found for ${sport}/${gameSlug}. The game may not exist or analysis hasn't been generated yet.`)
      }
      
      throw new Error(`Failed to load analysis: ${response.status} ${response.statusText}`)
    }

    const raw = await response.json()
    const analysis = AnalysisContentNormalizer.normalizeResponse(raw)
    
    return analysis
  } catch (error: any) {
    // Handle network errors (timeout, ECONNRESET, etc.)
    if (error.name === 'AbortError' || error.code === 'ECONNRESET' || error.message?.includes('socket hang up')) {
      console.error(`[Analysis] Network error (timeout/connection reset):`, {
        sport,
        gameSlug,
        error: error.message,
      })
      throw new Error(`Connection timeout or network error. Please try again. If this persists, the backend may be unreachable.`)
    }
    // Re-throw other errors
    throw error
  }
}

export async function generateMetadata({ params, searchParams }: Props): Promise<Metadata> {
  try {
    const resolvedParams = await Promise.resolve(params)

    const analysis = await fetchAnalysis(resolvedParams.slug)

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

export default async function AnalysisPage({ params, searchParams }: Props) {
  try {
    const resolvedParams = await Promise.resolve(params)
    const analysis = await fetchAnalysis(resolvedParams.slug)
    const sport = resolvedParams.slug[0] || "nfl"

    // Generate comprehensive JSON-LD structured data for SEO
    // Includes: Article, SportsEvent, FAQPage schemas for featured snippet eligibility
    let structuredData: unknown | null = null
    try {
      structuredData = generateSchemaGraph(analysis)
    } catch (err) {
      console.warn("[Analysis] Failed to generate structured data:", err)
      structuredData = null
    }

    return (
      <>
        {structuredData && (
          <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
          />
        )}
        <AnalysisPageClient analysis={analysis} sport={sport} />
      </>
    )
  } catch (error: any) {
    console.error("Error loading analysis:", error)

    const resolvedParams = await Promise.resolve(params)
    const sport = resolvedParams.slug[0] || "nfl"
    const gameSlug = resolvedParams.slug.slice(1).join("/")
    const attemptedPath = `/analysis/${resolvedParams.slug.join("/")}`
    const message = String(error?.message || "")

    const isNotFound = message.toLowerCase().includes("not found") || message.includes("404")
    const isNetworky =
      message.toLowerCase().includes("fetch") ||
      message.toLowerCase().includes("network") ||
      message.toLowerCase().includes("socket") ||
      message.toLowerCase().includes("timeout") ||
      message.toLowerCase().includes("econn")

    const title = isNotFound ? "Analysis Not Available" : "Temporary Issue Loading Analysis"
    const description = isNotFound
      ? "The analysis for this game hasn't been generated yet or the game may not exist."
      : isNetworky
        ? "We couldn't reach the analysis service right now. This is usually temporary—please retry."
        : "Something went wrong while loading this analysis. Please retry."

    const backgroundImage = SPORT_BACKGROUNDS[sport] || "/images/nflll.png"

    return (
      <div className="min-h-screen flex flex-col relative">
        <SportBackground imageUrl={backgroundImage} overlay="medium" />

        <div className="relative z-10 min-h-screen flex flex-col">
          <Header />
          <main className="flex-1 flex items-center justify-center px-4">
            <div className="max-w-md w-full text-center space-y-6">
              <AlertCircle className="h-16 w-16 text-yellow-500 mx-auto" />
              <div>
                <h1 className="text-2xl font-bold text-white mb-2">{title}</h1>
                <p className="text-gray-400 mb-4">{description}</p>
                <p className="text-sm text-gray-500 mb-6">
                  Game: {sport.toUpperCase()} - {gameSlug}
                </p>
              </div>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Link
                  href={attemptedPath}
                  className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-black font-semibold rounded-lg transition-colors"
                >
                  Retry
                </Link>
                <Link
                  href="/analysis"
                  className="inline-flex items-center justify-center gap-2 px-4 py-2 border border-white/20 hover:bg-white/10 text-white font-semibold rounded-lg transition-colors"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Back to Game Analysis
                </Link>
                <Link
                  href="/sports"
                  className="inline-flex items-center justify-center gap-2 px-4 py-2 border border-white/20 hover:bg-white/10 text-white font-semibold rounded-lg transition-colors"
                >
                  Browse Sports
                </Link>
              </div>
            </div>
          </main>
          <Footer />
        </div>
      </div>
    )
  }
}

