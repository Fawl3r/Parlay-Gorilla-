import { APIRequestContext } from "@playwright/test";

const backendUrl = process.env.PG_BACKEND_URL || "http://localhost:8000";

export async function registerUser(request: APIRequestContext, email: string, password: string) {
  const res = await request.post(`${backendUrl}/api/auth/register`, {
    data: { email, password },
  });
  if (!res.ok()) throw new Error(`Register failed: ${res.status()}`);
  const data = await res.json();
  return data.access_token as string;
}

export async function adminWalletLogin(request: APIRequestContext, wallet: string) {
  const res = await request.post(`${backendUrl}/api/admin/auth/wallet-login`, {
    data: { wallet_address: wallet, message: "e2e" },
  });
  if (!res.ok()) throw new Error(`Admin login failed: ${res.status()}`);
  const data = await res.json();
  return data.token as string;
}


