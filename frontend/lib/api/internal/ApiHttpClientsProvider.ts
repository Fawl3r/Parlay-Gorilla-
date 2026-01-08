import axios, { AxiosInstance } from 'axios'
import { authSessionManager } from '@/lib/auth/session-manager'

export interface ApiHttpClients {
  apiClient: AxiosInstance
  gamesClient: AxiosInstance
}

export class ApiHttpClientsProvider {
  constructor(private readonly baseURL: string) {}

  create(): ApiHttpClients {
    const apiClient = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 180000, // 180 second timeout (3 minutes) for parlay generation
      withCredentials: true,
    })

    const gamesClient = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000, // 30 second timeout for games
      withCredentials: true,
    })

    this.addAuthInterceptor(apiClient)
    this.addAuthInterceptor(gamesClient)

    return { apiClient, gamesClient }
  }

  private addAuthInterceptor(client: AxiosInstance) {
    client.interceptors.request.use((cfg) => this.addAuthToken(cfg))
  }

  // Keep behavior aligned with previous implementation, but avoid any server-only crashes.
  private async addAuthToken(config: any) {
    // Only attach tokens in the browser.
    if (typeof window === 'undefined') return config

    // IMPORTANT:
    // We store an `admin_token` in localStorage for the admin panel.
    // That token must NOT be used on normal app pages.
    const pathname = window.location.pathname || ''
    const url = String(config?.url || '')
    const isAdminContext = pathname.startsWith('/admin') || url.startsWith('/api/admin')

    if (isAdminContext) {
      const adminToken = localStorage.getItem('admin_token')
      if (adminToken) {
        config.headers = config.headers || {}
        config.headers.Authorization = `Bearer ${adminToken}`
        return config
      }
    }

    try {
      const token = await authSessionManager.getAccessToken()
      if (token) {
        config.headers = config.headers || {}
        config.headers.Authorization = `Bearer ${token}`
      }
    } catch {
      // Non-fatal: request can proceed unauthenticated.
    }

    return config
  }
}




