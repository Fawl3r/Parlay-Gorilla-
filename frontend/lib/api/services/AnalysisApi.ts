import axios from 'axios'
import { cacheManager, CACHE_TTL, cacheKey } from '@/lib/cache'
import { ApiHttpClients } from '@/lib/api/internal/ApiHttpClientsProvider'
import type { GameAnalysisListItem, GameAnalysisResponse } from '@/lib/api/types'

export class AnalysisApi {
  constructor(private readonly clients: ApiHttpClients) {}

  async getAnalysis(sport: string, slug: string, refresh = false): Promise<GameAnalysisResponse> {
    const key = cacheKey('analysis', sport, slug)

    if (!refresh) {
      const cached = cacheManager.get<GameAnalysisResponse>(key)
      if (cached) {
        const probs = cached.analysis_content?.model_win_probability
        const needsRefresh =
          probs &&
          Math.abs((probs.home_win_prob ?? 0.5) - 0.5) < 0.001 &&
          Math.abs((probs.away_win_prob ?? 0.5) - 0.5) < 0.001

        if (!needsRefresh) {
          console.log('[CACHE HIT] Analysis:', slug)
          return cached
        }

        console.log('[CACHE] Analysis has 50-50 probabilities, requesting refresh')
      }
    }

    try {
      console.log(refresh ? '[REFRESH] Fetching analysis:' : '[CACHE MISS] Fetching analysis:', slug)
      const params = refresh ? { refresh: 'true' } : {}
      const response = await this.clients.gamesClient.get<GameAnalysisResponse>(
        `/api/analysis/${sport}/${slug}`,
        { params }
      )

      cacheManager.set(key, response.data, CACHE_TTL.ANALYSIS_DETAIL)
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error('Analysis API Error Details:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status,
        })
      }
      throw error
    }
  }

  async listUpcomingAnalyses(sport: string, limit: number = 20): Promise<GameAnalysisListItem[]> {
    const key = cacheKey('analysis_list', sport, limit)

    const cached = cacheManager.get<GameAnalysisListItem[]>(key)
    if (cached) {
      console.log('[CACHE HIT] Analysis list:', sport)
      return cached
    }

    try {
      console.log('[CACHE MISS] Fetching analysis list:', sport)
      const response = await this.clients.gamesClient.get<GameAnalysisListItem[]>(
        `/api/analysis/${sport}/upcoming`,
        { params: { limit } }
      )

      cacheManager.set(key, response.data, CACHE_TTL.ANALYSIS_LIST)
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error('List Analyses API Error Details:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status,
        })
      }
      throw error
    }
  }

  async getTeamPhoto(sport: string, teamName: string, opponent?: string): Promise<string | null> {
    const key = cacheKey('team_photo', sport, teamName, opponent || 'none')

    const cached = cacheManager.get<string | null>(key)
    if (cached !== null) {
      console.log('[CACHE HIT] Team photo:', teamName)
      return cached
    }

    try {
      console.log('[CACHE MISS] Fetching team photo:', teamName)
      const response = await this.clients.gamesClient.get<{
        photo_url: string | null
        photo_urls: string[]
      }>(`/api/analysis/${sport}/team-photo`, { params: { team_name: teamName, opponent } })

      const photoUrl =
        response.data.photo_url || (response.data.photo_urls && response.data.photo_urls[0]) || null

      cacheManager.set(key, photoUrl, CACHE_TTL.TEAM_PHOTOS)
      return photoUrl
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error('Team Photo API Error:', error.message)
      }
      cacheManager.set(key, null, CACHE_TTL.TEAM_PHOTOS)
      return null
    }
  }

  async getTeamPhotos(sport: string, teamName: string, opponent?: string): Promise<string[]> {
    const key = cacheKey('team_photos', sport, teamName, opponent || 'none')

    const cached = cacheManager.get<string[]>(key)
    if (cached) {
      console.log('[CACHE HIT] Team photos:', teamName)
      return cached
    }

    try {
      console.log('[CACHE MISS] Fetching team photos:', teamName)
      const response = await this.clients.gamesClient.get<{
        photo_urls: string[]
        photo_url: string | null
      }>(`/api/analysis/${sport}/team-photo`, { params: { team_name: teamName, opponent } })

      let photos: string[] = []
      if (response.data.photo_urls && response.data.photo_urls.length > 0) {
        photos = response.data.photo_urls
      } else if (response.data.photo_url) {
        photos = [response.data.photo_url]
      }

      cacheManager.set(key, photos, CACHE_TTL.TEAM_PHOTOS)
      return photos
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error('Team Photos API Error:', error.message)
      }
      cacheManager.set(key, [], CACHE_TTL.TEAM_PHOTOS)
      return []
    }
  }
}




