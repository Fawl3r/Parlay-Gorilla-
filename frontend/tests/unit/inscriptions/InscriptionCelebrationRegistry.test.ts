import { describe, expect, it } from "vitest"

import { InscriptionCelebrationRegistry, type KeyValueStorage } from "@/lib/inscriptions/InscriptionCelebrationRegistry"

class MemoryStorage implements KeyValueStorage {
  private readonly map = new Map<string, string>()

  getItem(key: string): string | null {
    return this.map.get(key) ?? null
  }

  setItem(key: string, value: string): void {
    this.map.set(key, value)
  }
}

describe("InscriptionCelebrationRegistry", () => {
  it("persists marked ids and restores them", () => {
    const storage = new MemoryStorage()
    const a = new InscriptionCelebrationRegistry(storage, { storageKey: "t", maxEntries: 50 })

    expect(a.has("p1")).toBe(false)
    a.mark("p1")
    a.mark("p2")
    expect(a.has("p1")).toBe(true)
    expect(a.snapshot().sort()).toEqual(["p1", "p2"])

    const b = new InscriptionCelebrationRegistry(storage, { storageKey: "t", maxEntries: 50 })
    expect(b.has("p1")).toBe(true)
    expect(b.has("p2")).toBe(true)
  })

  it("caps stored entries to maxEntries", () => {
    const storage = new MemoryStorage()
    const reg = new InscriptionCelebrationRegistry(storage, { storageKey: "t2", maxEntries: 10 })
    for (let i = 0; i < 25; i++) reg.mark(`p-${i}`)

    const raw = storage.getItem("t2")
    expect(raw).toBeTruthy()
    const parsed = JSON.parse(raw || "[]")
    expect(Array.isArray(parsed)).toBe(true)
    expect(parsed.length).toBeLessThanOrEqual(10)
  })
})


