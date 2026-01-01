export type KeyValueStorage = {
  getItem(key: string): string | null
  setItem(key: string, value: string): void
}

type Options = {
  storage: KeyValueStorage | null
  storageKey?: string
  maxEntries?: number
}

/**
 * Tracks which saved parlays have already shown the “inscription success” celebration,
 * so we don't spam users when polling refreshes or navigating between tabs.
 */
export class InscriptionCelebrationRegistry {
  private readonly storageKey: string
  private readonly maxEntries: number
  private readonly seen = new Set<string>()

  constructor(private readonly storage: KeyValueStorage | null, options?: Omit<Options, "storage">) {
    this.storageKey = options?.storageKey || "pg_inscription_celebrations_v1"
    this.maxEntries = Math.max(10, options?.maxEntries ?? 50)
    this.hydrate()
  }

  static fromSessionStorage(): InscriptionCelebrationRegistry {
    const storage =
      typeof window !== "undefined" && window.sessionStorage
        ? (window.sessionStorage as unknown as KeyValueStorage)
        : null
    return new InscriptionCelebrationRegistry(storage)
  }

  has(id: string): boolean {
    const key = String(id || "").trim()
    if (!key) return false
    return this.seen.has(key)
  }

  mark(id: string): void {
    const key = String(id || "").trim()
    if (!key) return
    this.seen.add(key)
    this.persist()
  }

  snapshot(): string[] {
    return Array.from(this.seen)
  }

  private hydrate(): void {
    if (!this.storage) return
    try {
      const raw = this.storage.getItem(this.storageKey)
      if (!raw) return
      const parsed = JSON.parse(raw)
      if (!Array.isArray(parsed)) return
      for (const entry of parsed) {
        const key = String(entry || "").trim()
        if (key) this.seen.add(key)
      }
    } catch {
      // Ignore corrupt/blocked storage.
    }
  }

  private persist(): void {
    if (!this.storage) return
    try {
      const entries = Array.from(this.seen).slice(-this.maxEntries)
      this.storage.setItem(this.storageKey, JSON.stringify(entries))
    } catch {
      // Ignore quota or blocked storage.
    }
  }
}


