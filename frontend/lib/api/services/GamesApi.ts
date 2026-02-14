import axios from 'axios'
import { cacheManager, CACHE_TTL, cacheKey } from '@/lib/cache'
import { ApiHttpClients } from '@/lib/api/internal/ApiHttpClientsProvider'
import type { GameResponse, GamesListResponse, NFLWeeksResponse, GameFeedResponse, SportListItem } from '@/lib/api/types'

export class GamesApi {
  constructor(private readonly clients: ApiHttpClients) {}

  async getGames(
    sport: string = 'nfl',
    week?: number,
    forceRefresh: boolean = false
  ): Promise<GamesListResponse> {
    const key = cacheKey('games', sport, week || 'all')

    if (!forceRefresh) {
      const cached = cacheManager.get<GamesListResponse>(key)
      if (cached) {
        console.log(`[CACHE HIT] ${sport.toUpperCase()} games (${cached.games.length} games)`)
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

      const response = await this.clients.gamesClient.get<GamesListResponse>(
        `/api/sports/${sport}/games`,
        {
          params,
          timeout: 30000,
        }
      )

      const data = response.data as GamesListResponse
      const games = Array.isArray(data?.games) ? data.games : []
      const payload: GamesListResponse = {
        games,
        sport_state: data?.sport_state ?? undefined,
        next_game_at: data?.next_game_at ?? undefined,
        status_label: data?.status_label ?? undefined,
        days_to_next: data?.days_to_next ?? undefined,
        preseason_enable_days: data?.preseason_enable_days ?? undefined,
      }

      const elapsed = Date.now() - startTime
      console.log(`Games fetched in ${elapsed}ms, received ${games.length} games`)

      cacheManager.set(key, payload, CACHE_TTL.GAMES)
      return payload
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

  async getNFLGames(): Promise<GamesListResponse> {
    return this.getGames('nfl')
  }

  async listSports(): Promise<SportListItem[]> {
    const key = cacheKey('sports_list')

    const cached = cacheManager.get<SportListItem[]>(key)
    if (cached) {
      console.log('[CACHE HIT] Sports list')
      return cached.map((s) => ({
        ...s,
        in_season: s.in_season ?? true,
        status_label: s.status_label ?? (s.in_season === false ? 'Not in season' : 'In season'),
        is_enabled: typeof s.is_enabled === 'boolean' ? s.is_enabled : (s.in_season !== false),
      }))
    }

    const fallbackSports: SportListItem[] = [
      { slug: 'nfl', code: 'americanfootball_nfl', display_name: 'NFL', default_markets: ['h2h', 'spreads', 'totals'], in_season: true, status_label: 'In season', sport_state: 'IN_SEASON', is_enabled: true },
      { slug: 'nba', code: 'basketball_nba', display_name: 'NBA', default_markets: ['h2h', 'spreads', 'totals'], in_season: true, status_label: 'In season', sport_state: 'IN_SEASON', is_enabled: true },
      { slug: 'nhl', code: 'icehockey_nhl', display_name: 'NHL', default_markets: ['h2h', 'spreads', 'totals'], in_season: true, status_label: 'In season', sport_state: 'IN_SEASON', is_enabled: true },
      { slug: 'mlb', code: 'baseball_mlb', display_name: 'MLB', default_markets: ['h2h', 'spreads', 'totals'], in_season: true, status_label: 'In season', sport_state: 'IN_SEASON', is_enabled: true },
      { slug: 'ncaaf', code: 'americanfootball_ncaaf', display_name: 'NCAAF', default_markets: ['h2h', 'spreads', 'totals'], in_season: true, status_label: 'In season', sport_state: 'IN_SEASON', is_enabled: true },
      { slug: 'ncaab', code: 'basketball_ncaab', display_name: 'NCAAB', default_markets: ['h2h', 'spreads', 'totals'], in_season: true, status_label: 'In season', sport_state: 'IN_SEASON', is_enabled: true },
      { slug: 'epl', code: 'soccer_epl', display_name: 'Premier League', default_markets: ['h2h', 'spreads', 'totals'], in_season: true, status_label: 'In season', sport_state: 'IN_SEASON', is_enabled: true },
      { slug: 'mls', code: 'soccer_usa_mls', display_name: 'MLS', default_markets: ['h2h', 'spreads', 'totals'], in_season: true, status_label: 'In season', sport_state: 'IN_SEASON', is_enabled: true },
    ]

    try {
      console.log('[CACHE MISS] Fetching sports list...')
      const response = await this.clients.gamesClient.get('/api/sports', { timeout: 10000 })
      const raw = (response.data as any[]) || []
      const normalized: SportListItem[] = raw.map((s: any) => ({
        slug: s?.slug ?? '',
        code: s?.code ?? '',
        display_name: s?.display_name ?? '',
        default_markets: Array.isArray(s?.default_markets) ? s.default_markets : [],
        in_season: s?.in_season ?? true,
        status_label: s?.status_label ?? (s?.in_season === false ? 'Not in season' : 'In season'),
        upcoming_games: typeof s?.upcoming_games === 'number' ? s.upcoming_games : undefined,
        sport_state: s?.sport_state ?? (s?.in_season ? 'IN_SEASON' : 'OFFSEASON'),
        next_game_at: s?.next_game_at ?? undefined,
        last_game_at: s?.last_game_at ?? undefined,
        state_reason: s?.state_reason ?? undefined,
        is_enabled: typeof s?.is_enabled === 'boolean' ? s.is_enabled : (s?.in_season !== false),
        days_to_next: typeof s?.days_to_next === 'number' ? s.days_to_next : undefined,
        preseason_enable_days: typeof s?.preseason_enable_days === 'number' ? s.preseason_enable_days : undefined,
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

    const response = await this.clients.apiClient.get<GameFeedResponse[]>('/api/games/feed', {
      params,
      timeout: 30000,
    })
    return response.data
  }
}


