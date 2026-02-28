'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
    ArrowRight, Building2, TrendingUp, GitCompare,
    BarChart3, Sparkles
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
        <main className="min-h-screen bg-[var(--color-background)] text-[var(--color-text-primary)] selection:bg-emerald-500/20 selection:text-emerald-200 overflow-x-hidden">
            {/* Invitation Modal */}
            <InvitationModal
                isOpen={showInvitationModal}
                onClose={() => setShowInvitationModal(false)}
            />

            {/* Floating Navigation */}
            <header className="fixed top-4 left-0 right-0 z-50 flex justify-center px-4">
                <div className="flex items-center justify-between h-14 w-full max-w-5xl bg-[var(--color-surface)]/80 backdrop-blur-2xl border border-[var(--color-border)]/50 rounded-full shadow-[0_8px_30px_rgb(0,0,0,0.04)] px-4 sm:px-6">
                    {/* Logo */}
                    <Link href="/" className="flex items-center gap-2.5 group">
                        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-gray-900 to-gray-700 dark:from-white dark:to-gray-200 flex items-center justify-center text-white dark:text-gray-900 shadow-sm transition-transform group-hover:scale-105 group-hover:shadow-md">
                            <span className="text-[11px] font-bold tracking-wider">OA</span>
                        </div>
                        <span className="text-[15px] font-semibold tracking-tight text-[var(--color-text-primary)]">Osool<span className="text-emerald-500">.ai</span></span>
                    </Link>

                    {/* Actions */}
                    <div className="flex items-center gap-2">
                        {!loading && !isAuthenticated && (
                            <Link href="/login" className="hidden md:block text-[13px] font-medium text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-gray-100 dark:hover:bg-gray-800/80 rounded-full transition-all px-4 py-2">
                                Log in
                            </Link>
                        )}
                        <LanguageToggle />
                        <ThemeToggle />

                        {loading ? (
                            <div className="w-24 h-9 bg-[var(--color-surface-hover)] rounded-full animate-pulse ml-2" />
                        ) : isAuthenticated ? (
                            <>
                                <button
                                    onClick={() => setShowInvitationModal(true)}
                                    className="bg-gray-100 dark:bg-gray-800/80 text-[var(--color-text-primary)] text-[13px] font-medium py-2 px-4 rounded-full transition-all hover:bg-gray-200 dark:hover:bg-gray-700 hidden sm:flex items-center gap-2"
                                >
                                    <span>Invite</span>
                                    <ArrowRight size={14} strokeWidth={2} />
                                </button>
                                <div className="ml-1">
                                    <ProfileDropdown onGenerateInvitation={() => setShowInvitationModal(true)} />
                                </div>
                            </>
                        ) : (
                            <Link href="/signup" className="bg-gray-900 dark:bg-white text-white dark:text-gray-900 text-[13px] font-semibold py-2 px-5 rounded-full transition-transform hover:scale-105 active:scale-95 shadow-sm flex items-center gap-2 ml-2">
                                <span>Get Started</span>
                                <ArrowRight size={14} strokeWidth={2} />
                            </Link>
                        )}
                    </div>
                </div>
            </header>

            {/* Hero Section */}
            <section className="relative px-4 pt-36 pb-20 md:pt-44 md:pb-28 max-w-6xl mx-auto w-full">
                <div className="flex flex-col items-center text-center gap-6">
                    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/8 border border-emerald-500/15 mb-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                        <span className="text-[11px] font-medium text-emerald-600 dark:text-emerald-400 tracking-wide uppercase">AI-Powered Real Estate Intelligence</span>
                    </div>

                    <h1 className="text-[3rem] sm:text-[4rem] lg:text-[5rem] font-semibold leading-[1.05] tracking-tight max-w-4xl text-balance">
                        The intelligence behind your{' '}
                        <span className="text-emerald-500">next investment</span>
                    </h1>

                    <p className="text-[17px] md:text-lg text-[var(--color-text-secondary)] font-medium leading-relaxed max-w-2xl text-balance mt-2">
                        AMR analyzes the Egyptian real estate market with AI precision. Get instant insights on pricing, ROI forecasts, and developer audits.
                    </p>

                    <div className="flex flex-wrap gap-4 mt-6 justify-center">
                        <Link
                            href={isAuthenticated ? "/chat" : "/login"}
                            className="bg-gray-900 dark:bg-white text-white dark:text-gray-900 h-12 px-8 rounded-full font-semibold text-[15px] hover:scale-105 active:scale-95 transition-all shadow-[0_8px_30px_rgba(0,0,0,0.12)] flex items-center gap-2"
                        >
                            Start Analysis
                            <ArrowRight size={18} strokeWidth={2.5} />
                        </Link>
                        <Link
                            href="#demo"
                            className="h-12 px-8 rounded-full font-semibold text-[15px] bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-sm transition-all flex items-center shadow-[0_2px_10px_rgba(0,0,0,0.02)]"
                        >
                            View Demo
                        </Link>
                    </div>

                    <div className="flex items-center gap-3 mt-8 text-sm text-[var(--color-text-muted)]">
                        <div className="flex -space-x-1.5">
                            {[1, 2, 3].map((i) => (
                                <div key={i} className="w-6 h-6 rounded-full border-2 border-[var(--color-background)] bg-emerald-500/20" />
                            ))}
                        </div>
                        <p className="text-xs">Trusted by 2,000+ investors</p>
                    </div>
                </div>
            </section>

            {/* Dashboard Preview */}
            <section className="px-4 pb-20 max-w-5xl mx-auto">
                <div className="relative bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] shadow-2xl shadow-black/5 dark:shadow-black/30 overflow-hidden">
                    {/* Window Chrome */}
                    <div className="px-5 py-3 border-b border-[var(--color-border)] flex items-center gap-2">
                        <div className="flex gap-1.5">
                            <div className="w-2.5 h-2.5 rounded-full bg-[var(--color-text-muted)]/20" />
                            <div className="w-2.5 h-2.5 rounded-full bg-[var(--color-text-muted)]/20" />
                            <div className="w-2.5 h-2.5 rounded-full bg-[var(--color-text-muted)]/20" />
                        </div>
                        <div className="flex-1 flex justify-center">
                            <div className="px-3 py-0.5 bg-[var(--color-background)] rounded text-[10px] font-mono text-[var(--color-text-muted)]">
                                amr.osool.ai
                            </div>
                        </div>
                    </div>

                    <div className="p-6 md:p-8 flex flex-col gap-5">
                        {/* Stats */}
                        <div className="grid grid-cols-3 gap-4">
                            <div className="bg-[var(--color-background)] p-4 rounded-xl border border-[var(--color-border)]">
                                <p className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mb-1">New Capital Growth</p>
                                <div className="flex items-baseline gap-1.5">
                                    <span className="text-xl font-semibold">+12.4%</span>
                                    <span className="text-[10px] text-emerald-500 font-medium">YTD</span>
                                </div>
                            </div>
                            <div className="bg-[var(--color-background)] p-4 rounded-xl border border-[var(--color-border)]">
                                <p className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Predicted ROI</p>
                                <div className="flex items-baseline gap-1.5">
                                    <span className="text-xl font-semibold">18%</span>
                                    <span className="text-[10px] text-[var(--color-text-muted)]">Annual</span>
                                </div>
                            </div>
                            <div className="bg-[var(--color-background)] p-4 rounded-xl border border-[var(--color-border)]">
                                <p className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Liquidity Score</p>
                                <div className="flex items-baseline gap-1.5">
                                    <span className="text-xl font-semibold">87</span>
                                    <span className="text-[10px] text-emerald-500 font-medium">/100</span>
                                </div>
                            </div>
                        </div>

                        {/* Chart */}
                        <div className="bg-[var(--color-background)] rounded-xl border border-[var(--color-border)] p-5 relative h-48">
                            <div className="absolute top-4 left-5 flex items-center gap-2">
                                <span className="text-xs font-medium text-[var(--color-text-primary)]">Price Trend</span>
                                <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-500 font-medium">Live</span>
                            </div>
                            <svg className="w-full h-full" viewBox="0 0 400 160" preserveAspectRatio="none">
                                <defs>
                                    <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="rgb(16,185,129)" stopOpacity="0.15" />
                                        <stop offset="100%" stopColor="rgb(16,185,129)" stopOpacity="0" />
                                    </linearGradient>
                                </defs>
                                <path d="M0,130 Q40,120 80,100 T160,90 T240,60 T320,45 L400,20 L400,160 L0,160 Z" fill="url(#chartGradient)" />
                                <path d="M0,130 Q40,120 80,100 T160,90 T240,60 T320,45 L400,20" fill="none" stroke="rgb(16,185,129)" strokeWidth="2" strokeLinecap="round" />
                                <circle cx="400" cy="20" r="3" fill="rgb(16,185,129)" className="animate-pulse" />
                            </svg>
                        </div>
                    </div>
                </div>
            </section>

            {/* Developer Ticker */}
            <section id="developers" className="border-y border-[var(--color-border)] py-8 overflow-hidden">
                <div className="max-w-6xl mx-auto px-4 mb-4">
                    <p className="text-center text-[11px] font-medium text-[var(--color-text-muted)] uppercase tracking-[0.15em]">
                        Trusted insights on properties from
                    </p>
                </div>
                <div className="relative flex overflow-x-hidden">
                    <div className="animate-marquee whitespace-nowrap flex items-center gap-16 px-8 opacity-40">
                        {[...developers, ...developers].map((dev, idx) => (
                            <span key={idx} className="text-xl font-semibold text-[var(--color-text-muted)] tracking-wide">
                                {dev}
                            </span>
                        ))}
                    </div>
                </div>
            </section>

            {/* Feature Grid */}
            <section id="market" className="py-24 px-4 max-w-5xl mx-auto w-full">
                <div className="flex flex-col gap-3 mb-14 max-w-xl">
                    <h2 className="text-3xl md:text-4xl font-medium tracking-tight">
                        Smarter investment decisions
                    </h2>
                    <p className="text-[var(--color-text-secondary)]">
                        AI-powered tools to uncover hidden opportunities in the Egyptian property market.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Real-time Analysis */}
                    <div className="md:col-span-2 group relative overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-7 hover:border-emerald-500/20 transition-all duration-300">
                        <div className="flex flex-col h-full justify-between">
                            <div>
                                <div className="w-10 h-10 rounded-xl bg-emerald-500/8 flex items-center justify-center text-emerald-500 mb-5">
                                    <BarChart3 size={20} />
                                </div>
                                <h3 className="text-xl font-medium mb-2">Real-time Analysis</h3>
                                <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed max-w-md">
                                    Live data tracking market trends across Cairo, New Capital, and North Coast. Thousands of data points processed daily.
                                </p>
                            </div>
                            <div className="mt-6">
                                <Link href="/chat" className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-medium text-sm group/link">
                                    <span>View Market Report</span>
                                    <ArrowRight size={14} className="group-hover/link:translate-x-0.5 transition-transform" />
                                </Link>
                            </div>
                        </div>
                    </div>

                    {/* ROI Forecasting */}
                    <div className="group rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-7 hover:border-emerald-500/20 transition-all duration-300">
                        <div className="w-10 h-10 rounded-xl bg-emerald-500/8 flex items-center justify-center text-emerald-500 mb-5">
                            <TrendingUp size={20} />
                        </div>
                        <h3 className="text-lg font-medium mb-2">ROI Forecasting</h3>
                        <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed mb-5">
                            Predictive models estimate future value growth over 5 and 10 years.
                        </p>
                        <div className="h-20 w-full bg-[var(--color-background)] rounded-lg border border-[var(--color-border)] flex items-end px-2 pb-2 gap-1">
                            {[40, 55, 45, 70, 85].map((height, idx) => (
                                <div key={idx} className="w-1/5 bg-emerald-500 rounded-sm transition-all" style={{ height: `${height}%`, opacity: 0.15 + (idx * 0.2) }} />
                            ))}
                        </div>
                    </div>

                    {/* Developer Comparisons */}
                    <div className="group rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-7 hover:border-emerald-500/20 transition-all duration-300">
                        <div className="w-10 h-10 rounded-xl bg-emerald-500/8 flex items-center justify-center text-emerald-500 mb-5">
                            <GitCompare size={20} />
                        </div>
                        <h3 className="text-lg font-medium mb-2">Developer Comparisons</h3>
                        <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed">
                            Unbiased side-by-side comparisons. Delivery history, finish quality, and resale value retention.
                        </p>
                    </div>

                    {/* AI Chat Demo */}
                    <div id="demo" className="md:col-span-2 group rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-dark,var(--color-surface))] p-7 hover:border-emerald-500/20 transition-all duration-300 scroll-mt-24 overflow-hidden relative">
                        <div className="flex flex-col sm:flex-row gap-6 items-start">
                            <div className="flex-1">
                                <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/8 border border-emerald-500/15 mb-4">
                                    <Sparkles size={12} className="text-emerald-500" />
                                    <span className="text-[10px] font-medium text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">AMR Assistant</span>
                                </div>
                                <h3 className="text-xl font-medium mb-2">Ask AMR Anything</h3>
                                <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed mb-5">
                                    &ldquo;Average price per meter in Sheikh Zayed?&rdquo;<br />
                                    &ldquo;Compare Zed Towers vs. O West payment plans.&rdquo;
                                </p>
                                <Link
                                    href={isAuthenticated ? "/chat" : "/login"}
                                    className="bg-[var(--color-text-primary)] text-[var(--color-background)] px-5 py-2 rounded-lg font-medium text-sm hover:opacity-90 transition-opacity inline-block"
                                >
                                    Try AI Chat
                                </Link>
                            </div>
                            <div className="w-full sm:w-5/12 bg-[var(--color-background)] rounded-xl p-4 border border-[var(--color-border)] flex flex-col gap-2.5">
                                <div className="self-end bg-[var(--color-surface)] text-[var(--color-text-primary)] text-xs p-3 rounded-2xl rounded-br-md max-w-[90%] border border-[var(--color-border)]">
                                    Is it a good time to buy in New Alamein?
                                </div>
                                <div className="self-start text-[var(--color-text-secondary)] text-xs p-3 max-w-[90%] leading-relaxed">
                                    <span className="text-emerald-500 font-medium block mb-1 text-[10px] uppercase tracking-wider">AMR Analysis</span>
                                    Seasonal demand is peaking. Prices rose 8% in Q1 2024. Rental yields averaging 7-9%.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* CTA */}
            <section className="py-24 border-t border-[var(--color-border)]">
                <div className="max-w-2xl mx-auto px-4 text-center">
                    <h2 className="text-3xl md:text-4xl font-medium mb-4 tracking-tight">
                        Ready to invest with confidence?
                    </h2>
                    <p className="text-[var(--color-text-secondary)] mb-8 max-w-lg mx-auto">
                        Join the waiting list for AMR Premium and get exclusive access to off-market opportunities.
                    </p>
                    {!isAuthenticated && (
                        <Link
                            href="/signup"
                            className="inline-flex h-11 px-7 items-center rounded-xl bg-[var(--color-text-primary)] text-[var(--color-background)] font-medium text-sm hover:opacity-90 transition-opacity"
                        >
                            Get Early Access
                        </Link>
                    )}
                </div>
            </section>

            {/* Footer */}
            <footer className="border-t border-[var(--color-border)] py-10">
                <div className="max-w-5xl mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-4">
                    <div className="flex items-center gap-2">
                        <div className="w-5 h-5 rounded bg-[var(--color-text-primary)] text-[var(--color-background)] flex items-center justify-center">
                            <span className="text-[7px] font-bold">A</span>
                        </div>
                        <span className="text-sm font-medium">AMR</span>
                    </div>
                    <div className="flex gap-6 text-xs text-[var(--color-text-muted)]">
                        <a href="#" className="hover:text-[var(--color-text-primary)] transition-colors">Privacy</a>
                        <a href="#" className="hover:text-[var(--color-text-primary)] transition-colors">Terms</a>
                        <a href="#" className="hover:text-[var(--color-text-primary)] transition-colors">Contact</a>
                    </div>
                    <div className="text-xs text-[var(--color-text-muted)]">
                        © 2024 AMR Intelligence
                    </div>
                </div>
            </footer>

            <style jsx global>{`
                html { scroll-behavior: smooth; }
                @keyframes marquee {
                    0% { transform: translateX(0); }
                    100% { transform: translateX(-50%); }
                }
                .animate-marquee { animation: marquee 30s linear infinite; }
            `}</style>
        </main>
    );
}
