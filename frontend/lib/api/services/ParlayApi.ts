import axios from 'axios'
import { cacheManager, CACHE_TTL, cacheKey } from '@/lib/cache'
import { ApiHttpClients } from '@/lib/api/internal/ApiHttpClientsProvider'
import type {
  CustomParlayAnalysisResponse,
  CustomParlayLeg,
  CounterParlayRequest,
  CounterParlayResponse,
  HedgesRequest,
  HedgesResponse,
  ParlayCoverageRequest,
  ParlayCoverageResponse,
  ParlayRequest,
  ParlayResponse,
  ParlaySuggestError,
  InsufficientCandidatesError,
  SaveAiParlayRequest,
  SaveCustomParlayRequest,
  SavedParlayResponse,
  VerificationRecordResponse,
  TripleParlayRequest,
  TripleParlayResponse,
  UpsetFinderResponse,
  UpsetRiskTier,
} from '@/lib/api/types'
import type { ParlayDetail, ParlayHistoryItem } from '@/lib/api/parlay-results-types'

export class ParlayApi {
  constructor(private readonly clients: ApiHttpClients) {}

  private assertValidParlayResponse(response: ParlayResponse) {
    const legs = response?.legs
    const numLegs = response?.num_legs
    const hasLegs = Array.isArray(legs) && legs.length > 0
    const hasCount = typeof numLegs === 'number' && Number.isFinite(numLegs) && numLegs > 0

    if (!hasLegs || !hasCount) {
      const err: any = new Error(
        'Parlay generation returned no picks. Please try again in a moment or choose different sport(s).'
      )
      err.code = 'EMPTY_PARLAY'
      throw err
    }
  }

