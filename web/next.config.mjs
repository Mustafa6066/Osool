/** @type {import('next').NextConfig} */
const nextConfig = {
    typescript: {
        ignoreBuildErrors: false,
    },
    images: {
        remotePatterns: [
            {
                protocol: 'https',
                hostname: 'images.unsplash.com',
            },
            {
                protocol: 'https',
                hostname: '**.nawy.com',
            },
            {
                protocol: 'https',
                hostname: 'cdn.nawy.com',
            },
            {
                protocol: 'https',
                hostname: 'nawy.com',
            },
        ],
    },
};

export default nextConfig;
