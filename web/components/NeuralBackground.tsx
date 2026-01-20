'use client';

import React from 'react';

export default function NeuralBackground() {
    return (
        <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
            {/* Grid Pattern */}
            <div className="absolute inset-0 opacity-40 dark:opacity-100 bg-grid-light dark:bg-grid-dark grid-bg"></div>

            {/* Gradient Overlay */}
            <div className="absolute inset-0 bg-gradient-to-b from-[var(--color-background-light)]/50 via-transparent to-[var(--color-background-light)]/80 dark:from-[var(--color-background-dark)]/50 dark:via-transparent dark:to-[var(--color-background-dark)]/90 pointer-events-none"></div>

            {/* Animated Synapse Lines (Reference Design) */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none hidden lg:block z-10" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="gradient-champagne" x1="0%" x2="100%" y1="0%" y2="0%">
                        <stop offset="0%" style={{ stopColor: '#E6D5B8', stopOpacity: 0 }}></stop>
                        <stop offset="50%" style={{ stopColor: '#E6D5B8', stopOpacity: 0.8 }}></stop>
                        <stop offset="100%" style={{ stopColor: '#E6D5B8', stopOpacity: 0 }}></stop>
                    </linearGradient>
                    <linearGradient id="gradient-rose" x1="0%" x2="100%" y1="0%" y2="0%">
                        <stop offset="0%" style={{ stopColor: '#D4A3A3', stopOpacity: 0 }}></stop>
                        <stop offset="50%" style={{ stopColor: '#D4A3A3', stopOpacity: 0.8 }}></stop>
                        <stop offset="100%" style={{ stopColor: '#D4A3A3', stopOpacity: 0 }}></stop>
                    </linearGradient>
                    <linearGradient id="gradient-sage" x1="0%" x2="100%" y1="0%" y2="0%">
                        <stop offset="0%" style={{ stopColor: '#A3B18A', stopOpacity: 0 }}></stop>
                        <stop offset="50%" style={{ stopColor: '#A3B18A', stopOpacity: 0.8 }}></stop>
                        <stop offset="100%" style={{ stopColor: '#A3B18A', stopOpacity: 0 }}></stop>
                    </linearGradient>
                </defs>

                {/* Synapse to Property Card (Left) */}
                <path className="synapse-line" d="M 50% 50% C 40% 45%, 30% 45%, 20% 40%" fill="none" opacity="0.6" stroke="url(#gradient-champagne)" strokeWidth="1"></path>

                {/* Synapse to Insights Card (Top Right) */}
                <path className="synapse-line" d="M 50% 50% C 60% 45%, 70% 35%, 80% 30%" fill="none" opacity="0.6" stroke="url(#gradient-rose)" strokeWidth="1" style={{ animationDelay: '1s' }}></path>

                {/* Synapse to ROI Card (Bottom Right) */}
                <path className="synapse-line" d="M 50% 50% C 60% 60%, 70% 65%, 75% 70%" fill="none" opacity="0.5" stroke="url(#gradient-sage)" strokeWidth="1" style={{ animationDelay: '2s' }}></path>

                {/* Synapse to FABs (Bottom Left) */}
                <path className="synapse-line" d="M 50% 50% C 40% 60%, 30% 70%, 25% 75%" fill="none" opacity="0.4" stroke="url(#gradient-champagne)" strokeWidth="1" style={{ animationDelay: '1.5s' }}></path>
            </svg>
        </div>
    );
}
