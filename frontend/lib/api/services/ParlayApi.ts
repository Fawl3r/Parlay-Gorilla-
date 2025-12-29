import axios from 'axios'
import { cacheManager, CACHE_TTL, cacheKey } from '@/lib/cache'
import { ApiHttpClients } from '@/lib/api/internal/ApiHttpClientsProvider'
import type {
  CustomParlayAnalysisResponse,
  CustomParlayLeg,
  CounterParlayRequest,
  CounterParlayResponse,
  ParlayCoverageRequest,
  ParlayCoverageResponse,
  ParlayRequest,
  ParlayResponse,
  SaveAiParlayRequest,
  SaveCustomParlayRequest,
  SavedParlayResponse,
  TripleParlayRequest,
  TripleParlayResponse,
  UpsetFinderResponse,
  UpsetRiskTier,
} from '@/lib/api/types'
import type { ParlayDetail, ParlayHistoryItem } from '@/lib/api/parlay-results-types'

export class ParlayApi {
  constructor(private readonly clients: ApiHttpClients) {}

  async suggestParlay(request: ParlayRequest): Promise<ParlayResponse> {
    const key = cacheKey(
      'parlay',
      request.num_legs,
      request.risk_profile,
      request.sports?.join(',') || 'all',
      request.mix_sports ? 'mixed' : 'single',
      request.week || 'all'
    )

    const cached = cacheManager.get<ParlayResponse>(key)
    if (cached) {
      console.log('[CACHE HIT] Parlay suggestion')
      return cached
    }

    try {
      console.log('[CACHE MISS] Sending parlay request:', request)
      const response = await this.clients.apiClient.post<ParlayResponse>('/api/parlay/suggest', request)

      cacheManager.set(key, response.data, CACHE_TTL.PARLAY)
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error('Parlay API Error Details:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status,
          statusText: error.response?.statusText,
        })

        if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
          const timeoutError: any = new Error(
            'Parlay generation timed out. Please try again in a moment.'
          )
          timeoutError.isTimeout = true
          timeoutError.code = error.code
          throw timeoutError
        }

