/**
 * Structured Data (JSON-LD) generators for SEO
 * 
 * Creates schema.org markup optimized for Google Featured Snippets:
 * - FAQPage for Q&A featured snippets
 * - SportsEvent with teams, venue, and betting context
 * - Article for news/analysis snippets
 */

import { GameAnalysisResponse } from "@/lib/api"

function resolveSiteUrl(): string {
  const raw = process.env.NEXT_PUBLIC_SITE_URL || "https://parlaygorilla.com"
  const withProto = raw.includes("://") ? raw : `https://${raw}`
  return withProto.replace(/\/+$/, "")
}

const SITE_URL = resolveSiteUrl()
const LOGO_URL = `${SITE_URL}/images/newlogohead.png`

interface Team {
  "@type": "SportsTeam"
  name: string
  sport: string
}

interface FAQ {
  question: string
  answer: string
}

function extractTeamsFromMatchup(matchup: string | undefined | null): { awayTeam: string; homeTeam: string } | null {
  const raw = String(matchup || "").trim()
  if (!raw) return null
  const match = raw.match(/^(.+?)\s+@\s+(.+)$/)
  if (!match) return null
  return {
    awayTeam: match[1].trim(),
    homeTeam: match[2].trim(),
  }
}

/**
 * Generate FAQPage schema for featured snippet eligibility
 * 
 * Google shows FAQ rich results for pages with valid FAQPage markup.
 * We generate 5-7 common betting questions with analysis-based answers.
 */
export function generateFAQSchema(analysis: GameAnalysisResponse): object {
  const matchup = analysis.matchup || "this game"
  const probs = analysis.analysis_content?.model_win_probability
  const teams = extractTeamsFromMatchup(matchup)
  const homeTeam = teams?.homeTeam || "the home team"
  const awayTeam = teams?.awayTeam || "the away team"
  const homeProb = probs?.home_win_prob || 0.5
  const awayProb = probs?.away_win_prob || 0.5
  
  // Get picks from analysis
  const spreadPick = analysis.analysis_content?.ai_spread_pick
  const totalPick = analysis.analysis_content?.ai_total_pick
  const bestBet = analysis.analysis_content?.best_bets?.[0]
  
  const faqs: FAQ[] = []
  
  // Q1: Who will win?
  const favoredTeam = homeProb > awayProb ? homeTeam : awayTeam
  const favoredProb = Math.max(homeProb, awayProb)
  faqs.push({
    question: `Who will win ${matchup}?`,
    answer: `Based on our AI model analysis, ${favoredTeam} is projected to win with a ${(favoredProb * 100).toFixed(0)}% probability. ${analysis.analysis_content?.opening_summary?.slice(0, 200) || ''}`
  })
  
  // Q2: Spread pick
  if (spreadPick?.pick) {
    faqs.push({
      question: `What is the best spread bet for ${matchup}?`,
      answer: `Our AI model recommends ${spreadPick.pick}. ${spreadPick.rationale || ''}`.trim()
    })
  }
  
  // Q3: Over/under pick
  if (totalPick?.pick) {
    faqs.push({
      question: `Should I bet the over or under for ${matchup}?`,
      answer: `Our model suggests ${totalPick.pick}. ${totalPick.rationale || ''}`.trim()
    })
  }
  
  // Q4: Best bet
  if (bestBet?.pick) {
    faqs.push({
      question: `What is the best bet for ${matchup}?`,
      answer: `Our top pick is ${bestBet.pick}. ${bestBet.rationale || ''}`.trim()
    })
  }
  
  // Q5: Win probability
  faqs.push({
    question: `What are the win probabilities for ${matchup}?`,
    answer: `${homeTeam} has a ${(homeProb * 100).toFixed(0)}% chance to win, while ${awayTeam} has a ${(awayProb * 100).toFixed(0)}% chance. These probabilities are calculated using our AI model that factors in team stats, injuries, weather, and market data.`
  })
  
  // Q6: Key factors
  const keyStats = analysis.analysis_content?.key_stats
  if (keyStats && keyStats.length > 0) {
    const factorList = keyStats.slice(0, 3).join(". ")
    faqs.push({
      question: `What are the key factors in ${matchup}?`,
      answer: `The main factors influencing this game are: ${factorList}. Our model weighs these factors to generate accurate predictions.`
    })
  }
  
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": faqs.map(faq => ({
      "@type": "Question",
      "name": faq.question,
      "acceptedAnswer": {
        "@type": "Answer",
        "text": faq.answer
      }
    }))
  }
}

/**
 * Generate enhanced SportsEvent schema with teams, venue, and betting context
 */
export function generateSportsEventSchema(analysis: GameAnalysisResponse): object {
  const probs = analysis.analysis_content?.model_win_probability
  const teams = extractTeamsFromMatchup(analysis.matchup)
  const homeTeam = teams?.homeTeam || "Home Team"
  const awayTeam = teams?.awayTeam || "Away Team"
  
  // Parse game date
  const startDate = new Date(analysis.game_time || new Date().toISOString()).toISOString()
  
  // Sport-specific event type
  const sportEventType = getSportEventType(analysis.league || "NFL")
  
  return {
    "@context": "https://schema.org",
    "@type": sportEventType,
    "name": analysis.matchup,
    "description": analysis.seo_metadata?.description || analysis.analysis_content?.opening_summary?.slice(0, 160),
    "startDate": startDate,
    "eventStatus": "https://schema.org/EventScheduled",
    "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
    "sport": getSportName(analysis.league || "NFL"),
    
    // Home team
    "homeTeam": {
      "@type": "SportsTeam",
      "name": homeTeam,
      "sport": getSportName(analysis.league || "NFL")
    },
    
    // Away team
    "awayTeam": {
      "@type": "SportsTeam",
      "name": awayTeam,
      "sport": getSportName(analysis.league || "NFL")
    },
    
    // Competitors array (for broader compatibility)
    "competitor": [
      {
        "@type": "SportsTeam",
        "name": homeTeam,
        "sport": getSportName(analysis.league || "NFL")
      },
      {
        "@type": "SportsTeam",
        "name": awayTeam,
        "sport": getSportName(analysis.league || "NFL")
      }
    ],
    
    // Venue (if available)
    "location": {
      "@type": "Place",
      "name": `${homeTeam} Home Stadium`,
      "address": {
        "@type": "PostalAddress",
        "addressCountry": "US"
      }
    },
    
    // Organizer
    "organizer": {
      "@type": "SportsOrganization",
      "name": analysis.league || "NFL"
    }
  }
}

