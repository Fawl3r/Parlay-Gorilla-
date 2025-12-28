import type {
  WebPushSubscribeRequest,
  WebPushVapidPublicKeyResponse,
} from '@/lib/api/types'
import type { ApiFacade } from '@/lib/api/ApiFacade'
import { VapidKeyDecoder } from '@/lib/notifications/VapidKeyDecoder'

export class WebPushNotificationsManager {
  constructor(private readonly api: ApiFacade) {}

  isSupported(): boolean {
    return (
      typeof window !== 'undefined' &&
      'Notification' in window &&
      'serviceWorker' in navigator &&
      'PushManager' in window
    )
  }

  async getServerConfig(): Promise<WebPushVapidPublicKeyResponse> {
    return this.api.getWebPushVapidPublicKey()
  }

  async getCurrentSubscription(): Promise<PushSubscription | null> {
    if (!this.isSupported()) return null
    const registration = await navigator.serviceWorker.getRegistration()
    if (!registration) return null
    return await registration.pushManager.getSubscription()
  }

  async isSubscribed(): Promise<boolean> {
    return (await this.getCurrentSubscription()) !== null
  }

  async subscribe(): Promise<PushSubscription> {
    if (!this.isSupported()) {
      throw new Error('Browser notifications are not supported on this device.')
    }

    const config = await this.getServerConfig()
    if (!config.enabled || !config.public_key) {
      throw new Error('Notifications are not available right now.')
    }

    const permission = await Notification.requestPermission()
    if (permission !== 'granted') {
      throw new Error('Notifications are blocked. Please allow them in your browser settings.')
    }

    const registration = await navigator.serviceWorker.register('/push-sw.js', { scope: '/' })

    const existing = await registration.pushManager.getSubscription()
    if (existing) {
      await this.api.subscribeWebPush(this.toSubscribeRequest(existing))
      return existing
    }

    const applicationServerKey = new Uint8Array(VapidKeyDecoder.toUint8Array(config.public_key))
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey,
    })

    await this.api.subscribeWebPush(this.toSubscribeRequest(subscription))
    return subscription
  }

  async unsubscribe(): Promise<void> {
    if (!this.isSupported()) return

    const registration = await navigator.serviceWorker.getRegistration()
    if (!registration) return

    const subscription = await registration.pushManager.getSubscription()
    if (!subscription) return

    const endpoint = subscription.endpoint

    try {
      await subscription.unsubscribe()
    } finally {
      // Best-effort: remove from backend even if browser unsubscribe fails.
      await this.api.unsubscribeWebPush(endpoint)
    }
  }

  private toSubscribeRequest(subscription: PushSubscription): WebPushSubscribeRequest {
    const json = subscription.toJSON() as any
    return {
      endpoint: subscription.endpoint,
      keys: {
        p256dh: String(json?.keys?.p256dh || ''),
        auth: String(json?.keys?.auth || ''),
      },
      expirationTime: (json?.expirationTime ?? null) as any,
    }
  }
}


