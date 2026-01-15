export interface WebPushVapidPublicKeyResponse {
  enabled: boolean
  public_key: string
}

export interface WebPushSubscribeRequest {
  endpoint: string
  keys: {
    p256dh: string
    auth: string
  }
  expirationTime?: number | null
}

export interface WebPushSubscribeResponse {
  success: boolean
  subscription_id: string
}

export interface WebPushUnsubscribeResponse {
  success: boolean
  deleted: number
}
