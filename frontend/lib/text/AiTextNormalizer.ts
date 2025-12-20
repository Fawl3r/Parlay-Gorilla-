export class AiTextNormalizer {
  /**
   * Some stored AI fields contain *literal* escape sequences (e.g. "\\n\\n")
   * instead of real newlines. This normalizes them for display.
   */
  static normalizeEscapedNewlines(input: string): string {
    if (!input) return ""

    // Order matters: normalize CRLF first, then LF.
    return input
      .replace(/\\r\\n/g, "\n")
      .replace(/\\n/g, "\n")
      .replace(/\\t/g, "\t")
  }
}