        if (error.response?.status === 504) {
          const timeoutError: any = new Error(
            (error.response.data as any)?.detail ||
              'Parlay generation timed out. Please try again with fewer legs or a different risk profile.'
          )
          timeoutError.isTimeout = true
          timeoutError.code = 'TIMEOUT'
          throw timeoutError
        }
      } else {
        console.error('Parlay API Error Details:', error)
      }
      throw error
    }
  }

  async suggestTripleParlay(request?: TripleParlayRequest): Promise<TripleParlayResponse> {
    const payload = request ?? {}

    const key = cacheKey(
      'triple_parlay',
      payload.sports?.join(',') || 'all',
      payload.safe_legs || 'default',
      payload.balanced_legs || 'default',
      payload.degen_legs || 'default'
    )

    const cached = cacheManager.get<TripleParlayResponse>(key)
    if (cached) {
      console.log('[CACHE HIT] Triple parlay suggestion')
      return cached
    }

    try {
      console.log('[CACHE MISS] Sending triple parlay request:', payload)
      const response = await this.clients.apiClient.post<TripleParlayResponse>(
        '/api/parlay/suggest/triple',
        payload
      )

      cacheManager.set(key, response.data, CACHE_TTL.TRIPLE_PARLAY)
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error('Triple Parlay API Error Details:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status,
          statusText: error.response?.statusText,
        })
      } else {
        console.error('Triple Parlay API Error Details:', error)
      }
      throw error
    }
  }

  async analyzeCustomParlay(legs: CustomParlayLeg[]): Promise<CustomParlayAnalysisResponse> {
    try {
      console.log(`Analyzing custom parlay with ${legs.length} legs...`, legs)
      const response = await this.clients.apiClient.post<CustomParlayAnalysisResponse>(
        '/api/parlay/analyze',
        { legs }
      )
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const errorData = error.response?.data
        console.error('Custom Parlay Analysis Error:', {
          message: error.message,
          response: errorData,
          status: error.response?.status,
        })

        if (error.response?.status === 422 && (errorData as any)?.detail) {
          const detail = Array.isArray((errorData as any).detail)
            ? (errorData as any).detail
                .map((err: any) => `${err.loc?.join('.')}: ${err.msg}`)
                .join('; ')
            : (errorData as any).detail
          throw new Error(`Validation error: ${detail}`)
        }

        throw new Error((errorData as any)?.detail || (errorData as any)?.message || 'Failed to analyze parlay')
      }
      throw error
    }
  }

  async buildCounterParlay(request: CounterParlayRequest): Promise<CounterParlayResponse> {
    try {
      const legsCount = request.legs?.length ?? 0
      console.log(`Building counter parlay from ${legsCount} legs...`, request)
      const response = await this.clients.apiClient.post<CounterParlayResponse>(
        '/api/parlay/counter',
        request
      )
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const errorData = error.response?.data
        console.error('Counter Parlay Error:', {
          message: error.message,
          response: errorData,
          status: error.response?.status,
        })

        if (error.response?.status === 422 && (errorData as any)?.detail) {
          const detail = Array.isArray((errorData as any).detail)
            ? (errorData as any).detail
                .map((err: any) => `${err.loc?.join('.')}: ${err.msg}`)
                .join('; ')
            : (errorData as any).detail
          throw new Error(`Validation error: ${detail}`)
        }

        throw new Error((errorData as any)?.detail || (errorData as any)?.message || 'Failed to build counter parlay')
      }
      throw error
    }
  }

  async buildCoveragePack(request: ParlayCoverageRequest): Promise<ParlayCoverageResponse> {
    try {
      const legsCount = request.legs?.length ?? 0
      console.log(`Building coverage pack from ${legsCount} legs...`, request)
      const response = await this.clients.apiClient.post<ParlayCoverageResponse>(
        '/api/parlay/coverage',
        request
      )
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const errorData = error.response?.data
        console.error('Coverage Pack Error:', {
          message: error.message,
          response: errorData,
          status: error.response?.status,
        })

        if (error.response?.status === 422 && (errorData as any)?.detail) {
          const detail = Array.isArray((errorData as any).detail)
            ? (errorData as any).detail
                .map((err: any) => `${err.loc?.join('.')}: ${err.msg}`)
                .join('; ')
            : (errorData as any).detail
          throw new Error(`Validation error: ${detail}`)
        }

        throw new Error((errorData as any)?.detail || (errorData as any)?.message || 'Failed to build coverage pack')
      }
      throw error
    }
  }

  async getUpsets(options: {
    sport: string
    min_edge?: number
    max_results?: number
    risk_tier?: UpsetRiskTier
    week?: number
  }): Promise<UpsetFinderResponse> {
    const sport = (options.sport || 'NFL').toLowerCase()
    const params: Record<string, any> = {}
    if (options.min_edge !== undefined) params.min_edge = options.min_edge
    if (options.max_results !== undefined) params.max_results = options.max_results
    if (options.risk_tier !== undefined) params.risk_tier = options.risk_tier
    if (options.week !== undefined) params.week = options.week

    try {
      const response = await this.clients.apiClient.get<UpsetFinderResponse>(`/api/parlay/upsets/${sport}`, { params })
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const errorData = error.response?.data
        console.error('Upset Finder Error:', {
          message: error.message,
          response: errorData,
          status: error.response?.status,
        })

        if (error.response?.status === 422 && (errorData as any)?.detail) {
          const detail = Array.isArray((errorData as any).detail)
            ? (errorData as any).detail.map((err: any) => `${err.loc?.join('.')}: ${err.msg}`).join('; ')
            : (errorData as any).detail
          throw new Error(`Validation error: ${detail}`)
        }

        throw new Error((errorData as any)?.detail || (errorData as any)?.message || 'Failed to load upset candidates')
      }
      throw error
    }
  }

  // ============================================================================
  // Parlay Results / History (AI-generated)
  // ============================================================================

  async getParlayHistory(limit: number = 50, offset: number = 0): Promise<ParlayHistoryItem[]> {
    const response = await this.clients.apiClient.get<ParlayHistoryItem[]>('/api/parlays/history', {
      params: { limit, offset },
    })
    return response.data
  }

  async getParlayDetail(parlayId: string): Promise<ParlayDetail> {
    const response = await this.clients.apiClient.get<ParlayDetail>(`/api/parlays/${parlayId}`)
    return response.data
  }

  // ============================================================================
  // Saved Parlays
  // ============================================================================

  async saveCustomParlay(request: SaveCustomParlayRequest): Promise<SavedParlayResponse> {
    const response = await this.clients.apiClient.post<SavedParlayResponse>('/api/parlays/custom/save', request)
    return response.data
  }

  async saveAiParlay(request: SaveAiParlayRequest): Promise<SavedParlayResponse> {
    const response = await this.clients.apiClient.post<SavedParlayResponse>('/api/parlays/ai/save', request)
    return response.data
  }

  async listSavedParlays(
    type: 'all' | 'custom' | 'ai' = 'all',
    limit: number = 50,
    includeResults: boolean = false
  ): Promise<SavedParlayResponse[]> {
    const response = await this.clients.apiClient.get<SavedParlayResponse[]>('/api/parlays/saved', {
      params: { type, limit, include_results: includeResults },
    })
    return response.data
  }

  async retryParlayInscription(savedParlayId: string): Promise<SavedParlayResponse> {
    const response = await this.clients.apiClient.post<SavedParlayResponse>(
      `/api/parlays/${savedParlayId}/inscription/retry`
    )
    return response.data
  }

  async queueInscription(savedParlayId: string): Promise<SavedParlayResponse> {
    const response = await this.clients.apiClient.post<SavedParlayResponse>(
      `/api/parlays/${savedParlayId}/inscription/queue`
    )
    return response.data
  }
}


