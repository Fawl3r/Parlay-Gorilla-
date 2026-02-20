# Cloudflare Cache and Next.js Headers

This doc describes how caching is configured for the frontend and what to do when the UI appears stale after a deployment.

---

## Next.js headers (frontend/next.config.js)

The app sets **Cache-Control** so that:

- **HTML/document routes** (`/`, `/:path*`): `public, max-age=0, must-revalidate`  
  → Browsers and CDNs are told to revalidate every time; they must not serve old HTML without checking.
- **Static assets** (`/_next/static/:path*`): `public, max-age=31536000, immutable`  
  → Hashed filenames allow long-term caching; immutable is safe for these assets.

So in code we **do not** aggressively cache HTML. Only `/_next/static` is long-cached.

---

## When the UI still looks stale after a deploy

If you have deployed (e.g. pushed to `main`, Vercel and backend deploy ran) but the site still shows old content:

1. **Stale UI usually means Cloudflare (or another CDN) is serving a cached response.**  
   The origin (Vercel) may already be serving the new build, but the edge cache has not been updated.

2. **Action: purge the Cloudflare cache** for the frontend (parlaygorilla.com / www).  
   - In Cloudflare Dashboard: select the zone → **Caching** → **Configuration** → **Purge Everything** (or purge by URL/prefix if you prefer).  
   - After purge, reload the site; you should get the new HTML and new `/_next/static` assets.

3. **Do not change Cloudflare configuration** for this fix. Only purge cache when you need to see a new deployment immediately. Normal requests will eventually get fresh content once cache TTL expires; with `max-age=0, must-revalidate`, Cloudflare should revalidate when it respects the origin headers.

---

## Summary

- **next.config.js** enforces **must-revalidate** for HTML and **immutable** only for `/_next/static`.
- **Stale UI after deploy** → treat as **Cloudflare (or CDN) cache** and **purge cache** so users see the new deployment.
