"use client";

import { useLanguage } from '@/contexts/LanguageContext';
import { motion } from 'framer-motion';
import { Search, Shield, TrendingUp } from 'lucide-react';

export default function HowItWorks() {
    const { t } = useLanguage();

    const steps = [
        {
            number: '01',
            icon: <Search className="w-8 h-8" />,
            titleKey: 'howItWorks.step1.title',
            descKey: 'howItWorks.step1.description',
            gradient: 'from-blue-500 to-cyan-500',
        },
        {
            number: '02',
            icon: <Shield className="w-8 h-8" />,
            titleKey: 'howItWorks.step2.title',
            descKey: 'howItWorks.step2.description',
            gradient: 'from-purple-500 to-indigo-500',
        },
        {
            number: '03',
            icon: <TrendingUp className="w-8 h-8" />,
            titleKey: 'howItWorks.step3.title',
            descKey: 'howItWorks.step3.description',
            gradient: 'from-green-500 to-emerald-500',
        },
    ];

    return (
        <section className="section-padding bg-[var(--color-background)] relative overflow-hidden">
            {/* Background Decoration */}
            <div className="absolute inset-0 overflow-hidden">
                <div className="absolute -top-40 -right-40 w-80 h-80 bg-[var(--color-primary)]/5 rounded-full blur-3xl" />
                <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-[var(--color-secondary)]/5 rounded-full blur-3xl" />
            </div>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
                {/* Section Header */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="text-center mb-16"
                >
                    <h2 className="text-h1 text-[var(--color-text-primary)] mb-4">
                        {t('howItWorks.title')}
                    </h2>
                    <p className="text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto">
                        {t('howItWorks.subtitle')}
                    </p>
                </motion.div>

                {/* Steps */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 lg:gap-12">
                    {steps.map((step, index) => (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 30 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.6, delay: index * 0.15 }}
                            className="relative text-center"
                        >
                            {/* Connector Line (hidden on mobile and last item) */}
                            {index < steps.length - 1 && (
                                <div className="hidden md:block absolute top-20 left-[60%] w-[80%] h-[2px]">
                                    <div className="w-full h-full bg-gradient-to-r from-[var(--color-border)] via-[var(--color-primary)]/30 to-[var(--color-border)]" />
                                    <div className="absolute right-0 top-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-[var(--color-primary)]" />
                                </div>
                            )}

                            {/* Step Number & Icon */}
                            <div className="relative inline-block mb-6">
                                <div className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${step.gradient} flex items-center justify-center text-white shadow-lg`}>
                                    {step.icon}
                                </div>
                                <div className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-[var(--color-background)] border-2 border-[var(--color-border)] flex items-center justify-center text-xs font-bold text-[var(--color-text-primary)]">
                                    {step.number}
                                </div>
                            </div>

                            {/* Title */}
                            <h3 className="text-xl font-bold text-[var(--color-text-primary)] mb-3">
                                {t(step.titleKey)}
                            </h3>

                            {/* Description */}
                            <p className="text-[var(--color-text-secondary)] leading-relaxed">
                                {t(step.descKey)}
                            </p>
                        </motion.div>
                    ))}
                </div>

                {/* Trust Badges */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="mt-16 flex flex-wrap items-center justify-center gap-6"
                >
                    {[
                        'CBE Law 194 Compliant',
                        'Polygon Blockchain',
                        'AI-Powered Analytics',
                        '24/7 Support',
                    ].map((badge, index) => (
                        <div
                            key={index}
                            className="flex items-center gap-2 px-4 py-2 rounded-full bg-[var(--color-surface)] border border-[var(--color-border)] text-sm text-[var(--color-text-secondary)]"
                        >
                            <div className="w-2 h-2 rounded-full bg-[var(--color-primary)]" />
                            {badge}
                        </div>
                    ))}
                </motion.div>
            </div>
        </section>
    );
}
