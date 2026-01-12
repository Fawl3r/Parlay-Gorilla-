"use client"

import { createContext, useContext, useEffect, useState, ReactNode, useCallback, useRef } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { api } from './api'
import { cacheManager } from './cache'
import { clearAnalyticsCache } from './analytics-cache'
import { authSessionManager } from './auth/session-manager'

interface User {
  id: string
  email: string
  username?: string
  email_verified: boolean
  /**
   * Null means "unknown" (e.g., backend user fetch failed).
   * We only hard-redirect to profile setup when we *know* it's false.
   */
  profile_completed: boolean | null
}

interface AuthContextType {
  user: User | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<{ error: any }>
  signUp: (
    email: string,
    password: string,
    username?: string
  ) => Promise<{ error: any; requiresEmailVerification?: boolean }>
  signOut: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const PROFILE_SETUP_EXEMPT_PATHS = [
  '/profile/setup',
  '/auth',
  '/admin',
  '/',
  '/pricing',
  '/terms',
  '/privacy',
  '/support',
  '/report-bug',
  '/development-news',
  '/responsible-gaming',
  '/docs',
  '/tutorial',
]

const mapBackendUser = (backendUser: any): User => {
  return {
    id: String(backendUser?.id ?? ''),
    email: String(backendUser?.email ?? ''),
    username: backendUser?.username ?? undefined,
    email_verified: Boolean(backendUser?.email_verified),
    profile_completed:
      backendUser?.profile_completed === undefined || backendUser?.profile_completed === null
        ? null
        : Boolean(backendUser?.profile_completed),
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()
  const pathname = usePathname()
  const redirectingRef = useRef(false)
  const lastPathnameRef = useRef<string | null>(null)

  const refreshUser = useCallback(async () => {
    if (typeof window === 'undefined') return

    setLoading(true)

    let token: string | null = null
    try {
      token = await authSessionManager.getAccessToken()
      const backendUser = await api.getCurrentUser()
      setUser(mapBackendUser(backendUser))
    } catch (error: any) {
      // If token is invalid/expired, clear it.
      const status = error?.response?.status
      if (status === 401 || status === 403) {
        // Only clear local token if we had one. Cookie sessions should be cleared by server /logout.
        if (token) {
          authSessionManager.clearAccessToken()
          setUser(null)
        } else {
          setUser(null)
        }
        return
      }
      // Network errors (common on mobile/tunnels) should NOT force-log the user out.
      // Keep the existing `user` state (if any) and let the UI continue.
      console.warn('[Auth] refreshUser failed (keeping existing user):', error?.message || error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let isMounted = true

    refreshUser()

    const unsubscribe = authSessionManager.onTokenChange(() => {
      if (isMounted) {
        refreshUser()
      }
    })

    return () => {
      isMounted = false
      unsubscribe()
    }
  }, [refreshUser])

  useEffect(() => {
    // Don't redirect if loading, no user, or already redirecting
    if (loading || !user || redirectingRef.current) return

    // Check if we're already on an exempt path
    const isExempt = PROFILE_SETUP_EXEMPT_PATHS.some(
      (path) => pathname === path || pathname.startsWith(path + '/')
    )

    if (isExempt) {
      lastPathnameRef.current = pathname
      return
    }

    // Prevent redirect loops - don't redirect if we're already on the same path
    if (lastPathnameRef.current === pathname && pathname === '/profile/setup') {
      return
    }

    // Only redirect if profile is not completed and we're not already on setup page
    if (user.profile_completed === false && pathname !== '/profile/setup') {
      console.log('[Auth] Redirecting to profile setup - profile not completed')
      redirectingRef.current = true
      lastPathnameRef.current = '/profile/setup'
      router.push('/profile/setup')
      
      // Reset redirect flag after navigation
      setTimeout(() => {
        redirectingRef.current = false
      }, 100)
    } else {
      lastPathnameRef.current = pathname
    }
  }, [user, loading, pathname, router])

  const signIn = async (email: string, password: string) => {
    try {
      console.log('[Auth] Attempting sign in from:', typeof window !== 'undefined' ? window.location.origin : 'server')
      console.log('[Auth] API URL:', typeof window !== 'undefined' ? (window as any).__API_URL || 'unknown' : 'server')
      
      // Add timeout for mobile network issues
      const loginPromise = api.login(email, password)
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Network timeout - please check your connection and try again')), 30000)
      )

      const loginData = (await Promise.race([loginPromise, timeoutPromise])) as any
      const accessToken = loginData?.access_token as string | undefined

      if (!accessToken) {
        return { error: 'Login failed' }
      }

      authSessionManager.setAccessToken(accessToken)

      // Backend is the source of truth for profile completion status
      let backendUser: any | null = null
      try {
        backendUser = await api.getCurrentUser()
        setUser(mapBackendUser(backendUser))
      } catch (error) {
        console.warn('[Auth] Failed to fetch backend user on sign in:', error)
        // Fallback to the user payload returned by login.
        if (loginData?.user) {
          setUser(mapBackendUser(loginData.user))
        }
      }

      const profileCompleted =
        backendUser?.profile_completed === undefined || backendUser?.profile_completed === null
          ? null
          : Boolean(backendUser?.profile_completed)

      let redirectTo = sessionStorage.getItem('redirectAfterLogin') || '/app'
      sessionStorage.removeItem('redirectAfterLogin')

      // Use backend user data to determine redirect
      if (profileCompleted === false) {
        console.log('[Auth] Redirecting to profile setup on sign in')
        redirectTo = '/profile/setup'
      } else {
        console.log('[Auth] Profile completed, redirecting to:', redirectTo)
      }

      redirectingRef.current = true
      router.push(redirectTo)
      
      setTimeout(() => {
        redirectingRef.current = false
      }, 100)
      
      return { error: null }
    } catch (err: any) {
      // Better error messages for network issues
      const errorMessage = err.message || 'Login failed'
      if (errorMessage.includes('timeout') || errorMessage.includes('Network') || errorMessage.includes('fetch')) {
        return { error: 'Network error - please check your internet connection and try again' }
      }
      return { error: err?.response?.data?.detail || errorMessage }
    }
  }

  const signUp = async (email: string, password: string, username?: string) => {
    // #region agent log
    try {
      fetch('http://127.0.0.1:7242/ingest/abd8edf1-767f-4ebd-9040-91726939b7d4', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId: 'debug-session',
          runId: 'run1',
          hypothesisId: 'B',
          location: 'auth-context.tsx:224',
          message: 'signUp function entry',
          data: { email: email.substring(0, 10) + '...', hasUsername: !!username },
          timestamp: Date.now()
        })
      }).catch(() => {})
    } catch {}
    // #endregion
    try {
      // #region agent log
      try {
        fetch('http://127.0.0.1:7242/ingest/abd8edf1-767f-4ebd-9040-91726939b7d4', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sessionId: 'debug-session',
            runId: 'run1',
            hypothesisId: 'B',
            location: 'auth-context.tsx:226',
            message: 'Before api.register call',
            data: {},
            timestamp: Date.now()
          })
        }).catch(() => {})
      } catch {}
      // #endregion
      const data = await api.register(email, password, username)
      // #region agent log
      try {
        fetch('http://127.0.0.1:7242/ingest/abd8edf1-767f-4ebd-9040-91726939b7d4', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sessionId: 'debug-session',
            runId: 'run1',
            hypothesisId: 'B',
            location: 'auth-context.tsx:228',
            message: 'After api.register call',
            data: { hasToken: !!data?.access_token, hasUser: !!data?.user },
            timestamp: Date.now()
          })
        }).catch(() => {})
      } catch {}
      // #endregion
      const accessToken = data?.access_token as string | undefined
      if (accessToken) {
        authSessionManager.setAccessToken(accessToken)
      }

      // Set user from backend immediately (best-effort).
      try {
        const backendUser = await api.getCurrentUser()
        setUser(mapBackendUser(backendUser))
      } catch {
        if (data?.user) {
          setUser(mapBackendUser(data.user))
        }
      }

      // #region agent log
      try {
        fetch('http://127.0.0.1:7242/ingest/abd8edf1-767f-4ebd-9040-91726939b7d4', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sessionId: 'debug-session',
            runId: 'run1',
            hypothesisId: 'B',
            location: 'auth-context.tsx:242',
            message: 'signUp success',
            data: { requiresVerification: data?.user ? !Boolean(data.user.email_verified) : true },
            timestamp: Date.now()
          })
        }).catch(() => {})
      } catch {}
      // #endregion
      return {
        error: null,
        requiresEmailVerification: data?.user ? !Boolean(data.user.email_verified) : true,
      }
    } catch (err: any) {
      // #region agent log
      try {
        fetch('http://127.0.0.1:7242/ingest/abd8edf1-767f-4ebd-9040-91726939b7d4', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sessionId: 'debug-session',
            runId: 'run1',
            hypothesisId: 'B',
            location: 'auth-context.tsx:247',
            message: 'signUp error',
            data: { error: err?.response?.data?.detail || err.message, status: err?.response?.status },
            timestamp: Date.now()
          })
        }).catch(() => {})
      } catch {}
      // #endregion
      return { error: err?.response?.data?.detail || err.message || 'Registration failed' }
    }
  }

  const signOut = async () => {
    cacheManager.clearUserCache()
    clearAnalyticsCache()
    authSessionManager.clearAccessToken()
    setUser(null)

    // Best-effort: clear HttpOnly cookie session (hybrid auth).
    try {
      await api.logout()
    } catch {
      // Non-fatal.
    }

    const isAdmin = typeof window !== 'undefined' && window.location.pathname.startsWith('/admin')
    router.push(isAdmin ? '/admin/login' : '/auth/login')
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        signIn,
        signUp,
        signOut,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
