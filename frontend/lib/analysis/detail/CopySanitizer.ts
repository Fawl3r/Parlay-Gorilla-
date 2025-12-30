export class CopySanitizer {
  static sanitizeMainCopy(input: string): string {
    const raw = String(input || "")
    if (!raw.trim()) return ""

    // Keep this list small and deterministic. This is NOT an AI rewrite, just a guardrail.
    const replacements: Array<[RegExp, string]> = [
      [/model confidence/gi, "how sure the AI is"],
      [/expected value\s*\(ev\)/gi, "long-term value"],
      [/\bev\b/gi, "long-term value"],
      [/variance/gi, "risk"],
      [/advanced metrics/gi, "deeper stats"],
      [/model projection/gi, "score outlook"],
      [/weighted model/gi, "AI approach"],
    ]

    let out = raw
    for (const [pattern, value] of replacements) {
      out = out.replace(pattern, value)
    }

    // Don’t mention algorithms or data sources in user-facing copy.
    out = out.replace(/\b(algo|algorithm|dataset|data source|training data)\b/gi, "data")

    return out.trim()
  }

  static stripPercentages(input: string): string {
    const raw = String(input || "")
    if (!raw.trim()) return ""
    return raw.replace(/\b\d+(?:\.\d+)?%/g, "").replace(/\s{2,}/g, " ").trim()
  }

  static toSingleSentence(input: string, maxChars: number): string {
    const raw = String(input || "").trim()
    if (!raw) return ""

    const first = raw.split(/(?<=[.!?])\s+/)[0] ?? raw
    const clipped = first.length > maxChars ? `${first.slice(0, maxChars).trim()}…` : first
    return clipped
  }
}


