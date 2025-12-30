export type SavedAnalysisItem = {
  slug: string
  savedAtIso: string
}

const STORAGE_KEY = "pg_saved_analyses_v1"

export class SavedAnalysesManager {
  static list(): SavedAnalysisItem[] {
    if (typeof window === "undefined") return []
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY)
      const parsed = raw ? JSON.parse(raw) : []
      if (!Array.isArray(parsed)) return []
      return parsed
        .map((x) => ({ slug: String((x as any)?.slug || ""), savedAtIso: String((x as any)?.savedAtIso || "") }))
        .filter((x) => x.slug)
    } catch {
      return []
    }
  }

  static isSaved(slug: string): boolean {
    const s = String(slug || "").trim()
    if (!s) return false
    return this.list().some((x) => x.slug === s)
  }

  static toggle(slug: string): boolean {
    if (typeof window === "undefined") return false
    const s = String(slug || "").trim()
    if (!s) return false

    const items = this.list()
    const exists = items.some((x) => x.slug === s)

    const next = exists
      ? items.filter((x) => x.slug !== s)
      : [{ slug: s, savedAtIso: new Date().toISOString() }, ...items].slice(0, 200)

    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    } catch {
      // ignore storage failures
    }

    return !exists
  }
}


