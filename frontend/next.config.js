/** @type {import('next').NextConfig} */
const nextConfig = {
    transpilePackages: ['framer-motion'],
    eslint: {
        ignoreDuringBuilds: true,
    },
    typescript: {
        ignoreBuildErrors: true,
    },
    experimental: {
        workerThreads: false,
        cpus: 1,
    },
    async rewrites() {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        return [
            {
                source: '/api/:path*',
                destination: `${apiUrl}/api/:path*`,
            },
            {
                source: '/auth/:path*',
                destination: `${apiUrl}/auth/:path*`,
            },
            {
                source: '/ws/:path*',
                destination: `${apiUrl}/ws/:path*`,
            },
        ];
    },
};

module.exports = nextConfig;
