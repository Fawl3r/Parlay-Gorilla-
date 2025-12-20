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

  async getCurrentUser() {
    const response = await this.clients.apiClient.get('/api/auth/me')
    return response.data
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
}




