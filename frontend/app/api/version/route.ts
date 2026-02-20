import { NextResponse } from "next/server"

/**
 * Lightweight version endpoint for Deploy Guardian and build verification.
 * Returns git_sha only (NEXT_PUBLIC_GIT_SHA from build); no secrets, no auth.
 * Cache-Control: no-store so Cloudflare and clients do not cache.
 */
export const dynamic = "force-dynamic"

export async function GET() {
  const gitSha =
    (process.env.NEXT_PUBLIC_GIT_SHA && process.env.NEXT_PUBLIC_GIT_SHA.trim()) ||
    "unknown"
  return NextResponse.json(
    { git_sha: gitSha },
    { headers: { "Cache-Control": "no-store" } }
  )
}
