import { ApiHttpClients } from '@/lib/api/internal/ApiHttpClientsProvider'

export class AuthApi {
  constructor(private readonly clients: ApiHttpClients) {}

  async login(email: string, password: string) {
    const response = await this.clients.apiClient.post('/api/auth/login', { email, password })
    return response.data
  }

  async register(email: string, password: string, username?: string) {
    const response = await this.clients.apiClient.post('/api/auth/register', { email, password, username })
    return response.data
  }

  /** Returns current user or null when not authenticated (401/403). Avoids throwing so auth context can set user to null without catch. */
  async getCurrentUser() {
    try {
      const response = await this.clients.apiClient.get('/api/auth/me')
      return response.data
    } catch (e: unknown) {
      const status = (e as { response?: { status?: number } })?.response?.status
      if (status === 401 || status === 403) return null
      throw e
    }
  }

  async verifyEmail(token: string) {
    const response = await this.clients.apiClient.post('/api/auth/verify-email', { token })
    return response.data
  }

  async resendVerificationEmail() {
    const response = await this.clients.apiClient.post('/api/auth/resend-verification')
    return response.data
  }

  async forgotPassword(email: string) {
    const response = await this.clients.apiClient.post('/api/auth/forgot-password', { email })
    return response.data
  }

  async resetPassword(token: string, password: string) {
    const response = await this.clients.apiClient.post('/api/auth/reset-password', { token, password })
    return response.data
  }

  async logout() {
    const response = await this.clients.apiClient.post('/api/auth/logout')
    return response.data
  }
}




