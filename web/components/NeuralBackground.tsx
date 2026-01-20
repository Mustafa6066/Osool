'use client';

import React from 'react';

export default function NeuralBackground() {
    return (
        <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
            {/* Grid Pattern */}
            <div className="absolute inset-0 opacity-40 dark:opacity-100 bg-grid-light dark:bg-grid-dark grid-bg"></div>

            {/* Gradient Overlay */}

            {/* Animated Synapses */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none z-10 overflow-visible" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="synapse-gradient" x1="0%" x2="100%" y1="0%" y2="0%">
                        <stop offset="0%" stopColor="#E6D5B8" stopOpacity="0"></stop>
                        <stop offset="50%" stopColor="#E6D5B8" stopOpacity="0.8"></stop>
                        <stop offset="100%" stopColor="#ffffff" stopOpacity="0"></stop>
                    </linearGradient>
                    <filter id="glow">
                        <feGaussianBlur result="coloredBlur" stdDeviation="2.5"></feGaussianBlur>
                        <feMerge>
                            <feMergeNode in="coloredBlur"></feMergeNode>
                            <feMergeNode in="SourceGraphic"></feMergeNode>
                        </feMerge>
                    </filter>
                </defs>

                {/* Synapse 1 */}
                <path className="synapse-path" d="M 50% 50% C 45% 50%, 40% 40%, 30% 35%" fill="none" stroke="url(#synapse-gradient)" strokeWidth="1.5" style={{ animationDuration: '5s' }}></path>
                <circle className="animate-pulse opacity-70" cx="30%" cy="35%" fill="#E6D5B8" r="3">
                    <animate attributeName="opacity" dur="3s" repeatCount="indefinite" values="0.3;0.8;0.3"></animate>
                </circle>

                {/* Synapse 2 */}
                <path className="synapse-path" d="M 50% 50% C 60% 50%, 70% 40%, 75% 30%" fill="none" stroke="url(#synapse-gradient)" strokeWidth="1.5" style={{ animationDuration: '4.5s', animationDelay: '1s' }}></path>
                <circle className="animate-pulse opacity-70" cx="75%" cy="30%" fill="#D4A3A3" r="3">
                    <animate attributeName="opacity" dur="4s" repeatCount="indefinite" values="0.3;0.8;0.3"></animate>
                </circle>

                {/* Synapse 3 */}
                <path className="synapse-path" d="M 50% 50% C 55% 60%, 65% 70%, 75% 75%" fill="none" stroke="url(#synapse-gradient)" strokeWidth="1.5" style={{ animationDuration: '6s', animationDelay: '2s' }}></path>
                <circle className="animate-pulse opacity-70" cx="75%" cy="75%" fill="#A3B18A" r="3">
                    <animate attributeName="opacity" dur="5s" repeatCount="indefinite" values="0.3;0.8;0.3"></animate>
                </circle>
            </svg>
        </div>
    );
}
