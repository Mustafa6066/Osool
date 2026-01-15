"use client";

import { motion } from 'framer-motion';
import { ReactNode } from 'react';

interface FeatureCardProps {
    icon: ReactNode;
    title: string;
    description: string;
    gradient: string;
    delay?: number;
}

export default function FeatureCard({ icon, title, description, gradient, delay = 0 }: FeatureCardProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.6, delay }}
            className="group relative rounded-2xl p-6 
                 bg-[var(--color-surface)] border border-[var(--color-border)]
                 hover:border-transparent hover:shadow-xl
                 transition-all duration-300 card-hover"
        >
            {/* Gradient Border on Hover */}
            <div className={`absolute inset-0 rounded-2xl ${gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-300 -z-10 blur-sm`} />
            <div className="absolute inset-[1px] rounded-2xl bg-[var(--color-surface)] -z-5" />

            {/* Icon */}
            <div className={`w-14 h-14 rounded-xl ${gradient} flex items-center justify-center mb-5 
                       shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                <div className="text-white">
                    {icon}
                </div>
            </div>

            {/* Title */}
            <h3 className="text-xl font-bold text-[var(--color-text-primary)] mb-3 group-hover:text-[var(--color-primary)] transition-colors">
                {title}
            </h3>

            {/* Description */}
            <p className="text-[var(--color-text-secondary)] leading-relaxed">
                {description}
            </p>

            {/* Hover Arrow */}
            <div className="mt-4 flex items-center gap-2 text-[var(--color-primary)] opacity-0 group-hover:opacity-100 transition-opacity">
                <span className="text-sm font-semibold">Learn more</span>
                <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
            </div>
        </motion.div>
    );
}
