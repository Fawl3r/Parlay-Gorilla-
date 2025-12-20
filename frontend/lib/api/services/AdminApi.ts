import { ApiHttpClients } from '@/lib/api/internal/ApiHttpClientsProvider'

export class AdminApi {
  constructor(private readonly clients: ApiHttpClients) {}

  async adminWalletLogin(walletAddress: string, message: string) {
    const response = await this.clients.apiClient.post('/api/admin/auth/wallet-login', {
      wallet_address: walletAddress,
      message,
    })
    return response.data
  }
}




