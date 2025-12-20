import { api } from './api'

export interface SharedParlaySummary {
  id: string
  num_legs: number
  risk_profile: string
  parlay_hit_prob: number
  legs: any[]
  ai_summary?: string
  ai_risk_notes?: string
  created_at?: string | null
}

export interface SharedParlayUser {
  id?: string
  display_name: string
}

export interface SharedParlaySharedMeta {
  comment?: string | null
  views_count: number
  likes_count: number
  is_liked?: boolean
  shared_at?: string | null
}

export interface SharedParlayDetail {
  parlay: SharedParlaySummary
  shared: SharedParlaySharedMeta
  user: SharedParlayUser
}

export interface SharedParlayFeedItem {
  share_token: string
  comment?: string | null
  created_at?: string | null
  views_count: number
  likes_count: number
  is_liked?: boolean
  parlay: SharedParlaySummary
  user: SharedParlayUser
}

export interface LeaderboardEntry {
  user_id: string
  display_name: string
  total_parlays: number
  high_prob_parlays: number
}

class SocialApi {
  async shareParlay(parlayId: string, comment?: string, isPublic: 'public' | 'unlisted' | 'private' = 'public') {
    const response = await api.post('/api/social/share', {
      parlay_id: parlayId,
      comment,
      is_public: isPublic,
    })
    return response.data as { share_token: string; share_url: string; shared_at: string }
  }

  async getSharedParlay(shareToken: string): Promise<SharedParlayDetail> {
    const response = await api.get(`/api/social/share/${shareToken}`)
    return response.data as SharedParlayDetail
  }

  async toggleLike(shareToken: string) {
    const response = await api.post(`/api/social/share/${shareToken}/like`)
    return response.data as { liked: boolean; likes_count: number }
  }

  async getFeed(limit: number = 20): Promise<SharedParlayFeedItem[]> {
    const response = await api.get('/api/social/feed', { params: { limit } })
    return (response.data?.items || []) as SharedParlayFeedItem[]
  }

  async getLeaderboard(limit: number = 20): Promise<LeaderboardEntry[]> {
    const response = await api.get('/api/social/leaderboard', { params: { limit } })
    return (response.data?.leaderboard || []) as LeaderboardEntry[]
  }
}

export const socialApi = new SocialApi()

