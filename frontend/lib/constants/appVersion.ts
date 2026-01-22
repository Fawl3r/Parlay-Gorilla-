/**
 * App Version Constants
 * Single source of truth for application version information
 */

export const APP_VERSION = "1.0a"
export const APP_BUILD = "FREE"
export const ENGINE_NAME = "Parlay Gorilla Engine"

/**
 * Get formatted version string for display
 */
export function getVersionString(): string {
  return `App Version ${APP_VERSION}`
}

/**
 * Get formatted engine version string for display
 */
export function getEngineVersionString(): string {
  return `Engine v${APP_VERSION}`
}
