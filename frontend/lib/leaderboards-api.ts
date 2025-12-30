import { api } from "@/lib/api"

export type VerifiedWinnersEntry = {
  rank: number
  username: string
  verified_wins: number
  win_rate: number
  last_win_at?: string | null
  inscription_id?: string | null
}

export type VerifiedWinnersResponse = {
  leaderboard: VerifiedWinnersEntry[]
}

export type AiPowerUsersEntry = {
  rank: number
  username: string
  ai_parlays_generated: number
  last_generated_at?: string | null
}

export type AiPowerUsersResponse = {
  timeframe: "30d" | "all_time" | string
  leaderboard: AiPowerUsersEntry[]
}

export class LeaderboardsApi {
  async getVerifiedWinners(limit: number = 20): Promise<VerifiedWinnersResponse> {
    const res = await api.get(`/api/leaderboards/custom?limit=${limit}`)
    return res.data as VerifiedWinnersResponse
  }

  async getAiUsage(params: { period?: "30d" | "all_time"; limit?: number } = {}): Promise<AiPowerUsersResponse> {
    const period = params.period ?? "30d"
    const limit = params.limit ?? 20
    const res = await api.get(`/api/leaderboards/ai-usage?period=${period}&limit=${limit}`)
    return res.data as AiPowerUsersResponse
  }
}

export const leaderboardsApi = new LeaderboardsApi()


