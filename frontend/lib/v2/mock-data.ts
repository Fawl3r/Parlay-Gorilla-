/**
 * V2 MOCK DATA UTILITIES
 * Isolated mock data for V2 UI preview
 * NOT connected to production APIs
 */

export type Sport = 'nfl' | 'nba' | 'nhl' | 'mlb' | 'ncaaf' | 'ncaab'

export interface MockPick {
  id: string
  sport: Sport
  league: string
  matchup: string
  homeTeam: string
  awayTeam: string
  pick: string
  pickType: 'moneyline' | 'spread' | 'total'
  odds: number
  confidence: number
  gameTime: string
  aiGenerated: boolean
}

export interface MockParlay {
  id: string
  picks: MockPick[]
  totalOdds: number
  avgConfidence: number
  potentialPayout: number
  stake: number
}

export interface MockLeaderboardEntry {
  rank: number
  username: string
  winRate: number
  totalPicks: number
  roi: number
  avgConfidence: number
}

// Mock picks data
export const MOCK_PICKS: MockPick[] = [
  {
    id: '1',
    sport: 'nfl',
    league: 'NFL',
    matchup: 'Chiefs vs 49ers',
    homeTeam: 'Chiefs',
    awayTeam: '49ers',
    pick: 'Chiefs -3.5',
    pickType: 'spread',
    odds: -110,
    confidence: 78,
    gameTime: '2026-02-16T18:00:00Z',
    aiGenerated: true,
  },
  {
    id: '2',
    sport: 'nba',
    league: 'NBA',
    matchup: 'Lakers vs Celtics',
    homeTeam: 'Celtics',
    awayTeam: 'Lakers',
    pick: 'Over 228.5',
    pickType: 'total',
    odds: -108,
    confidence: 72,
    gameTime: '2026-02-16T19:30:00Z',
    aiGenerated: true,
  },
  {
    id: '3',
    sport: 'nhl',
    league: 'NHL',
    matchup: 'Rangers vs Bruins',
    homeTeam: 'Bruins',
    awayTeam: 'Rangers',
    pick: 'Rangers ML',
    pickType: 'moneyline',
    odds: 150,
    confidence: 65,
    gameTime: '2026-02-16T19:00:00Z',
    aiGenerated: true,
  },
  {
    id: '4',
    sport: 'nba',
    league: 'NBA',
    matchup: 'Warriors vs Nets',
    homeTeam: 'Warriors',
    awayTeam: 'Nets',
    pick: 'Warriors -7.5',
    pickType: 'spread',
    odds: -112,
    confidence: 81,
    gameTime: '2026-02-16T22:00:00Z',
    aiGenerated: true,
  },
  {
    id: '5',
    sport: 'mlb',
    league: 'MLB',
    matchup: 'Yankees vs Red Sox',
    homeTeam: 'Red Sox',
    awayTeam: 'Yankees',
    pick: 'Under 8.5',
    pickType: 'total',
    odds: -105,
    confidence: 69,
    gameTime: '2026-02-16T19:10:00Z',
    aiGenerated: true,
  },
]

// Mock leaderboard data
export const MOCK_LEADERBOARD: MockLeaderboardEntry[] = [
  {
    rank: 1,
    username: 'AI Engine',
    winRate: 64.2,
    totalPicks: 487,
    roi: 12.8,
    avgConfidence: 73.5,
  },
  {
    rank: 2,
    username: 'SharpBettor',
    winRate: 58.9,
    totalPicks: 312,
    roi: 8.4,
    avgConfidence: 68.2,
  },
  {
    rank: 3,
    username: 'DataDegen',
    winRate: 57.1,
    totalPicks: 294,
    roi: 6.9,
    avgConfidence: 65.8,
  },
  {
    rank: 4,
    username: 'ParlayCrusher',
    winRate: 55.3,
    totalPicks: 421,
    roi: 5.2,
    avgConfidence: 62.4,
  },
  {
    rank: 5,
    username: 'AnalyticsPro',
    winRate: 54.7,
    totalPicks: 268,
    roi: 4.8,
    avgConfidence: 61.9,
  },
]

// Helper functions
export function formatOdds(odds: number): string {
  if (odds > 0) return `+${odds}`
  return odds.toString()
}

export function getSportColor(sport: Sport): string {
  const colors: Record<Sport, string> = {
    nfl: 'bg-blue-500/20 text-blue-300',
    nba: 'bg-orange-500/20 text-orange-300',
    nhl: 'bg-cyan-500/20 text-cyan-300',
    mlb: 'bg-red-500/20 text-red-300',
    ncaaf: 'bg-purple-500/20 text-purple-300',
    ncaab: 'bg-amber-500/20 text-amber-300',
  }
  return colors[sport]
}

export function getConfidenceColor(confidence: number): string {
  if (confidence >= 75) return 'text-emerald-400'
  if (confidence >= 65) return 'text-yellow-400'
  return 'text-orange-400'
}

export function getConfidenceBgColor(confidence: number): string {
  if (confidence >= 75) return 'bg-emerald-500'
  if (confidence >= 65) return 'bg-yellow-500'
  return 'bg-orange-500'
}
