export type AuthTokenListener = (token: string | null) => void

class AuthTokenStorage {
  private readonly key = 'auth_token'

  getToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(this.key)
  }

  setToken(token: string | null) {
    if (typeof window === 'undefined') return
    if (token) {
      localStorage.setItem(this.key, token)
      return
    }
    localStorage.removeItem(this.key)
  }

  getAdminToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('admin_token')
  }
}

class AuthSessionManager {
  private readonly storage = new AuthTokenStorage()
  private readonly listeners = new Set<AuthTokenListener>()

  /**
   * Returns the token to use for Authorization headers.
   *
   * - On `/admin/*`, prefer `admin_token`.
   * - Else, use `auth_token`.
   */
  async getAccessToken(): Promise<string | null> {
    if (typeof window === 'undefined') return null
    const pathname = window.location.pathname || ''
    if (pathname.startsWith('/admin')) {
      return this.storage.getAdminToken() || this.storage.getToken()
    }
    return this.storage.getToken()
  }

  setAccessToken(token: string | null) {
    this.storage.setToken(token)
    this.notify()
  }

  clearAccessToken() {
    this.setAccessToken(null)
  }

  onTokenChange(listener: AuthTokenListener): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  private notify() {
    const token = this.storage.getToken()
    for (const listener of this.listeners) {
      listener(token)
    }
  }
}

export const authSessionManager = new AuthSessionManager()

