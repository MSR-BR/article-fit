import type { NextConfig } from 'next';
import path from 'node:path';

const nextConfig: NextConfig = {
  output: 'standalone',
  poweredByHeader: false,
  reactStrictMode: true,
  transpilePackages: ['@journal-matcher/contracts'],
  turbopack: {
    root: path.join(import.meta.dirname, '../..'),
  },
};

export default nextConfig;
