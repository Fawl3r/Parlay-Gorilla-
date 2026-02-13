export class ApiBaseUrlResolver {
  private readonly prodFallbackBackendUrl = 'https://api.parlaygorilla.com'

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
    const defaultBackendUrl =
      process.env.NODE_ENV === 'production'
        ? this.prodFallbackBackendUrl
        : 'http://localhost:8000'

    const candidate =
      process.env.PG_BACKEND_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      process.env.BACKEND_URL ||
      defaultBackendUrl

    const raw = String(candidate || '').trim()
    const isProd = process.env.NODE_ENV === 'production'
    const looksLocal = /localhost|127\.0\.0\.1/.test(raw)
    const looksLikeFrontend = /https?:\/\/(www\.)?parlaygorilla\.com\b/.test(raw)
    if (isProd && (looksLocal || looksLikeFrontend)) return this.prodFallbackBackendUrl

    return candidate
  }

  private normalizeBaseUrl(raw: string): string {
    const value = String(raw || '').trim()
    if (!value) return 'http://localhost:8000'
    if (value.includes('://')) return value
    // Render Blueprints commonly provide private-network values as hostport (e.g. my-backend:10000).
    return `http://${value}`
  }
}



