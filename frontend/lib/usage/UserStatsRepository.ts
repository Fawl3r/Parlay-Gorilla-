import { api } from "@/lib/api"

export type UserStatsResponse = {
  ai_parlays: {
    lifetime: number
    last_30_days: number
    period_used: number
    period_limit: number
    period_remaining: number
    period_start?: string | null
    period_end?: string | null
  }
  usage_breakdown?: {
    weekly_activity?: {
      ai_parlays_this_week?: number
      most_active_day?: string | null
    }
    custom_ai_behavior?: {
      custom_ai_share_percent?: number
      verified_on_chain_this_period?: number
    }
  }
  custom_ai_parlays: {
    saved_lifetime: number
    saved_last_30_days: number
    period_used: number
    period_limit: number
    period_remaining: number
    period_start?: string | null
    period_end?: string | null
  }
  inscriptions: {
    consumed_lifetime: number
    period_used: number
    period_limit: number
    period_remaining: number
    inscription_cost_credits: number
    credits_spent_lifetime: number
    period_start?: string | null
    period_end?: string | null
  }
  verified_wins: {
    lifetime: number
    last_30_days: number
  }
  leaderboards: {
    verified_winners: { rank: number | null }
    ai_usage_30d: { rank: number | null }
    ai_usage_all_time: { rank: number | null }
  }
}

export class UserStatsRepository {
  async getMyStats(): Promise<UserStatsResponse> {
    const response = await api.get("/api/users/me/stats")
    return response.data as UserStatsResponse
  }
}


