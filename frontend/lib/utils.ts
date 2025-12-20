import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

import { buildAnalysisUrl } from "@/lib/routing/AnalysisUrlBuilder"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(d)
}

export function formatOdds(price: string): string {
  // Price is already in American format (e.g., "+150", "-110")
  return price
}

/**
 * Generate analysis URL slug for a game
 * Matches backend slug format:
 * - NFL: {sport}/{away}-vs-{home}-week-{week}-{year}
 * - Other: {sport}/{away}-vs-{home}-{date}
 */
export function generateAnalysisUrl(
  sport: string,
  awayTeam: string,
  homeTeam: string,
  startTime: string,
  week?: number | null
): string {
  return buildAnalysisUrl(sport, awayTeam, homeTeam, startTime, week)
}

