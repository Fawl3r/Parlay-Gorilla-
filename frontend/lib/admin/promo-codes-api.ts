import { api } from '@/lib/api'

export type PromoRewardType = 'premium_month' | 'credits_3'

export interface PromoCode {
  id: string
  code: string
  reward_type: PromoRewardType
  expires_at: string
  max_uses_total: number
  redeemed_count: number
  is_active: boolean
  deactivated_at?: string | null
  created_at: string
}

export interface PromoCodeListResponse {
  codes: PromoCode[]
  total: number
  page: number
  page_size: number
}

export interface PromoCodeCreateRequest {
  reward_type: PromoRewardType
  expires_at: string
  max_uses_total?: number
  code?: string
  notes?: string
}

export interface PromoCodeBulkCreateRequest {
  count: number
  reward_type: PromoRewardType
  expires_at: string
  max_uses_total?: number
  notes?: string
}

export const promoCodesAdminApi = {
  async list(params: {
    page?: number
    page_size?: number
    search?: string
    reward_type?: PromoRewardType
    is_active?: boolean
  }): Promise<PromoCodeListResponse> {
    const query = new URLSearchParams()
    if (params.page) query.append('page', String(params.page))
    if (params.page_size) query.append('page_size', String(params.page_size))
    if (params.search) query.append('search', params.search)
    if (params.reward_type) query.append('reward_type', params.reward_type)
    if (params.is_active !== undefined) query.append('is_active', String(params.is_active))
    const suffix = query.toString() ? `?${query.toString()}` : ''
    const { data } = await api.get(`/api/admin/promo-codes${suffix}`)
    return data
  },

  async create(payload: PromoCodeCreateRequest): Promise<PromoCode> {
    const { data } = await api.post('/api/admin/promo-codes', {
      reward_type: payload.reward_type,
      expires_at: payload.expires_at,
      max_uses_total: payload.max_uses_total ?? 1,
      code: payload.code,
      notes: payload.notes,
    })
    return data
  },

  async bulkCreate(payload: PromoCodeBulkCreateRequest): Promise<PromoCode[]> {
    const { data } = await api.post('/api/admin/promo-codes/bulk', {
      count: payload.count,
      reward_type: payload.reward_type,
      expires_at: payload.expires_at,
      max_uses_total: payload.max_uses_total ?? 1,
      notes: payload.notes,
    })
    return data
  },

  async deactivate(promoCodeId: string): Promise<PromoCode> {
    const { data } = await api.post(`/api/admin/promo-codes/${promoCodeId}/deactivate`)
    return data
  },
}


