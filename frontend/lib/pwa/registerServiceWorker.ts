/**
 * Registers the PWA service worker (push-sw.js). Production-only, secure context only.
 * Fail silently so PWA installability never breaks the app.
 */

let didRegister = false

function doRegister(): void {
  navigator.serviceWorker
    .register('/push-sw.js', { scope: '/' })
    .catch(() => {
      // Fail silently — PWA must never break app
    })
}

export function registerServiceWorker(): void {
  if (typeof window === 'undefined') {
    return
  }

  if (process.env.NODE_ENV !== 'production') {
    if (process.env.NODE_ENV === 'development') {
      console.debug('[PWA] SW registration skipped (not production)')
    }
    return
  }

  if (!('serviceWorker' in navigator)) {
    return
  }

  const isSecure =
    window.isSecureContext ||
    window.location.hostname === 'localhost' ||
    window.location.hostname === '127.0.0.1'
  if (!isSecure) {
    return
  }

  if (didRegister) {
    return
  }
  didRegister = true

  if (document.readyState === 'complete') {
    doRegister()
  } else {
    window.addEventListener('load', doRegister)
  }
}