/**
 * Generate Article schema for the analysis content
 */
export function generateArticleSchema(analysis: GameAnalysisResponse): object {
  const slug = String(analysis.slug || "").replace(/^\//, "")
  return {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": analysis.seo_metadata?.title || `${analysis.matchup} Prediction & Analysis`,
    "description": analysis.seo_metadata?.description || analysis.analysis_content?.opening_summary?.slice(0, 160),
    "datePublished": analysis.generated_at,
    "dateModified": analysis.generated_at,
    "author": {
      "@type": "Organization",
      "name": "Parlay Gorilla",
      "url": SITE_URL
    },
    "publisher": {
      "@type": "Organization",
      "name": "Parlay Gorilla",
      "url": SITE_URL,
      "logo": {
        "@type": "ImageObject",
        "url": LOGO_URL
      }
    },
    "mainEntityOfPage": {
      "@type": "WebPage",
      "@id": `${SITE_URL}/analysis/${slug}`
    },
    "articleSection": "Sports Betting",
    "keywords": analysis.seo_metadata?.keywords || `${analysis.matchup}, prediction, picks, betting, ${analysis.league}`
  }
}

/**
 * Generate BettingOffer schema (experimental, for betting context)
 */
export function generateBettingOfferSchema(analysis: GameAnalysisResponse): object | null {
  const spreadPick = analysis.analysis_content?.ai_spread_pick
  const totalPick = analysis.analysis_content?.ai_total_pick
  
  if (!spreadPick?.pick && !totalPick?.pick) {
    return null
  }
  
  const offers = []
  
  if (spreadPick?.pick) {
    offers.push({
      "@type": "Offer",
      "name": `Spread Pick: ${spreadPick.pick}`,
      "description": spreadPick.rationale || "AI-powered spread recommendation",
      "category": "Sports Betting - Spread"
    })
  }
  
  if (totalPick?.pick) {
    offers.push({
      "@type": "Offer", 
      "name": `Total Pick: ${totalPick.pick}`,
      "description": totalPick.rationale || "AI-powered over/under recommendation",
      "category": "Sports Betting - Total"
    })
  }
  
  return {
    "@context": "https://schema.org",
    "@type": "ItemList",
    "name": `${analysis.matchup} Betting Picks`,
    "description": "AI-powered betting recommendations",
    "itemListElement": offers.map((offer, index) => ({
      "@type": "ListItem",
      "position": index + 1,
      "item": offer
    }))
  }
}

/**
 * Generate combined schema graph for the page
 */
export function generateSchemaGraph(analysis: GameAnalysisResponse): object {
  const schemas = [
    generateArticleSchema(analysis),
    generateSportsEventSchema(analysis),
    generateFAQSchema(analysis),
  ]
  
  const bettingSchema = generateBettingOfferSchema(analysis)
  if (bettingSchema) {
    schemas.push(bettingSchema)
  }
  
  return {
    "@context": "https://schema.org",
    "@graph": schemas
  }
}

// Helper functions
function getSportEventType(sport: string): string {
  const sportUpper = sport.toUpperCase()
  
  if (sportUpper.includes("NFL") || sportUpper.includes("FOOTBALL")) {
    return "SportsEvent"  // Football game
  }
  if (sportUpper.includes("NBA") || sportUpper.includes("BASKETBALL")) {
    return "SportsEvent"  // Basketball game
  }
  if (sportUpper.includes("NHL") || sportUpper.includes("HOCKEY")) {
    return "SportsEvent"  // Hockey game
  }
  if (sportUpper.includes("MLB") || sportUpper.includes("BASEBALL")) {
    return "SportsEvent"  // Baseball game
  }
  if (sportUpper.includes("SOCCER") || sportUpper.includes("MLS") || sportUpper.includes("EPL")) {
    return "SportsEvent"  // Soccer match
  }
  
  return "SportsEvent"
}

function getSportName(sport: string): string {
  const sportUpper = sport.toUpperCase()
  
  if (sportUpper.includes("NFL")) return "American Football"
  if (sportUpper.includes("NCAAF")) return "College Football"
  if (sportUpper.includes("NBA")) return "Basketball"
  if (sportUpper.includes("NCAAB")) return "College Basketball"
  if (sportUpper.includes("WNBA")) return "Women's Basketball"
  if (sportUpper.includes("NHL")) return "Ice Hockey"
  if (sportUpper.includes("MLB")) return "Baseball"
  if (sportUpper.includes("MLS")) return "Soccer"
  if (sportUpper.includes("EPL")) return "Soccer"
  if (sportUpper.includes("SOCCER")) return "Soccer"
  
  return "Sports"
}

