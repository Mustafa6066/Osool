'use client';

import { useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
    ArrowRight, Building2, TrendingUp, GitCompare,
    BarChart3, Sparkles, Sun, Moon
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import ProfileDropdown from '@/components/ProfileDropdown';
import InvitationModal from '@/components/InvitationModal';
import ThemeToggle from '@/components/ThemeToggle';
import LanguageToggle from '@/components/LanguageToggle';

export default function Home() {
    const { isAuthenticated, loading, user } = useAuth();
    const { t, language } = useLanguage();
    const [showInvitationModal, setShowInvitationModal] = useState(false);

    const developers = ['EMAAR', 'SODIC', 'ORASCOM', 'PALM HILLS', 'MOUNTAIN VIEW', 'TMG'];

    return (
        <main className="min-h-screen bg-[var(--color-background)] text-[var(--color-text-primary)] font-display selection:bg-[#267360] selection:text-white overflow-x-hidden">
            {/* Invitation Modal */}
            <InvitationModal
                isOpen={showInvitationModal}
                onClose={() => setShowInvitationModal(false)}
            />

            {/* Navigation */}
            <header className="fixed top-0 w-full z-50 border-b border-[var(--color-border)] backdrop-blur-xl bg-[var(--color-background)]/80 transition-colors duration-300">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16 sm:h-20">
                        {/* Logo */}
                        <Link href="/" className="flex items-center gap-2 text-[#267360] group">
                            <div className="w-8 h-8 rounded bg-[#267360] text-white flex items-center justify-center transition-transform group-hover:scale-110">
                                <Building2 size={20} />
                            </div>
                            <span className="text-xl font-bold tracking-tight">AMR</span>
                        </Link>

                        {/* Desktop Nav */}
                        <nav className="hidden md:flex items-center gap-8">
                            <Link href="#market" className="text-sm font-medium hover:text-[#267360] transition-colors">
                                Market Analysis
                            </Link>
                            <Link href="#developers" className="text-sm font-medium hover:text-[#267360] transition-colors">
                                Developers
                            </Link>
                        </nav>

                        {/* Actions */}
                        <div className="flex items-center gap-3">
                            {!loading && !isAuthenticated && (
                                <Link href="/login" className="hidden md:block text-sm font-medium hover:text-[#267360] transition-colors mr-2">
                                    Login
                                </Link>
                            )}
                            <LanguageToggle />
                            <ThemeToggle />

                            {loading ? (
                                <div className="w-32 h-10 bg-[var(--color-surface)] rounded-lg animate-pulse"></div>
                            ) : isAuthenticated ? (
                                <>
                                    <button
                                        onClick={() => setShowInvitationModal(true)}
                                        className="bg-[#267360] hover:bg-[#1e5c4d] text-white text-sm font-bold py-2.5 px-5 rounded-lg transition-all shadow-lg shadow-[#267360]/20 hidden sm:flex items-center gap-2 group"
                                    >
                                        <span>Generate Invitation</span>
                                        <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
                                    </button>
                                    <ProfileDropdown onGenerateInvitation={() => setShowInvitationModal(true)} />
                                </>
                            ) : (
                                <Link href="/signup" className="bg-[#267360] hover:bg-[#1e5c4d] text-white text-sm font-bold py-2.5 px-5 rounded-lg transition-all shadow-lg shadow-[#267360]/20 flex items-center gap-2 group">
                                    <span>Get Early Access</span>
                                    <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
                                </Link>
                            )}
                        </div>
                    </div>
                </div>
            </header>

            {/* Hero Section */}
            <section className="relative px-4 py-12 md:py-20 lg:py-24 max-w-7xl mx-auto w-full mt-20">
                <div className="grid lg:grid-cols-2 gap-12 items-center">
                    {/* Text Content */}
                    <div className="flex flex-col gap-6 max-w-2xl">
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#267360]/10 border border-[#267360]/20 w-fit">
                            <span className="w-2 h-2 rounded-full bg-[#267360] animate-pulse"></span>
                            <span className="text-xs font-bold text-[#267360] tracking-wide uppercase">AI-Powered Insights V2.0</span>
                        </div>
                        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black leading-[1.1] tracking-tight">
                            The Intelligence Behind Your{' '}
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#267360] to-emerald-400">
                                Next Investment.
                            </span>
                        </h1>
                        <p className="text-lg text-[var(--color-text-secondary)] leading-relaxed max-w-lg">
                            AMR is the state-of-the-art AI advisor for the Egyptian real estate market. Analyze, compare, and invest with data-driven confidence in Cairo and beyond.
                        </p>
                        <div className="flex flex-wrap gap-3 mt-2">
                            <Link
                                href={isAuthenticated ? "/chat" : "/login"}
                                className="bg-[#267360] text-white h-12 px-8 rounded-lg font-bold text-base hover:bg-[#1e5c4d] transition-all flex items-center justify-center gap-2"
                            >
                                Start Analysis
                                <BarChart3 size={20} />
                            </Link>
                            <Link
                                href="#demo"
                                className="h-12 px-8 rounded-lg font-bold text-base border border-[var(--color-border)] hover:bg-[var(--color-surface)] transition-all flex items-center justify-center"
                            >
                                View Demo
                            </Link>
                        </div>
                        <div className="flex items-center gap-4 mt-6 text-sm text-[var(--color-text-muted)]">
                            <div className="flex -space-x-2">
                                {[1, 2, 3].map((i) => (
                                    <div
                                        key={i}
                                        className="w-8 h-8 rounded-full border-2 border-[var(--color-background)] bg-gradient-to-br from-[#267360] to-emerald-600"
                                    />
                                ))}
                            </div>
                            <p>Trusted by 2,000+ investors</p>
                        </div>
                    </div>

                    {/* Visual Dashboard */}
                    <div className="relative w-full aspect-[4/3] lg:aspect-square max-h-[600px] flex items-center justify-center">
                        {/* Background Glow */}
                        <div className="absolute inset-0 bg-[#267360]/20 blur-[100px] rounded-full opacity-50 dark:opacity-30"></div>

                        {/* Dashboard Card */}
                        <div className="relative w-full h-full bg-[var(--color-surface)] rounded-xl border border-[var(--color-border)] shadow-2xl overflow-hidden flex flex-col">
                            {/* Card Header */}
                            <div className="px-6 py-4 border-b border-[var(--color-border)] flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="w-3 h-3 rounded-full bg-red-500"></div>
                                    <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                                    <div className="w-3 h-3 rounded-full bg-green-500"></div>
                                </div>
                                <div className="px-3 py-1 bg-[var(--color-surface)] rounded text-xs font-mono text-[var(--color-text-muted)]">
                                    amr_agent_v2.exe
                                </div>
                            </div>

                            {/* Stats & Chart */}
                            <div className="relative flex-1 p-6 flex flex-col gap-6">
                                {/* Stats Row */}
                                <div className="flex gap-4">
                                    <div className="flex-1 bg-[var(--color-background)] p-4 rounded-lg border border-[var(--color-border)]">
                                        <p className="text-xs text-[var(--color-text-muted)] mb-1">New Capital Growth</p>
                                        <div className="flex items-end gap-2">
                                            <span className="text-2xl font-bold">+12.4%</span>
                                            <span className="text-xs text-[#267360] font-bold mb-1">↑ YTD</span>
                                        </div>
                                    </div>
                                    <div className="flex-1 bg-[var(--color-background)] p-4 rounded-lg border border-[var(--color-border)]">
                                        <p className="text-xs text-[var(--color-text-muted)] mb-1">Predicted ROI</p>
                                        <div className="flex items-end gap-2">
                                            <span className="text-2xl font-bold">18%</span>
                                            <span className="text-xs text-[var(--color-text-muted)] mb-1">Annual</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Chart Visualization */}
                                <div className="flex-1 bg-[var(--color-background)] rounded-lg border border-[var(--color-border)] p-4 relative overflow-hidden group">
                                    <div className="absolute top-4 right-4 z-10">
                                        <span className="bg-[#267360] text-white text-xs font-bold px-2 py-1 rounded">Live Analysis</span>
                                    </div>
                                    <svg className="w-full h-full" viewBox="0 0 400 200" preserveAspectRatio="none">
                                        <defs>
                                            <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="0%" stopColor="#267360" stopOpacity="0.4" />
                                                <stop offset="100%" stopColor="#267360" stopOpacity="0" />
                                            </linearGradient>
                                        </defs>
                                        <path
                                            d="M0,160 Q40,150 80,120 T160,110 T240,80 T320,60 L400,30 L400,200 L0,200 Z"
                                            fill="url(#chartGradient)"
                                        />
                                        <path
                                            d="M0,160 Q40,150 80,120 T160,110 T240,80 T320,60 L400,30"
                                            fill="none"
                                            stroke="#267360"
                                            strokeWidth="3"
                                            strokeLinecap="round"
                                        />
                                        <circle cx="320" cy="60" r="6" fill="currentColor" className="text-[var(--color-surface)] stroke-[#267360] stroke-[3px] animate-pulse" />
                                    </svg>
                                </div>
                            </div>

                            {/* Floating Alert */}
                            <div className="absolute bottom-6 left-6 right-6 bg-[var(--color-surface-elevated)] p-3 rounded-lg shadow-lg border border-[var(--color-border)] flex items-center gap-3 animate-bounce" style={{ animationDuration: '3s' }}>
                                <div className="w-8 h-8 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center text-green-600 dark:text-green-400">
                                    <TrendingUp size={18} />
                                </div>
                                <div>
                                    <p className="text-xs font-bold">Market Alert</p>
                                    <p className="text-xs text-[var(--color-text-muted)]">Sodic East prices up 2% this week.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Developer Ticker */}
            <section id="developers" className="border-y border-[var(--color-border)] bg-[var(--color-surface)] py-8 overflow-hidden">
                <div className="max-w-7xl mx-auto px-4 mb-4">
                    <p className="text-center text-sm font-medium text-[var(--color-text-muted)] uppercase tracking-wider">
                        Trusted insights on properties from
                    </p>
                </div>
                <div className="relative flex overflow-x-hidden group">
                    <div className="animate-marquee whitespace-nowrap flex items-center gap-16 px-8 opacity-60 grayscale hover:grayscale-0 transition-all duration-500">
                        {[...developers, ...developers].map((dev, idx) => (
                            <span key={idx} className="text-2xl font-bold text-[var(--color-text-muted)]">
                                {dev}
                            </span>
                        ))}
                    </div>
                </div>
            </section>

            {/* Bento Grid Features */}
            <section id="market" className="py-20 px-4 max-w-7xl mx-auto w-full">
                <div className="flex flex-col gap-4 mb-12">
                    <h2 className="text-3xl md:text-4xl font-bold tracking-tight max-w-2xl">
                        Smarter Investment Decisions
                    </h2>
                    <p className="text-lg text-[var(--color-text-secondary)] max-w-2xl">
                        Leverage AI to uncover hidden opportunities in the Egyptian property market.
                    </p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Real-time Analysis */}
                    <div className="md:col-span-2 group relative overflow-hidden rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-sm hover:shadow-md transition-all hover:border-[#267360]/50">
                        <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:opacity-20 transition-opacity">
                            <BarChart3 size={96} className="text-[#267360]" />
                        </div>
                        <div className="relative z-10 flex flex-col h-full justify-between">
                            <div>
                                <div className="w-12 h-12 rounded-lg bg-[#267360]/10 flex items-center justify-center text-[#267360] mb-6">
                                    <BarChart3 size={24} />
                                </div>
                                <h3 className="text-2xl font-bold mb-2">Real-time Analysis</h3>
                                <p className="text-[var(--color-text-secondary)] max-w-md">
                                    Live data tracking market trends across Cairo, New Capital, and North Coast. Our algorithms process thousands of data points daily.
                                </p>
                            </div>
                            <div className="mt-8">
                                <Link href="/chat" className="flex items-center gap-2 text-[#267360] font-bold text-sm group">
                                    <span>View Market Report</span>
                                    <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
                                </Link>
                            </div>
                        </div>
                    </div>

                    {/* ROI Forecasting */}
                    <div className="group relative overflow-hidden rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-sm hover:shadow-md transition-all hover:border-[#267360]/50">
                        <div className="w-12 h-12 rounded-lg bg-[#267360]/10 flex items-center justify-center text-[#267360] mb-6">
                            <TrendingUp size={24} />
                        </div>
                        <h3 className="text-xl font-bold mb-2">ROI Forecasting</h3>
                        <p className="text-sm text-[var(--color-text-secondary)] mb-6">
                            Predictive models estimate your property's future value growth over 5 and 10 years.
                        </p>
                        {/* Micro Chart */}
                        <div className="h-24 w-full bg-[var(--color-background)] rounded border border-[var(--color-border)] relative flex items-end px-2 pb-2 gap-1">
                            {[40, 55, 45, 70, 85].map((height, idx) => (
                                <div
                                    key={idx}
                                    className="w-1/5 bg-[#267360] rounded-sm transition-all"
                                    style={{ height: `${height}%`, opacity: 0.2 + (idx * 0.2) }}
                                />
                            ))}
                        </div>
                    </div>

                    {/* Developer Comparisons */}
                    <div className="group relative overflow-hidden rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-sm hover:shadow-md transition-all hover:border-[#267360]/50">
                        <div className="w-12 h-12 rounded-lg bg-[#267360]/10 flex items-center justify-center text-[#267360] mb-6">
                            <GitCompare size={24} />
                        </div>
                        <h3 className="text-xl font-bold mb-2">Developer Comparisons</h3>
                        <p className="text-sm text-[var(--color-text-secondary)]">
                            Unbiased side-by-side comparisons. See delivery history, finish quality, and resale value retention.
                        </p>
                    </div>

                    {/* AI Chat - Demo Section */}
                    <div id="demo" className="md:col-span-2 group relative overflow-hidden rounded-lg border border-[var(--color-border)] bg-[#1A1D1F] p-8 shadow-sm hover:shadow-md transition-all scroll-mt-24">
                        <div className="absolute inset-0 bg-gradient-to-r from-[#267360]/20 to-transparent opacity-20"></div>
                        <div className="relative z-10 flex flex-col sm:flex-row gap-8 items-center">
                            <div className="flex-1">
                                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/20 w-fit mb-4">
                                    <Sparkles size={16} className="text-[#267360]" />
                                    <span className="text-xs font-bold text-white tracking-wide">AMR ASSISTANT</span>
                                </div>
                                <h3 className="text-2xl font-bold mb-2 text-white">Ask AMR Anything</h3>
                                <p className="text-gray-300 max-w-md mb-6">
                                    "What is the average price per meter in Sheikh Zayed?"<br />
                                    "Compare payment plans for Zed Towers vs. O West."
                                </p>
                                <Link
                                    href={isAuthenticated ? "/chat" : "/login"}
                                    className="bg-white text-gray-900 px-6 py-2 rounded-lg font-bold text-sm hover:bg-gray-100 transition-colors inline-block"
                                >
                                    Try AI Chat
                                </Link>
                            </div>
                            {/* Chat Simulation */}
                            <div className="w-full sm:w-1/2 bg-[#2c3533] rounded-lg p-4 border border-white/10 flex flex-col gap-3">
                                <div className="self-end bg-[#267360]/20 text-white text-xs p-3 rounded-t-lg rounded-bl-lg max-w-[90%] border border-[#267360]/20">
                                    Is it a good time to buy in New Alamein?
                                </div>
                                <div className="self-start bg-[#1e2423] text-gray-200 text-xs p-3 rounded-t-lg rounded-br-lg max-w-[90%] border border-white/5">
                                    <span className="text-[#267360] font-bold block mb-1">AMR Analysis:</span>
                                    Yes. Seasonal demand is peaking. Prices have risen 8% in Q1 2024. Rental yields are currently averaging 7-9%.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-20 bg-[var(--color-surface)]">
                <div className="max-w-4xl mx-auto px-4 text-center">
                    <h2 className="text-3xl md:text-5xl font-black mb-6 tracking-tight">
                        Ready to invest with confidence?
                    </h2>
                    <p className="text-lg text-[var(--color-text-secondary)] mb-10 max-w-xl mx-auto">
                        Join the waiting list for AMR Premium and get exclusive access to off-market opportunities.
                    </p>
                    {!isAuthenticated && (
                        <Link
                            href="/signup"
                            className="inline-flex h-12 px-8 items-center rounded-lg bg-[#267360] text-white font-bold hover:bg-[#1e5c4d] transition-colors"
                        >
                            Get Early Access
                        </Link>
                    )}
                </div>
            </section>

            {/* Footer */}
            <footer className="border-t border-[var(--color-border)] py-12">
                <div className="max-w-7xl mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-6">
                    <div className="flex items-center gap-2">
                        <Building2 className="text-[#267360]" size={20} />
                        <span className="text-lg font-bold">AMR</span>
                    </div>
                    <div className="flex gap-8 text-sm text-[var(--color-text-secondary)]">
                        <a href="#" className="hover:text-[#267360] transition-colors">Privacy Policy</a>
                        <a href="#" className="hover:text-[#267360] transition-colors">Terms of Service</a>
                        <a href="#" className="hover:text-[#267360] transition-colors">Contact</a>
                    </div>
                    <div className="text-sm text-[var(--color-text-muted)]">
                        © 2024 AMR Intelligence. All rights reserved.
                    </div>
                </div>
            </footer>

            <style jsx global>{`
                html {
                    scroll-behavior: smooth;
                }
                @keyframes marquee {
                    0% { transform: translateX(0); }
                    100% { transform: translateX(-50%); }
                }
                .animate-marquee {
                    animation: marquee 30s linear infinite;
                }
            `}</style>
        </main>
    );
}
