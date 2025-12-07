const path = require('path');

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'a.espncdn.com',
        pathname: '/i/teamlogos/**',
      },
    ],
  },
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // Explicitly set the @ alias to ensure it works in all cases
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname),
    };
    
    // Debug: Log the alias configuration (only in dev to avoid build logs)
    if (dev) {
      console.log('Webpack alias @ resolves to:', path.resolve(__dirname));
    }
    
    return config;
  },
}

module.exports = nextConfig

