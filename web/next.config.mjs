import { dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const webRoot = dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
    typescript: {
        ignoreBuildErrors: false,
    },
    turbopack: {
        root: webRoot,
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
