import { ApiHttpClients } from '@/lib/api/internal/ApiHttpClientsProvider'

export class ProfileApi {
  constructor(private readonly clients: ApiHttpClients) {}

  async getMyProfile() {
    const response = await this.clients.apiClient.get('/api/profile/me')
    return response.data
  }

  async updateProfile(data: {
    display_name?: string
    avatar_url?: string
    bio?: string
    timezone?: string
    default_risk_profile?: 'conservative' | 'balanced' | 'degen'
    favorite_teams?: string[]
    favorite_sports?: string[]
  }) {
    const response = await this.clients.apiClient.put('/api/profile/me', data)
    return response.data
  }

  async completeProfileSetup(data: {
    display_name: string
    avatar_url?: string
    bio?: string
    timezone?: string
    default_risk_profile?: 'conservative' | 'balanced' | 'degen'
    favorite_teams?: string[]
    favorite_sports?: string[]
  }) {
    const response = await this.clients.apiClient.post('/api/profile/setup', data)
    return response.data
  }

  async getMyBadges() {
    const response = await this.clients.apiClient.get('/api/profile/badges')
    return response.data
  }
}




