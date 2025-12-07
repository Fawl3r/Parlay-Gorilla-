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
  webpack: (config, { isServer }) => {
    // Ensure @ alias resolves correctly
    const alias = config.resolve.alias || {};
    config.resolve.alias = {
      ...alias,
      '@': path.resolve(__dirname),
    };
    
    // Ensure proper module resolution
    config.resolve.modules = [
      path.resolve(__dirname, 'node_modules'),
      'node_modules',
    ];
    
    return config;
  },
}

module.exports = nextConfig

