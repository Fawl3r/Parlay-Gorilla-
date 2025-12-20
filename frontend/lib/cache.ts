/**
 * Client-side cache manager for API responses
 * 
 * Provides configurable TTL-based caching to reduce API calls and help with rate limiting.
 * Different endpoints have different cache durations based on data volatility.
 */

export interface CacheEntry<T> {
  data: T
  timestamp: number
  ttl: number
}

export class CacheManager {
  private cache: Map<string, CacheEntry<unknown>> = new Map()
  private maxSize: number = 100 // Maximum number of cache entries

  /**
   * Get cached data if available and not expired
   */
  get<T>(key: string): T | null {
    const entry = this.cache.get(key) as CacheEntry<T> | undefined
    
    if (!entry) {
      return null
    }

    const age = Date.now() - entry.timestamp
    
    if (age > entry.ttl) {
      // Expired, remove from cache
      this.cache.delete(key)
      return null
    }

    return entry.data
  }

  /**
   * Set cache entry with TTL
   */
  set<T>(key: string, data: T, ttl: number): void {
    // Evict oldest entries if cache is full
    if (this.cache.size >= this.maxSize) {
      this.evictOldest()
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    })
  }

  /**
   * Check if key exists and is valid (not expired)
   */
  has(key: string): boolean {
    return this.get(key) !== null
  }

  /**
   * Remove specific cache entry
   */
  delete(key: string): void {
    this.cache.delete(key)
  }

  /**
   * Clear all cache entries
   */
  clear(): void {
    this.cache.clear()
  }

  /**
   * Clear cache entries matching a pattern
   */
  clearPattern(pattern: string | RegExp): void {
    const regex = typeof pattern === 'string' ? new RegExp(pattern) : pattern
    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        this.cache.delete(key)
      }
    }
  }

  /**
   * Clear user-specific cache entries (e.g., analytics, user data)
   * Call this when user logs out or changes
   */
  clearUserCache(): void {
    this.clearPattern(/^(analytics|user_|my_)/)
  }

  /**
   * Evict oldest cache entries (FIFO)
   */
  private evictOldest(): void {
    if (this.cache.size === 0) return

    // Find oldest entry
    let oldestKey: string | null = null
    let oldestTime = Infinity

    for (const [key, entry] of this.cache.entries()) {
      if (entry.timestamp < oldestTime) {
        oldestTime = entry.timestamp
        oldestKey = key
      }
    }

    if (oldestKey) {
      this.cache.delete(oldestKey)
    }
  }

  /**
   * Get cache statistics
   */
  getStats() {
    const now = Date.now()
    let valid = 0
    let expired = 0

    for (const entry of this.cache.values()) {
      const age = now - entry.timestamp
      if (age <= entry.ttl) {
        valid++
      } else {
        expired++
      }
    }

    return {
      total: this.cache.size,
      valid,
      expired,
      maxSize: this.maxSize,
    }
  }
}

// Singleton instance
export const cacheManager = new CacheManager()

// Cache TTL constants (in milliseconds)
export const CACHE_TTL = {
  // Games data - updates frequently but can be cached briefly
  GAMES: 60 * 1000, // 1 minute
  
  // NFL weeks - changes infrequently (only when season progresses)
  NFL_WEEKS: 60 * 60 * 1000, // 1 hour
  
  // Parlay suggestions - expensive to generate, cache for a bit
  PARLAY: 5 * 60 * 1000, // 5 minutes
  TRIPLE_PARLAY: 5 * 60 * 1000, // 5 minutes
  
  // Analytics - user-specific, changes frequently
  ANALYTICS: 30 * 1000, // 30 seconds
  
  // Analysis lists - updates periodically
  ANALYSIS_LIST: 2 * 60 * 1000, // 2 minutes
  
  // Analysis details - already has Next.js revalidate, but client cache helps
  ANALYSIS_DETAIL: 48 * 60 * 60 * 1000, // 48 hours
  
  // Team photos - static data, can cache longer
  TEAM_PHOTOS: 60 * 60 * 1000, // 1 hour
  
  // Sports list - very static
  SPORTS_LIST: 60 * 60 * 1000, // 1 hour (season status can change)
  
  // Health check - very short cache
  HEALTH_CHECK: 10 * 1000, // 10 seconds
} as const

/**
 * Generate cache key from parts
 */
export function cacheKey(...parts: (string | number | null | undefined)[]): string {
  return parts
    .filter((part) => part !== null && part !== undefined)
    .map((part) => String(part))
    .join(':')
}

