import axios from 'axios'
import { ApiHttpClients } from '@/lib/api/internal/ApiHttpClientsProvider'
import type {
  WebPushSubscribeRequest,
  WebPushSubscribeResponse,
  WebPushUnsubscribeResponse,
  WebPushVapidPublicKeyResponse,
} from '@/lib/api/types'

export class NotificationsApi {
  constructor(private readonly clients: ApiHttpClients) {}

  async getWebPushVapidPublicKey(): Promise<WebPushVapidPublicKeyResponse> {
    const response = await this.clients.gamesClient.get<WebPushVapidPublicKeyResponse>(
      '/api/notifications/push/vapid-public-key'
    )
    return response.data
  }

  async subscribeWebPush(payload: WebPushSubscribeRequest): Promise<WebPushSubscribeResponse> {
    try {
      const response = await this.clients.gamesClient.post<WebPushSubscribeResponse>(
        '/api/notifications/push/subscribe',
        payload
      )
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail =
          (error.response?.data as any)?.detail ||
          error.message ||
          'Failed to enable notifications'
        throw new Error(String(detail))
      }
      throw error
    }
  }

  async unsubscribeWebPush(endpoint: string): Promise<WebPushUnsubscribeResponse> {
    try {
      const response = await this.clients.gamesClient.post<WebPushUnsubscribeResponse>(
        '/api/notifications/push/unsubscribe',
        { endpoint }
      )
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail =
          (error.response?.data as any)?.detail ||
          error.message ||
          'Failed to disable notifications'
        throw new Error(String(detail))
      }
      throw error
    }
  }
}


