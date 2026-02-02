import { ApiHttpClients } from '@/lib/api/internal/ApiHttpClientsProvider'

export interface AiPicksHealthResponse {
  window_days: number
  totals: {
    app_opened: number
    ai_picks_generate_attempt: number
    ai_picks_generate_success: number
    ai_picks_generate_fail: number
  }
  success_rate: number
  beginner: { success: number; fail: number; success_rate: number }
  standard: { success: number; fail: number; success_rate: number }
  fail_reasons_top: Array<{ reason: string; count: number }>
  quick_actions: Array<{ action_id: string; clicked: number }>
  graduation: {
    nudge_shown: number
    nudge_clicked_profile: number
    nudge_clicked_dismiss: number
    ctr: number
  }
  premium: {
    upsell_shown: number
    upgrade_clicked: number
    ctr: number
  }
}

export class InternalMetricsApi {
  constructor(private readonly clients: ApiHttpClients) {}

  async getAiPicksHealth(days: number = 7): Promise<AiPicksHealthResponse> {
    const response = await this.clients.apiClient.get<AiPicksHealthResponse>(
      '/api/internal/ai-picks-health',
      { params: { days } }
    )
    return response.data
  }
}
