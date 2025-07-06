/** @type {import('next').NextConfig} */
const nextConfig = {
  // output: 'standalone', // Commenting out for simpler deployment
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  env: {
    BACKEND_URL: process.env.BACKEND_URL || (process.env.NODE_ENV === 'production' ? 'http://backend:8000' : 'http://localhost:8000'),
  },
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL || (process.env.NODE_ENV === 'production' ? 'http://backend:8000' : 'http://localhost:8000');
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/:path*`,
      },
    ]
  },
}

module.exports = nextConfig