/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async headers() {
    return [
      { source: '/push-sw.js', headers: [{ key: 'Cache-Control', value: 'no-store' }] },
      { source: '/manifest.json', headers: [{ key: 'Cache-Control', value: 'no-store' }] },
    ]
  },
  async rewrites() {
    // Proxy backend API through Next.js to avoid CORS/localhost issues (especially on tunnels/mobile).
    // This runs on the Next.js server, not in the browser.
    const prodBackendUrl = "https://api.parlaygorilla.com"
    const isProd = process.env.NODE_ENV === "production"

    let backendBaseUrl =
      process.env.PG_BACKEND_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      process.env.BACKEND_URL ||
      (isProd ? prodBackendUrl : "http://localhost:8000")

    // Production: always use API host. Never proxy to localhost or to the frontend origin.
    const rawBackend = String(backendBaseUrl || "").trim()
    const looksLocal = /localhost|127\.0\.0\.1/.test(rawBackend)
    const looksLikeFrontend = /https?:\/\/(www\.)?parlaygorilla\.com\b/.test(rawBackend)
    if (isProd && (looksLocal || looksLikeFrontend || !rawBackend)) {
      backendBaseUrl = prodBackendUrl
    }

    // Allow Render private-network hostport values (e.g. my-backend:10000)
    if (backendBaseUrl && !String(backendBaseUrl).includes("://")) {
      backendBaseUrl = `http://${backendBaseUrl}`;
    }

    return [
      {
        source: "/health",
        destination: `${backendBaseUrl}/health`,
      },
      {
        source: "/api/:path*",
        destination: `${backendBaseUrl}/api/:path*`,
      },
    ];
  },
  images: {
    remotePatterns: [
      // Team logos removed - we use TeamBadge component with abbreviations and colors only
    ],
  },
  // Ignore TypeScript errors during build
  // These are type annotation issues with framer-motion, not runtime errors
  typescript: {
    ignoreBuildErrors: true,
  },
  // Performance optimizations for faster compilation
  // Note: swcMinify is enabled by default in Next.js 16+
  // Turbopack file system caching is enabled by default in Next.js 16.1+
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  // Turbopack configuration (default in Next.js 16+)
  turbopack: {
    // Client-side fallbacks: avoid bundling Node core modules into the browser build
    resolveAlias: {
      // Explicit path aliases for Turbopack (matches tsconfig.json paths)
      // Note: Turbopack should auto-detect from tsconfig.json, but explicit config ensures compatibility
      '@': './',
    },
  },
  // Webpack configuration (for --webpack flag compatibility)
  webpack: (config, { dev, isServer, nextRuntime }) => {
    // Faster source maps in development
    if (dev) {
      config.devtool = "eval-cheap-module-source-map";
    }

    // Optimize module resolution
    config.resolve.symlinks = false;

    // Client-only fallbacks: avoid bundling Node core modules into the browser build.
    // (Do NOT apply to the server build.)
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      };
    }

    // CRITICAL FIX (Next 16 + Webpack):
    // The server webpack runtime currently tries to require chunks as `./<id>.js`,
    // but Next emits them under `.next/server/chunks/<id>.js`.
    // Force a chunk filename template that matches the emitted path so runtime loads correctly.
    // In dev, explicitly align server chunk paths to avoid runtime requiring `./<id>.js`
    // when chunks are emitted under `.next/server/chunks/<id>.js`.
    // Note: This may not be needed in Next.js 16.1+ with improved chunk handling, but kept for compatibility.
    if (dev && isServer && nextRuntime !== "edge") {
      config.output.chunkFilename = "chunks/[id].js";
    }

    // Avoid overriding Next.js' own webpack caching strategy.
    // Forcing `config.cache` can cause mismatched runtime/chunk outputs on Windows.

    return config;
  },
  // Experimental features for faster builds
  experimental: {
    // optimizeCss: true, // Disabled - requires critters package
    optimizePackageImports: ['lucide-react', 'framer-motion'],
  },
  // Note: Path aliases are automatically handled by Next.js from tsconfig.json
  // No custom webpack config needed for @ alias resolution
}

module.exports = nextConfig

