export type ConfidenceComparable = {
  confidence?: number | null
}

export class BetConfidenceRanker<T extends ConfidenceComparable> {
  rank(items: readonly T[]): T[] {
    return [...items].sort((a, b) => this._confidence(b) - this._confidence(a))
  }

  top(items: readonly T[]): T | null {
    const ranked = this.rank(items)
    return ranked.length > 0 ? ranked[0] : null
  }

  private _confidence(item: T): number {
    const raw = item?.confidence
    return typeof raw === "number" && Number.isFinite(raw) ? raw : 0
  }
}


