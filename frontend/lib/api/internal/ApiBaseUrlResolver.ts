export class ApiBaseUrlResolver {
  resolveAxiosBaseUrl(): string {
    // In the browser, always use same-origin so Next.js rewrites can proxy to backend.
    // This prevents CORS + "localhost on iPhone" issues.
    if (typeof window !== 'undefined') return ''
    return this.normalizeBaseUrl(this.resolveServerBackendBaseUrl())
  }

  resolveDebugBaseUrl(): string {
    if (typeof window !== 'undefined') return window.location.origin
    return this.normalizeBaseUrl(this.resolveServerBackendBaseUrl())
  }

  private resolveServerBackendBaseUrl(): string {
    return (
      process.env.PG_BACKEND_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      'http://localhost:8000'
    )
  }

  private normalizeBaseUrl(raw: string): string {
    const value = String(raw || '').trim()
    if (!value) return 'http://localhost:8000'
    if (value.includes('://')) return value
    // Render Blueprints commonly provide private-network values as hostport (e.g. my-backend:10000).
    return `http://${value}`
  }
}



