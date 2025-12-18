"use client"

import { useState, useEffect } from 'react'
import { X, ChevronUp, ChevronDown, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react'

interface DebugInfo {
  apiUrl: string
  origin: string
  userAgent: string
  hasAuthToken: boolean
  localStorageKeys: string[]
  errors: string[]
  networkStatus: 'checking' | 'online' | 'offline'
}

export function MobileDebugPanel() {
  const [isOpen, setIsOpen] = useState(false)
  const [debugInfo, setDebugInfo] = useState<DebugInfo | null>(null)
  const [testResult, setTestResult] = useState<{ status: 'idle' | 'testing' | 'success' | 'error', message: string }>({ status: 'idle', message: '' })

  const updateDebugInfo = async () => {
    if (typeof window === 'undefined') return

    const apiUrl = (window as any).__API_URL || window.location.origin
    const origin = window.location.origin
    const userAgent = navigator.userAgent
    
    // Check for auth token
    const hasAuthToken = Boolean(localStorage.getItem('auth_token'))

    // Get localStorage keys (filter sensitive data)
    const localStorageKeys = Object.keys(localStorage).filter(key => 
      !key.includes('password') && !key.includes('secret')
    )

    // Get recent errors from console (if available)
    const errors: string[] = []
    if ((window as any).__consoleErrors) {
      errors.push(...(window as any).__consoleErrors.slice(-5))
    }

    setDebugInfo({
      apiUrl,
      origin,
      userAgent,
      hasAuthToken,
      localStorageKeys,
      errors,
      networkStatus: navigator.onLine ? 'online' : 'offline'
    })
  }

  useEffect(() => {
    // Only show in development or when ?debug=true
    if (typeof window !== 'undefined') {
      const urlParams = new URLSearchParams(window.location.search)
      const showDebug = process.env.NODE_ENV === 'development' || urlParams.get('debug') === 'true'
      
      if (showDebug) {
        updateDebugInfo()
        const interval = setInterval(updateDebugInfo, 5000) // Update every 5 seconds
        return () => clearInterval(interval)
      }
    }
  }, [])

  const testBackendConnection = async () => {
    if (!debugInfo) return

    setTestResult({ status: 'testing', message: 'Testing backend connection...' })
    
    try {
      // First try a simple fetch with timeout
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 second timeout
      
      const response = await fetch(`${debugInfo.apiUrl}/health`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        signal: controller.signal,
        mode: 'cors'
      })
      
      clearTimeout(timeoutId)
      
      if (response.ok) {
        const data = await response.json()
        setTestResult({ 
          status: 'success', 
          message: `✓ Backend is reachable! Status: ${data.status || 'healthy'}` 
        })
      } else {
        setTestResult({ 
          status: 'error', 
          message: `✗ Backend returned error: ${response.status} ${response.statusText}. Check CORS configuration.` 
        })
      }
    } catch (error: any) {
      let errorMessage = 'Connection failed'
      
      if (error.name === 'AbortError') {
        errorMessage = 'Connection timeout (10s). Backend may be unreachable or firewall is blocking.'
      } else if (error.message?.includes('Failed to fetch')) {
        errorMessage = 'Network error: Cannot reach backend. Check:\n1. Backend is running\n2. Firewall allows port 8000\n3. Both devices on same network\n4. Correct IP address'
      } else if (error.message?.includes('CORS')) {
        errorMessage = 'CORS error: Backend is reachable but blocking requests. Check backend CORS configuration.'
      } else {
        errorMessage = `Connection failed: ${error.message || 'Unknown error'}`
      }
      
      setTestResult({ 
        status: 'error', 
        message: errorMessage
      })
    }
  }

  // Only show in development or with ?debug=true
  if (typeof window === 'undefined') return null
  
  const urlParams = new URLSearchParams(window.location.search)
  const showDebug = process.env.NODE_ENV === 'development' || urlParams.get('debug') === 'true'
  
  if (!showDebug || !debugInfo) return null

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-gray-900 text-white text-xs font-mono">
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full bg-gray-800 hover:bg-gray-700 px-4 py-2 flex items-center justify-between"
      >
        <span className="font-semibold">🐛 Debug Panel</span>
        <div className="flex items-center gap-2">
          {debugInfo.networkStatus === 'online' ? (
            <CheckCircle className="w-4 h-4 text-green-400" />
          ) : (
            <AlertCircle className="w-4 h-4 text-red-400" />
          )}
          {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
        </div>
      </button>

      {/* Debug Content */}
      {isOpen && (
        <div className="max-h-96 overflow-y-auto p-4 space-y-4 bg-gray-900 border-t border-gray-700">
          {/* API Info */}
          <div>
            <div className="font-semibold mb-2 text-yellow-400">API Configuration</div>
            <div className="space-y-1 pl-2">
              <div>API URL: <span className="text-green-400">{debugInfo.apiUrl}</span></div>
              <div>Origin: <span className="text-blue-400">{debugInfo.origin}</span></div>
              <div>Network: <span className={debugInfo.networkStatus === 'online' ? 'text-green-400' : 'text-red-400'}>{debugInfo.networkStatus}</span></div>
            </div>
          </div>

          {/* Auth Status */}
          <div>
            <div className="font-semibold mb-2 text-yellow-400">Authentication</div>
            <div className="pl-2">
              {debugInfo.hasAuthToken ? (
                <div className="text-green-400">✓ Session token found</div>
              ) : (
                <div className="text-red-400">✗ No session token</div>
              )}
            </div>
          </div>

          {/* Test Connection */}
          <div>
            <button
              onClick={testBackendConnection}
              disabled={testResult.status === 'testing'}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-3 py-1 rounded text-xs flex items-center gap-2"
            >
              {testResult.status === 'testing' ? (
                <>
                  <RefreshCw className="w-3 h-3 animate-spin" />
                  Testing...
                </>
              ) : (
                <>
                  <RefreshCw className="w-3 h-3" />
                  Test Backend Connection
                </>
              )}
            </button>
            {testResult.status !== 'idle' && (
              <div className={`mt-2 text-xs ${testResult.status === 'success' ? 'text-green-400' : 'text-red-400'}`}>
                {testResult.message}
              </div>
            )}
          </div>

          {/* LocalStorage Keys */}
          <div>
            <div className="font-semibold mb-2 text-yellow-400">LocalStorage ({debugInfo.localStorageKeys.length} keys)</div>
            <div className="pl-2 max-h-20 overflow-y-auto">
              {debugInfo.localStorageKeys.length > 0 ? (
                <div className="space-y-1">
                  {debugInfo.localStorageKeys.slice(0, 5).map(key => (
                    <div key={key} className="text-gray-300">• {key}</div>
                  ))}
                  {debugInfo.localStorageKeys.length > 5 && (
                    <div className="text-gray-500">... and {debugInfo.localStorageKeys.length - 5} more</div>
                  )}
                </div>
              ) : (
                <div className="text-gray-500">No localStorage keys</div>
              )}
            </div>
          </div>

          {/* Errors */}
          {debugInfo.errors.length > 0 && (
            <div>
              <div className="font-semibold mb-2 text-red-400">Recent Errors</div>
              <div className="pl-2 space-y-1 max-h-20 overflow-y-auto">
                {debugInfo.errors.map((error, i) => (
                  <div key={i} className="text-red-300 text-xs">{error}</div>
                ))}
              </div>
            </div>
          )}

          {/* User Agent (truncated) */}
          <div>
            <div className="font-semibold mb-2 text-yellow-400">Device Info</div>
            <div className="pl-2 text-gray-300 text-xs">
              {debugInfo.userAgent.substring(0, 80)}...
            </div>
          </div>

          {/* Instructions */}
          <div className="pt-2 border-t border-gray-700">
            <div className="text-gray-400 text-xs">
              💡 Add <code className="bg-gray-800 px-1 rounded">?debug=true</code> to URL to show in production
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

