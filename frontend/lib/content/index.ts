/**
 * Content System Exports
 * Helper functions for accessing copy
 */

import { copy } from "./copy"

/**
 * Get copy value by path (dot-notation)
 * Example: getCopy('site.home.hero.headline')
 */
export function getCopy(path: string): string {
  const keys = path.split(".")
  let value: any = copy

  for (const key of keys) {
    if (value === null || value === undefined) {
      console.warn(`Copy path not found: ${path}`)
      return path
    }
    value = value[key]
  }

  if (typeof value !== "string") {
    console.warn(`Copy path "${path}" is not a string:`, value)
    return path
  }

  return value
}

/**
 * Get nested copy object by path
 * Example: getCopyObject('site.home.hero')
 */
export function getCopyObject(path: string): any {
  const keys = path.split(".")
  let value: any = copy

  for (const key of keys) {
    if (value === null || value === undefined) {
      console.warn(`Copy path not found: ${path}`)
      return {}
    }
    value = value[key]
  }

  return value || {}
}

/**
 * Export copy object directly for cases where you need the full structure
 */
export { copy }

/**
 * Type-safe copy accessor
 */
export type CopyPath = keyof typeof copy | `${keyof typeof copy}.${string}`

