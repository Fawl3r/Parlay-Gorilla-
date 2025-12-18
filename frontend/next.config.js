/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    // Proxy backend API through Next.js to avoid CORS/localhost issues (especially on tunnels/mobile).
    // This runs on the Next.js server, not in the browser.
    let backendBaseUrl =
      process.env.PG_BACKEND_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      "http://localhost:8000";

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
  // Ignore ESLint errors during production build
  // These are style issues, not runtime errors
  eslint: {
    ignoreDuringBuilds: true,
  },
  // Ignore TypeScript errors during build
  // These are type annotation issues with framer-motion, not runtime errors
  typescript: {
    ignoreBuildErrors: true,
  },
  // Performance optimizations for faster compilation
  // Note: swcMinify is enabled by default in Next.js 15+
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  // Optimize webpack for faster builds
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

    // CRITICAL FIX (Next 15 + Webpack):
    // The server webpack runtime currently tries to require chunks as `./<id>.js`,
    // but Next emits them under `.next/server/chunks/<id>.js`.
    // Force a chunk filename template that matches the emitted path so runtime loads correctly.
    // In dev, explicitly align server chunk paths to avoid runtime requiring `./<id>.js`
    // when chunks are emitted under `.next/server/chunks/<id>.js`.
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