  async suggestParlay(request: ParlayRequest): Promise<ParlayResponse> {
    const key = cacheKey(
      'parlay',
      request.num_legs,
      request.risk_profile,
      request.sports?.join(',') || 'all',
      request.mix_sports ? 'mixed' : 'single',
      request.week || 'all',
      request.request_mode === 'TRIPLE' ? 'triple' : 'default'
    )

    const cached = cacheManager.get<ParlayResponse>(key)
    if (cached) {
      console.log('[CACHE HIT] Parlay suggestion')
      return cached
    }

    try {
      console.log('[CACHE MISS] Sending parlay request:', request)
      const response = await this.clients.apiClient.post<ParlayResponse>('/api/parlay/suggest', request)

      this.assertValidParlayResponse(response.data)
      cacheManager.set(key, response.data, CACHE_TTL.PARLAY)
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const errorData = error.response?.data
        console.error('Parlay API Error Details:', {
          message: error.message,
          response: errorData,
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
            (errorData as any)?.detail ||
              'Parlay generation timed out. Please try again with fewer legs or a different risk profile.'
          )
          timeoutError.isTimeout = true
          timeoutError.code = 'TIMEOUT'
          throw timeoutError
        }

        // 401/402/403 with typed ParlaySuggestError (login_required, premium_required, credits_required)
        if ([401, 402, 403].includes(error.response?.status ?? 0) && errorData && typeof errorData === 'object') {
          const body = errorData as Record<string, unknown>
          if (typeof body.code === 'string' && typeof body.message === 'string') {
            const suggestError: ParlaySuggestError = {
              code: body.code as ParlaySuggestError['code'],
              message: body.message,
              hint: body.hint != null ? String(body.hint) : undefined,
              meta: body.meta != null && typeof body.meta === 'object' ? (body.meta as Record<string, unknown>) : undefined,
            }
            const typedError: any = new Error(suggestError.message)
            typedError.parlaySuggestError = suggestError
            typedError.code = suggestError.code
            typedError.statusCode = error.response?.status
            throw typedError
          }
        }

        // Handle 503 Service Unavailable (e.g. OOM / heavy load)
        if (error.response?.status === 503) {
          const body = errorData && typeof errorData === 'object' ? (errorData as Record<string, unknown>) : {}
          const detail = typeof body.detail === 'string' ? body.detail : "We're under heavy load. Try fewer picks or single sport."
          const serviceError: any = new Error(detail)
          serviceError.isServerError = true
          serviceError.code = 'SERVICE_UNAVAILABLE'
          serviceError.statusCode = 503
          throw serviceError
        }

        // Handle 500 Internal Server Error
        if (error.response?.status === 500) {
          const body = errorData && typeof errorData === 'object' ? (errorData as Record<string, unknown>) : {}
          const detail = typeof body.detail === 'string' ? body.detail : 'Server error occurred while generating parlay. Please try again in a moment.'
          const serverError: any = new Error(detail)
          serverError.isServerError = true
          serverError.code = 'SERVER_ERROR'
          serverError.statusCode = 500
          throw serverError
        }

        // 409 request_dedupe: same options requested too soon; show friendly message (not a hard error)
        if (error.response?.status === 409 && errorData && typeof errorData === 'object') {
          const body = errorData as Record<string, unknown>
          if (body.code === 'request_dedupe') {
            const dedupeError: any = new Error(
              typeof body.detail === 'string' ? body.detail : 'Please wait a moment before requesting the same parlay again.'
            )
            dedupeError.code = 'request_dedupe'
            dedupeError.statusCode = 409
            dedupeError.isRetryable = true
            throw dedupeError
          }
        }

        // 429 rate limit: friendly message, treat as retryable
        if (error.response?.status === 429) {
          const rateLimitError: any = new Error(
            (errorData as any)?.detail || 'Too many requests. Please slow down and try again in a few minutes.'
          )
          rateLimitError.code = 'rate_limit'
          rateLimitError.statusCode = 429
          rateLimitError.isRetryable = true
          throw rateLimitError
        }

        // 409 with structured InsufficientCandidatesError (needed, have, top_exclusion_reasons, debug_id)
        if (error.response?.status === 409 && errorData && typeof errorData === 'object') {
          const body = errorData as Record<string, unknown>
          if (
            typeof body.needed === 'number' &&
            typeof body.have === 'number' &&
            Array.isArray(body.top_exclusion_reasons) &&
            typeof body.debug_id === 'string'
          ) {
            const rawReasons = body.top_exclusion_reasons as (string | Record<string, unknown>)[]
            const insufficientError: InsufficientCandidatesError = {
              code: 'insufficient_candidates',
              message: typeof body.message === 'string' ? body.message : 'Not enough games available.',
              hint: body.hint != null ? String(body.hint) : undefined,
              needed: body.needed,
              have: body.have,
              top_exclusion_reasons: rawReasons as InsufficientCandidatesError['top_exclusion_reasons'],
              debug_id: body.debug_id,
              meta: body.meta != null && typeof body.meta === 'object' ? (body.meta as Record<string, unknown>) : undefined,
            }
            const typedError: any = new Error(insufficientError.message)
            typedError.insufficientCandidatesError = insufficientError
            typedError.parlaySuggestError = { code: 'insufficient_candidates', message: insufficientError.message, hint: insufficientError.hint, meta: insufficientError.meta }
            typedError.code = 'insufficient_candidates'
            typedError.statusCode = 409
            throw typedError
          }
        }

        // 422 with typed ParlaySuggestError (invalid_request, etc.)
        if (error.response?.status === 422 && errorData && typeof errorData === 'object') {
          const body = errorData as Record<string, unknown>
          if (typeof body.code === 'string' && typeof body.message === 'string') {
            const suggestError: ParlaySuggestError = {
              code: body.code as ParlaySuggestError['code'],
              message: body.message,
              hint: body.hint != null ? String(body.hint) : undefined,
              meta: body.meta != null && typeof body.meta === 'object' ? (body.meta as Record<string, unknown>) : undefined,
            }
            const typedError: any = new Error(suggestError.message)
            typedError.parlaySuggestError = suggestError
            typedError.code = suggestError.code
            typedError.statusCode = error.response?.status
            throw typedError
          }
        }

        // FastAPI validation errors (422 with detail array) - not our typed ParlaySuggestError
        if (error.response?.status === 422 && (errorData as any)?.detail) {
          const rawDetail = (errorData as any).detail
          const detail = Array.isArray(rawDetail)
            ? rawDetail
                .map((err: any) => {
                  const loc = Array.isArray(err?.loc)
                    ? err.loc.filter((p: any) => p !== 'body').join('.')
                    : ''
                  const msg = String(err?.msg || err?.message || 'Invalid value')
                  return loc ? `${loc}: ${msg}` : msg
                })
                .filter(Boolean)
                .join('; ')
            : typeof rawDetail === 'string'
              ? rawDetail
              : JSON.stringify(rawDetail)
          throw new Error(`Validation error: ${detail}`)
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

  async buildHedges(request: HedgesRequest): Promise<HedgesResponse> {
    try {
      const response = await this.clients.apiClient.post<HedgesResponse>(
        '/api/parlay/hedges',
        request
      )
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const errorData = error.response?.data
        if (error.response?.status === 422 && (errorData as any)?.detail) {
          const detail = Array.isArray((errorData as any).detail)
            ? (errorData as any).detail.map((err: any) => `${err.loc?.join('.')}: ${err.msg}`).join('; ')
            : (errorData as any).detail
          throw new Error(`Validation error: ${detail}`)
        }
        throw new Error((errorData as any)?.detail || (errorData as any)?.message || 'Failed to build hedges')
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

  async retryVerificationRecord(savedParlayId: string): Promise<VerificationRecordResponse> {
    const response = await this.clients.apiClient.post<VerificationRecordResponse>(
      `/api/parlays/${savedParlayId}/verification/retry`
    )
    return response.data
  }

  async queueVerificationRecord(savedParlayId: string): Promise<VerificationRecordResponse> {
    const response = await this.clients.apiClient.post<VerificationRecordResponse>(
      `/api/parlays/${savedParlayId}/verification/queue`
    )
    return response.data
  }

  async getVerificationRecord(verificationId: string): Promise<VerificationRecordResponse> {
    try {
    const response = await this.clients.apiClient.get<VerificationRecordResponse>(
        `/api/public/verification-records/${verificationId}`
    )
    return response.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error('Verification Record API Error:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status,
          statusText: error.response?.statusText,
        })
      }
      throw error
    }
  }

  async getCandidateLegsCount(
    sport: string,
    week?: number,
    numLegs?: number,
    includePlayerProps?: boolean,
    requestMode?: 'TRIPLE' | string
  ): Promise<{
    candidate_legs_count: number
    unique_games?: number
    available: boolean
    top_exclusion_reasons?: string[]
    debug_id?: string
    strong_edges?: number
  }> {
    try {
      const params = new URLSearchParams({ sport })
      if (week != null) params.append('week', week.toString())
      if (numLegs != null) params.append('num_legs', numLegs.toString())
      if (includePlayerProps === true) params.append('include_player_props', 'true')
      if (requestMode === 'TRIPLE') params.append('request_mode', 'TRIPLE')
      const response = await this.clients.apiClient.get<{
        candidate_legs_count: number
        unique_games?: number
        available: boolean
        top_exclusion_reasons?: string[]
        debug_id?: string
        strong_edges?: number
      }>(`/api/parlay/candidate-legs-count?${params.toString()}`)
      return response.data
    } catch (error) {
      console.error('Error fetching candidate legs count:', error)
      return { candidate_legs_count: 0, available: false }
    }
  }
}


