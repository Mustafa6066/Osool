"use client";

import { useLanguage } from '@/contexts/LanguageContext';
import FeatureCard from './FeatureCard';
import { motion } from 'framer-motion';
import {
    TrendingUp,
    Search,
    Calculator,
    BarChart3,
    LineChart,
    Sparkles
} from 'lucide-react';

export default function Features() {
    const { t } = useLanguage();

    const features = [
        {
            icon: <Search className="w-7 h-7" />,
            titleKey: 'features.intelligentSearch.title',
            descKey: 'features.intelligentSearch.description',
            gradient: 'bg-gradient-to-br from-blue-500 to-cyan-600',
        },
        {
            icon: <TrendingUp className="w-7 h-7" />,
            titleKey: 'features.aiValuation.title',
            descKey: 'features.aiValuation.description',
            gradient: 'bg-gradient-to-br from-green-500 to-emerald-600',
        },
        {
            icon: <Calculator className="w-7 h-7" />,
            titleKey: 'features.mortgageCalculator.title',
            descKey: 'features.mortgageCalculator.description',
            gradient: 'bg-gradient-to-br from-purple-500 to-indigo-600',
        },
        {
            icon: <BarChart3 className="w-7 h-7" />,
            titleKey: 'features.investmentAnalysis.title',
            descKey: 'features.investmentAnalysis.description',
            gradient: 'bg-gradient-to-br from-pink-500 to-rose-600',
        },
        {
            icon: <LineChart className="w-7 h-7" />,
            titleKey: 'features.visualInsights.title',
            descKey: 'features.visualInsights.description',
            gradient: 'bg-gradient-to-br from-orange-500 to-amber-600',
        },
        {
            icon: <Sparkles className="w-7 h-7" />,
            titleKey: 'features.proactiveRecommendations.title',
            descKey: 'features.proactiveRecommendations.description',
            gradient: 'bg-gradient-to-br from-violet-500 to-purple-600',
        },
    ];

    return (
        <section className="section-padding bg-[var(--color-background)]">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Section Header */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                    className="text-center mb-16"
                >
                    <h2 className="text-h1 text-[var(--color-text-primary)] mb-4">
                        {t('features.title')}
                    </h2>
                    <p className="text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto">
                        {t('features.subtitle')}
                    </p>
                </motion.div>

                {/* Features Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
                    {features.map((feature, index) => (
                        <FeatureCard
                            key={index}
                            icon={feature.icon}
                            title={t(feature.titleKey)}
                            description={t(feature.descKey)}
                            gradient={feature.gradient}
                            delay={index * 0.1}
                        />
                    ))}
                </div>
            </div>
        </section>
    );
}
