/**
 * Caching utilities for analytics endpoints
 * Analytics data is user-specific and should be cached with shorter TTLs
 */

import { cacheManager, CACHE_TTL, cacheKey } from './cache'

/**
 * Get user ID from auth token (simple hash for cache key)
 */
function getUserIdFromToken(): string | null {
  if (typeof window === 'undefined') return null
  
  // Try to get user ID from token or localStorage
  const token = localStorage.getItem('auth_token')
  if (!token) return null
  
  // Simple hash of token for cache key (first 8 chars)
  return token.substring(0, 8)
}

/**
 * Cached authenticated fetch for analytics endpoints
 * Returns the Response object for compatibility with existing code
 */
export async function cachedAuthenticatedFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = localStorage.getItem('auth_token')

  if (!token) {
    throw new Error('Authentication required')
  }

  // Generate cache key from URL and user ID
  const userId = getUserIdFromToken()
  const urlKey = url.split('?')[0] // Remove query params for key
  const queryParams = new URLSearchParams(url.split('?')[1] || '')
  const cacheKeyStr = cacheKey('analytics', userId, urlKey, queryParams.toString())

  // Check cache first
  const cached = cacheManager.get<unknown>(cacheKeyStr)
  if (cached !== null && cached !== undefined) {
    console.log('[CACHE HIT] Analytics:', urlKey)
    // Return cached data as a Response object
    return new Response(JSON.stringify(cached), {
      status: 200,
      statusText: 'OK',
      headers: { 'Content-Type': 'application/json' },
    })
  }

  console.log('[CACHE MISS] Fetching analytics:', urlKey)

  // Make the actual request
  const headers = new Headers(options.headers)
  headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(url, {
    ...options,
    headers,
  })

  // Only cache successful responses
  if (response.ok) {
    try {
      // Clone response to read it without consuming
      const clonedResponse = response.clone()
      const data = await clonedResponse.json()
      cacheManager.set(cacheKeyStr, data, CACHE_TTL.ANALYTICS)
    } catch {
      // If response is not JSON, don't cache
    }
  }

  return response
}

/**
 * Clear analytics cache (call when user logs out or data changes)
 */
export function clearAnalyticsCache(): void {
  cacheManager.clearPattern(/^analytics:/)
}

