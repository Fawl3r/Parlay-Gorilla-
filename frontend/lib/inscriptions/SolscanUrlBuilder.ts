export class SolscanUrlBuilder {
  static forTx(signature: string): string {
    const sig = String(signature || "").trim()
    if (!sig) return "https://solscan.io"
    return `https://solscan.io/tx/${encodeURIComponent(sig)}`
  }
}


