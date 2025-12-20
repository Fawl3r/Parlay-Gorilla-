export class VapidKeyDecoder {
  // Convert base64url string to Uint8Array for PushManager.subscribe().
  static toUint8Array(base64Url: string): Uint8Array {
    const raw = String(base64Url || '').trim()
    if (!raw) return new Uint8Array()

    const padding = '='.repeat((4 - (raw.length % 4)) % 4)
    const base64 = (raw + padding).replace(/-/g, '+').replace(/_/g, '/')
    const binary = atob(base64)

    const bytes = new Uint8Array(binary.length)
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i)
    }
    return bytes
  }
}


