# Caching Implementation Summary

## Overview

A comprehensive client-side caching system has been implemented to reduce API requests and help with rate limiting. The caching system covers all major API endpoints with appropriate TTLs (Time To Live) based on data volatility.

## What Was Implemented

### 1. Core Cache Manager (`frontend/lib/cache.ts`)

- **CacheManager Class**: A robust in-memory cache with TTL support
- **Features**:
  - Automatic expiration based on TTL
  - LRU-style eviction when cache is full (max 100 entries)
  - Pattern-based cache clearing
  - Cache statistics for debugging

### 2. API Client Caching (`frontend/lib/api.ts`)

All API methods now use caching with appropriate TTLs:

| Endpoint | Cache TTL | Reason |
|----------|----------|--------|
| `getGames()` | 1 minute | Games update frequently but can be cached briefly |
| `getNFLWeeks()` | 1 hour | Changes infrequently (only when season progresses) |
| `listSports()` | 24 hours | Very static data |
| `suggestParlay()` | 5 minutes | Expensive to generate, cache for a bit |
| `suggestTripleParlay()` | 5 minutes | Expensive to generate, cache for a bit |
| `getAnalysis()` | 10 minutes | Already has Next.js revalidate, client cache helps |
| `listUpcomingAnalyses()` | 2 minutes | Updates periodically |
| `getTeamPhoto()` / `getTeamPhotos()` | 1 hour | Static data, can cache longer |
| `healthCheck()` | 10 seconds | Very short cache for health checks |

### 3. Analytics Caching (`frontend/lib/analytics-cache.ts`)

- **User-specific caching**: Analytics data is cached per user (based on token)
- **TTL**: 30 seconds (user-specific data changes frequently)
- **Automatic cache clearing**: Cleared on logout

### 4. Cache Utilities (`frontend/lib/cache-utils.ts`)

Helper functions for manual cache management:
- `clearAllCache()` - Clear everything
- `clearGamesCache()` - Clear games cache
- `clearParlayCache()` - Clear parlay cache
- `clearAnalysisCache()` - Clear analysis cache
- `clearTeamPhotosCache()` - Clear team photos cache
- `clearUserCache()` - Clear user-specific cache
- `getCacheStats()` - Get cache statistics

## How It Works

### Cache Flow

1. **Request Made**: Component calls API method
2. **Cache Check**: API method checks cache first
3. **Cache Hit**: If found and not expired, return cached data immediately
4. **Cache Miss**: If not found or expired, make API request
5. **Cache Store**: Store response in cache with appropriate TTL
6. **Return Data**: Return data to component

### Cache Keys

Cache keys are generated from request parameters:
- Games: `games:{sport}:{week}`
- Parlays: `parlay:{num_legs}:{risk_profile}:{sports}:{mix}:{week}`
- Analytics: `analytics:{userId}:{endpoint}:{queryParams}`

### Cache Invalidation

- **Automatic**: Entries expire based on TTL
- **On Logout**: User-specific cache is cleared
- **Manual**: Use utility functions to clear specific cache types

## Benefits

1. **Reduced API Calls**: Repeated requests within TTL return cached data
2. **Rate Limiting Protection**: Fewer requests = less chance of hitting rate limits
3. **Faster Response Times**: Cached responses are instant
4. **Better UX**: Users see data immediately on navigation
5. **Cost Savings**: Fewer API calls = lower costs for external APIs

## Backend Caching

The backend already had some caching:
- **Games API**: 10-minute in-memory cache
- **Parlay Cache**: Database-backed cache with `CacheManager` class
- **Team Photos**: Backend caching (7 days mentioned in comments)

The frontend caching complements the backend caching and provides an additional layer of protection.

## Usage Examples

### Automatic (Already Implemented)

All API calls automatically use caching - no code changes needed in components.

### Manual Cache Clearing

```typescript
import { clearParlayCache, clearGamesCache } from '@/lib/cache-utils'

// Clear parlay cache after user generates a new parlay
clearParlayCache()

// Clear games cache when user changes sport
clearGamesCache()
```

### Check Cache Statistics

```typescript
import { getCacheStats } from '@/lib/cache-utils'

const stats = getCacheStats()
console.log('Cache stats:', stats)
// { total: 15, valid: 12, expired: 3, maxSize: 100 }
```

## Testing

To verify caching is working:

1. **Open Browser DevTools Console**
2. **Make an API request** - You'll see `[CACHE MISS]` log
3. **Make the same request again** - You'll see `[CACHE HIT]` log
4. **Wait for TTL to expire** - Next request will be `[CACHE MISS]` again

## Configuration

Cache TTLs can be adjusted in `frontend/lib/cache.ts`:

```typescript
export const CACHE_TTL = {
  GAMES: 60 * 1000,        // 1 minute
  NFL_WEEKS: 60 * 60 * 1000, // 1 hour
  PARLAY: 5 * 60 * 1000,   // 5 minutes
  // ... etc
}
```

## Future Enhancements

Potential improvements:
1. **Persistent Cache**: Store cache in localStorage for persistence across page reloads
2. **Cache Warming**: Pre-fetch common data on app load
3. **Cache Analytics**: Track cache hit rates
4. **Adaptive TTLs**: Adjust TTLs based on data freshness from API
5. **Service Worker Cache**: Use service workers for offline support

## Files Modified/Created

### Created
- `frontend/lib/cache.ts` - Core cache manager
- `frontend/lib/analytics-cache.ts` - Analytics-specific caching
- `frontend/lib/cache-utils.ts` - Utility functions

### Modified
- `frontend/lib/api.ts` - Added caching to all API methods
- `frontend/lib/auth-context.tsx` - Clear cache on logout
- `frontend/app/analytics/page.tsx` - Use cached authenticated fetch

## Notes

- Cache is in-memory only (cleared on page refresh)
- Maximum 100 cache entries (oldest evicted when full)
- Cache keys include all relevant parameters to avoid collisions
- User-specific data (analytics) is cached per user token
- All cache operations are logged to console for debugging

