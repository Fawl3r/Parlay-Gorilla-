import type { MetadataRoute } from "next"

function resolveSiteUrl(): string {
  const raw = process.env.NEXT_PUBLIC_SITE_URL || "https://parlaygorilla.com"
  const withProto = raw.includes("://") ? raw : `https://${raw}`
  return withProto.replace(/\/+$/, "")
}

export default function robots(): MetadataRoute.Robots {
  const siteUrl = resolveSiteUrl()

  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
      },
    ],
    sitemap: `${siteUrl}/sitemap.xml`,
    host: siteUrl,
  }
}




