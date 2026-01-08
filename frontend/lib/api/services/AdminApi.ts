import { ApiHttpClients } from '@/lib/api/internal/ApiHttpClientsProvider'

export class AdminApi {
  constructor(private readonly clients: ApiHttpClients) {}

  async adminLogin(email: string, password: string) {
    const response = await this.clients.apiClient.post('/api/admin/auth/login', {
      email,
      password,
    })
    return response.data
  }
}




