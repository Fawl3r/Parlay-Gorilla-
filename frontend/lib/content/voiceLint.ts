/**
 * Voice Lint Utility
 * Checks for banned words that don't match the brand voice
 */

export const BANNED_WORDS = [
  "guaranteed",
  "lock",
  "risk-free",
  "AI-powered",
  "leverage",
  "optimize",
  "data-driven",
  "sure thing",
  "life-changing",
  "bet smarter", // Overused, use sparingly
]

export interface VoiceLintResult {
  violations: Array<{
    path: string
    value: string
    bannedWord: string
  }>
  passed: boolean
}

/**
 * Recursively check an object for banned words
 */
export function lintObject(obj: any, path = ""): VoiceLintResult["violations"] {
  const violations: VoiceLintResult["violations"] = []

  if (typeof obj === "string") {
    const lowerText = obj.toLowerCase()
    for (const banned of BANNED_WORDS) {
      const b = banned.toLowerCase()
      // Match whole-word only for "lock" so "unlock" is allowed
      const isMatch =
        b === "lock"
          ? /\block\b/.test(lowerText)
          : lowerText.includes(b)
      if (isMatch) {
        violations.push({
          path,
          value: obj,
          bannedWord: banned,
        })
      }
    }
  } else if (Array.isArray(obj)) {
    obj.forEach((item, index) => {
      violations.push(...lintObject(item, `${path}[${index}]`))
    })
  } else if (obj !== null && typeof obj === "object") {
    Object.keys(obj).forEach((key) => {
      const newPath = path ? `${path}.${key}` : key
      violations.push(...lintObject(obj[key], newPath))
    })
  }

  return violations
}

/**
 * Lint a copy object and return results
 */
export function lintCopy(copy: any): VoiceLintResult {
  const violations = lintObject(copy)
  return {
    violations,
    passed: violations.length === 0,
  }
}

/**
 * Log violations to console (dev mode only)
 */
export function logViolations(result: VoiceLintResult) {
  if (result.passed) {
    return
  }

  console.warn(`🚨 Voice Lint: Found ${result.violations.length} violation(s)`)
  result.violations.forEach((violation) => {
    console.warn(
      `  - ${violation.path}: Contains banned word "${violation.bannedWord}"\n    Text: "${violation.value}"`
    )
  })
}

/**
 * Check copy in dev mode
 */
export function checkVoice(copy: any, log = true): boolean {
  if (typeof window === "undefined" || process.env.NODE_ENV !== "development") {
    return true // Skip in production
  }

  const result = lintCopy(copy)
  if (log) {
    logViolations(result)
  }
  return result.passed
}

