import axios from 'axios'
import { cacheManager, CACHE_TTL, cacheKey } from '@/lib/cache'
import { ApiHttpClients } from '@/lib/api/internal/ApiHttpClientsProvider'
import type { GameResponse, NFLWeeksResponse, GameFeedResponse } from '@/lib/api/types'

export class GamesApi {
  constructor(private readonly clients: ApiHttpClients) {}

  async getGames(
    sport: string = 'nfl',
    week?: number,
    forceRefresh: boolean = false
  ): Promise<GameResponse[]> {
    const key = cacheKey('games', sport, week || 'all')

    // Check cache first (unless force refresh)
    if (!forceRefresh) {
      const cached = cacheManager.get<GameResponse[]>(key)
      if (cached) {
        console.log(`[CACHE HIT] ${sport.toUpperCase()} games (${cached.length} games)`)
        return cached
      }
    } else {
      cacheManager.delete(key)
      console.log(`[CACHE CLEAR] Clearing cache for ${sport.toUpperCase()} games`)
    }

    try {
      console.log(
        `[CACHE MISS] Fetching ${sport.toUpperCase()} games${week ? ` for week ${week}` : ''}...`
      )
      const startTime = Date.now()

      const params: Record<string, any> = { refresh: forceRefresh }
      if (week) params.week = week

      const response = await this.clients.gamesClient.get<GameResponse[]>(
        `/api/sports/${sport}/games`,
        {
          params,
          timeout: 30000,
        }
      )

      const elapsed = Date.now() - startTime
      console.log(`Games fetched in ${elapsed}ms, received ${response.data.length} games`)

      cacheManager.set(key, response.data, CACHE_TTL.GAMES)
      return response.data
    } catch (error: any) {
      if (axios.isAxiosError(error)) {
        console.error('API Error Details:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status,
          statusText: error.response?.statusText,
          code: error.code,
        })

        if (
          error.code === 'ECONNABORTED' ||
          error.code === 'ERR_NETWORK' ||
          error.message?.includes('timeout')
        ) {
          const timeoutError: any = new Error('Backend connection timeout')
          timeoutError.isTimeout = true
          timeoutError.code = error.code
          throw timeoutError
        }
      } else {
        console.error('API Error Details:', error)
      }
      throw error
    }
  }

  async warmupCache(): Promise<void> {
    try {
      // Warmup is an admin-only operation (it can trigger heavy server work).
      // Never call it from public pages like the landing page.
      if (typeof window === 'undefined') return
      const pathname = window.location.pathname || ''
      if (!pathname.startsWith('/admin')) return

      console.log('Warming up cache for all sports...')
      await this.clients.gamesClient.get('/api/warmup')
      console.log('Cache warmup complete')
    } catch (error) {
      console.warn('Cache warmup failed (non-critical):', error)
    }
  }

  async getNFLWeeks(): Promise<NFLWeeksResponse> {
    const key = cacheKey('nfl_weeks')

    const cached = cacheManager.get<NFLWeeksResponse>(key)
    if (cached) {
      console.log('[CACHE HIT] NFL weeks')
      return cached
    }

    try {
      console.log('[CACHE MISS] Fetching NFL weeks...')
      const response = await this.clients.gamesClient.get<NFLWeeksResponse>('/api/weeks/nfl')
      cacheManager.set(key, response.data, CACHE_TTL.NFL_WEEKS)
      return response.data
    } catch (error) {
      console.error('Error fetching NFL weeks:', error)
      return {
        current_week: null,
        season_year: new Date().getFullYear(),
        weeks: [],
      }
    }
  }

  async getNFLGames(): Promise<GameResponse[]> {
    return this.getGames('nfl')
  }

  async listSports(): Promise<
    Array<{
      slug: string
      code: string
      display_name: string
      default_markets: string[]
      in_season?: boolean
      status_label?: string
      upcoming_games?: number
    }>
  > {
    const key = cacheKey('sports_list')

    const cached = cacheManager.get<
      Array<{
        slug: string
        code: string
        display_name: string
        default_markets: string[]
        in_season?: boolean
        status_label?: string
        upcoming_games?: number
      }>
    >(key)
    if (cached) {
      console.log('[CACHE HIT] Sports list')
      return cached.map((s) => ({
        ...s,
        in_season: s.in_season ?? true,
        status_label: s.status_label ?? (s.in_season === false ? 'Not in season' : 'In season'),
      }))
    }

    const fallbackSports: Array<{
      slug: string
      code: string
      display_name: string
      default_markets: string[]
      in_season?: boolean
      status_label?: string
    }> = [
      { slug: 'nfl', code: 'americanfootball_nfl', display_name: 'NFL', default_markets: ['h2h', 'spreads', 'totals'], in_season: true, status_label: 'In season' },
      { slug: 'nba', code: 'basketball_nba', display_name: 'NBA', default_markets: ['h2h', 'spreads', 'totals'], in_season: true, status_label: 'In season' },
      { slug: 'nhl', code: 'icehockey_nhl', display_name: 'NHL', default_markets: ['h2h', 'spreads', 'totals'], in_season: true, status_label: 'In season' },
      { slug: 'mlb', code: 'baseball_mlb', display_name: 'MLB', default_markets: ['h2h', 'spreads', 'totals'], in_season: true, status_label: 'In season' },
      { slug: 'ncaaf', code: 'americanfootball_ncaaf', display_name: 'NCAAF', default_markets: ['h2h', 'spreads', 'totals'], in_season: true, status_label: 'In season' },
      { slug: 'ncaab', code: 'basketball_ncaab', display_name: 'NCAAB', default_markets: ['h2h', 'spreads', 'totals'], in_season: true, status_label: 'In season' },
      { slug: 'epl', code: 'soccer_epl', display_name: 'Premier League', default_markets: ['h2h', 'spreads', 'totals'], in_season: true, status_label: 'In season' },
      { slug: 'mls', code: 'soccer_usa_mls', display_name: 'MLS', default_markets: ['h2h', 'spreads', 'totals'], in_season: true, status_label: 'In season' },
    ]

    try {
      console.log('[CACHE MISS] Fetching sports list...')
      const response = await this.clients.gamesClient.get('/api/sports', { timeout: 10000 })
      const normalized = (response.data as any[]).map((s) => ({
        ...s,
        in_season: (s?.in_season ?? true) as boolean,
        status_label: (s?.status_label ?? (s?.in_season === false ? 'Not in season' : 'In season')) as string,
      }))
      cacheManager.set(key, normalized, CACHE_TTL.SPORTS_LIST)
      console.log('[SUCCESS] Sports list fetched:', response.data.length, 'sports')
      return normalized
    } catch (error: any) {
      console.error('Error fetching sports list:', error)
      cacheManager.set(key, fallbackSports, 60) // Cache for 1 minute
      return fallbackSports
    }
  }

  async healthCheck(): Promise<{ status: string; timestamp: string; service: string }> {
    const key = cacheKey('health_check')

    const cached = cacheManager.get<{ status: string; timestamp: string; service: string }>(key)
    if (cached) return cached

    const response = await this.clients.apiClient.get('/health')
    cacheManager.set(key, response.data, CACHE_TTL.HEALTH_CHECK)
    return response.data
  }

  async getGameFeed(
    sport?: string,
    window: "today" | "upcoming" | "live" | "all" = "today"
  ): Promise<GameFeedResponse[]> {
    const params: Record<string, any> = { window }
    if (sport) params.sport = sport

    const response = await this.clients.apiClient.get<GameFeedResponse[]>('/api/v1/games/feed', {
      params,
      timeout: 30000,
    })
    return response.data
  }
}


