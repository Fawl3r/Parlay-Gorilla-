/**
 * Parlay Purchase Utilities
 * 
 * Functions for managing one-time parlay purchases ($3 single, $5 multi).
 * Used when free users exhaust their daily free parlays.
 */

import axios from 'axios';

export type ParlayType = 'single' | 'multi';
export type Provider = 'lemonsqueezy' | 'coinbase';

export interface ParlayPurchaseCheckoutRequest {
  parlay_type: ParlayType;
  provider: Provider;
}

export interface ParlayPurchaseCheckoutResponse {
  checkout_url: string;
  provider: string;
  parlay_type: string;
  purchase_id: string;
  amount: number;
  currency: string;
}

export interface ParlayPurchase {
  id: string;
  user_id: string;
  parlay_type: string;
  amount: number;
  currency: string;
  status: string;
  is_available: boolean;
  is_expired: boolean;
  created_at: string | null;
  expires_at: string | null;
  used_at: string | null;
}

export interface ParlayPurchaseStats {
  available: number;
  used: number;
  expired: number;
  pending: number;
  total_spent: number;
}

export interface AvailablePurchasesResponse {
  has_single: boolean;
  has_multi: boolean;
  single_purchase: ParlayPurchase | null;
  multi_purchase: ParlayPurchase | null;
}

export interface UserPurchasesResponse {
  purchases: ParlayPurchase[];
  stats: ParlayPurchaseStats;
}

// Get API URL same way as main api.ts
const getApiUrl = (): string => {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      const isTunnel = /\.(ngrok|trycloudflare|localtest|loca|serveo|localhost\.run|tunnel|mole|serveo\.net|localtunnel\.me|ngrok\.io|cloudflaretunnel\.com|cfargotunnel\.com)/.test(hostname);
      if (isTunnel) {
        const port = window.location.port ? `:${window.location.port}` : '';
        return `${protocol}//${hostname}${port.replace(':3000', ':8000')}`;
      } else {
        return `http://${hostname}:8000`;
      }
    }
  }
  return 'http://localhost:8000';
};

const apiClient = axios.create({
  baseURL: getApiUrl(),
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000,
});

// Add auth token interceptor
apiClient.interceptors.request.use((config) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/**
 * Create a checkout session for one-time parlay purchase.
 * 
 * @param parlayType - 'single' ($3) or 'multi' ($5)
 * @param provider - 'lemonsqueezy' (card) or 'coinbase' (crypto)
 * @returns Checkout URL and purchase details
 */
export async function createParlayPurchaseCheckout(
  parlayType: ParlayType,
  provider: Provider = 'lemonsqueezy'
): Promise<ParlayPurchaseCheckoutResponse> {
  const response = await apiClient.post<ParlayPurchaseCheckoutResponse>(
    '/billing/parlay-purchase/checkout',
    {
      parlay_type: parlayType,
      provider,
    }
  );
  return response.data;
}

/**
 * Check if user has any available (unused) parlay purchases.
 * 
 * @returns Object with available purchases by type
 */
export async function checkAvailablePurchases(): Promise<AvailablePurchasesResponse> {
  const response = await apiClient.get<AvailablePurchasesResponse>(
    '/billing/parlay-purchase/available'
  );
  return response.data;
}

/**
 * Get user's parlay purchase history and stats.
 * 
 * @returns List of purchases and usage statistics
 */
export async function getUserPurchases(): Promise<UserPurchasesResponse> {
  const response = await apiClient.get<UserPurchasesResponse>('/billing/parlay-purchases');
  return response.data;
}

/**
 * Redirect user to checkout for parlay purchase.
 * 
 * @param parlayType - 'single' or 'multi'
 * @param provider - Payment provider
 */
export async function redirectToCheckout(
  parlayType: ParlayType,
  provider: Provider = 'lemonsqueezy'
): Promise<void> {
  try {
    const result = await createParlayPurchaseCheckout(parlayType, provider);
    
    // Redirect to checkout URL
    if (result.checkout_url) {
      window.location.href = result.checkout_url;
    } else {
      throw new Error('No checkout URL returned');
    }
  } catch (error) {
    console.error('Failed to create checkout:', error);
    throw error;
  }
}

/**
 * Get pricing information for parlay purchases.
 * Values are also in the backend config, but we hardcode them here for UI.
 */
export const PARLAY_PRICING = {
  single: {
    price: 3.00,
    currency: 'USD',
    label: 'Single-Sport Parlay',
    description: 'Generate one Gorilla Parlay for a single sport',
  },
  multi: {
    price: 5.00,
    currency: 'USD',
    label: 'Multi-Sport Parlay',
    description: 'Generate one Gorilla Parlay mixing multiple sports',
  },
} as const;

/**
 * Format price for display.
 */
export function formatPrice(amount: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(amount);
}

