#!/usr/bin/env tsx
/**
 * Voice Lint Check Script
 * Run manually to check for banned words in copy
 */

import { copy } from "../lib/content/copy"
import { lintCopy, logViolations } from "../lib/content/voiceLint"

console.log("🔍 Checking voice compliance...\n")

const result = lintCopy(copy)

if (result.passed) {
  console.log("✅ Voice check passed! No banned words found.\n")
  process.exit(0)
} else {
  logViolations(result)
  console.log(`\n❌ Voice check failed: ${result.violations.length} violation(s) found.\n`)
  process.exit(1)
}

