/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  async rewrites() {
    const backendUrl = process.env.BACKEND_API_URL || 'http://localhost:8000';
    return [
      { source: '/api/:path*', destination: `${backendUrl}/api/:path*` },
      { source: '/docs/:path*', destination: `${backendUrl}/docs/:path*` },
      { source: '/openapi.json', destination: `${backendUrl}/openapi.json` },
    ];
  },
};
export default nextConfig;
