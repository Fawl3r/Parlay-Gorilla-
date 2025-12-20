/**
 * Cache utility functions for manual cache management
 * 
 * Use these functions to manually clear cache when needed:
 * - After user actions that change data
 * - When you want to force a refresh
 * - For debugging purposes
 */

import { cacheManager } from './cache'
import { clearAnalyticsCache } from './analytics-cache'

/**
 * Clear all cache
 */
export function clearAllCache(): void {
  cacheManager.clear()
  console.log('[CACHE] All cache cleared')
}

/**
 * Clear games cache
 */
export function clearGamesCache(): void {
  cacheManager.clearPattern(/^games:/)
  console.log('[CACHE] Games cache cleared')
}

/**
 * Clear parlay cache
 */
export function clearParlayCache(): void {
  cacheManager.clearPattern(/^(parlay|triple_parlay):/)
  console.log('[CACHE] Parlay cache cleared')
}

/**
 * Clear analysis cache
 */
export function clearAnalysisCache(): void {
  cacheManager.clearPattern(/^analysis/)
  console.log('[CACHE] Analysis cache cleared')
}

/**
 * Clear team photos cache
 */
export function clearTeamPhotosCache(): void {
  cacheManager.clearPattern(/^team_photo/)
  console.log('[CACHE] Team photos cache cleared')
}

/**
 * Clear user-specific cache (analytics, user data)
 */
export function clearUserCache(): void {
  cacheManager.clearUserCache()
  clearAnalyticsCache()
  console.log('[CACHE] User cache cleared')
}

/**
 * Get cache statistics (useful for debugging)
 */
export function getCacheStats() {
  return cacheManager.getStats()
}

