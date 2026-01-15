'use client';

import Link from 'next/link';
import { ArrowRight, CheckCircle2, TrendingUp, Shield, Brain, Sparkles, MessageSquare } from 'lucide-react';
import AmrDemoChat from '../components/AmrDemoChat';
import { motion } from 'framer-motion';

export default function Home() {
    return (
        <main className="min-h-screen bg-slate-50 dark:bg-slate-950 overflow-hidden relative">
            {/* Background Gradients */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
                <div className="absolute -top-[10%] -left-[10%] w-[50%] h-[50%] bg-green-500/10 rounded-full blur-[100px] animate-pulse"></div>
                <div className="absolute top-[20%] -right-[10%] w-[40%] h-[40%] bg-blue-500/10 rounded-full blur-[100px] animate-pulse [animation-delay:2s]"></div>
            </div>

            {/* Navbar (Simple) */}
            <nav className="relative z-50 w-full max-w-7xl mx-auto px-6 py-6 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <span className="text-2xl font-black bg-gradient-to-r from-green-600 to-emerald-500 bg-clip-text text-transparent">Osool</span>
                    <span className="px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs font-bold border border-green-200 dark:border-green-800">BETA</span>
                </div>
                <div className="flex items-center gap-4">
                    <Link href="/login" className="text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-green-600 dark:hover:text-green-400 transition-colors">Login</Link>
                    <Link href="/signup" className="px-5 py-2.5 rounded-full bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-sm font-bold shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-0.5">
                        Get Early Access
                    </Link>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="relative z-10 w-full max-w-7xl mx-auto px-6 pt-10 pb-20 md:pt-20 md:pb-32 grid lg:grid-cols-2 gap-16 items-center">

                {/* Left: Copy */}
                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="space-y-8"
                >
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 shadow-sm">
                        <Sparkles size={16} className="text-amber-500" />
                        <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">Phase 1: The Only Honest Agent in Egypt</span>
                    </div>

                    <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-slate-900 dark:text-white leading-[1.1]">
                        Meet <span className="text-green-600">Amr.</span> <br />
                        Your Real Estate <br />
                        <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">Wealth Partner.</span>
                    </h1>

                    <p className="text-lg md:text-xl text-slate-600 dark:text-slate-400 max-w-lg leading-relaxed">
                        Stop guessing. Start investing. Amr analyzes 5,000+ verified listings against inflation data to find your perfect hedge.
                    </p>

                    <div className="flex flex-col sm:flex-row gap-4 pt-4">
                        <Link href="/chat" className="group px-8 py-4 rounded-full bg-green-600 hover:bg-green-700 text-white font-bold text-lg shadow-lg shadow-green-500/30 transition-all flex items-center justify-center gap-2">
                            Start Chatting Free
                            <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                        </Link>
                        <Link href="/market" className="px-8 py-4 rounded-full bg-white dark:bg-slate-800 text-slate-900 dark:text-white font-bold text-lg border border-slate-200 dark:border-slate-700 hover:border-green-500/50 transition-all flex items-center justify-center gap-2">
                            <TrendingUp size={20} className="text-slate-500" />
                            Market Data
                        </Link>
                    </div>

                    <div className="flex items-center gap-6 pt-4 text-sm text-slate-500 dark:text-slate-500 font-medium">
                        <div className="flex items-center gap-2">
                            <CheckCircle2 size={18} className="text-green-500" /> No Sales Calls
                        </div>
                        <div className="flex items-center gap-2">
                            <CheckCircle2 size={18} className="text-green-500" /> Verified Data
                        </div>
                        <div className="flex items-center gap-2">
                            <CheckCircle2 size={18} className="text-green-500" /> AI-Driven ROI
                        </div>
                    </div>
                </motion.div>

                {/* Right: Demo */}
                <motion.div
                    initial={{ opacity: 0, x: 30 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.8, delay: 0.2 }}
                    className="relative"
                >
                    <div className="absolute -inset-4 bg-gradient-to-tr from-green-500/20 to-blue-500/20 rounded-[2rem] blur-2xl opacity-70"></div>
                    <AmrDemoChat />

                    {/* Floating Badges */}
                    <motion.div
                        animate={{ y: [0, -10, 0] }}
                        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                        className="absolute -right-8 top-20 bg-white dark:bg-slate-800 p-4 rounded-2xl shadow-xl border border-slate-100 dark:border-slate-700 z-20 hidden md:block"
                    >
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-full">
                                <Brain size={20} className="text-blue-600 dark:text-blue-400" />
                            </div>
                            <div>
                                <p className="text-xs text-slate-500 font-bold uppercase">Intelligence</p>
                                <p className="text-sm font-bold text-slate-900 dark:text-white">GPT-4o + XGBoost</p>
                            </div>
                        </div>
                    </motion.div>

                    <motion.div
                        animate={{ y: [0, 10, 0] }}
                        transition={{ duration: 5, repeat: Infinity, ease: "easeInOut", delay: 1 }}
                        className="absolute -left-8 bottom-20 bg-white dark:bg-slate-800 p-4 rounded-2xl shadow-xl border border-slate-100 dark:border-slate-700 z-20 hidden md:block"
                    >
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-full">
                                <Shield size={20} className="text-green-600 dark:text-green-400" />
                            </div>
                            <div>
                                <p className="text-xs text-slate-500 font-bold uppercase">Trust</p>
                                <p className="text-sm font-bold text-slate-900 dark:text-white">0% hallucinations</p>
                            </div>
                        </div>
                    </motion.div>
                </motion.div>

            </section>

            {/* Feature Grid (Quick) */}
            <section className="w-full max-w-7xl mx-auto px-6 py-20 border-t border-slate-200 dark:border-slate-800">
                <div className="grid md:grid-cols-3 gap-8">
                    {[
                        {
                            icon: <MessageSquare size={32} className="text-blue-500" />,
                            title: "Visual Conversations",
                            desc: "Amr doesn't just text. He draws charts, maps, and ROI projections in real-time."
                        },
                        {
                            icon: <Brain size={32} className="text-purple-500" />,
                            title: "Inflation Hedging",
                            desc: "Our engine tracks currency devaluation daily to recommend assets that hold value."
                        },
                        {
                            icon: <Shield size={32} className="text-green-500" />,
                            title: "Verified Inventory",
                            desc: "Access 14,000+ units from top developers. No ghost listings. No waste of time."
                        }
                    ].map((feature, i) => (
                        <div key={i} className="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 hover:shadow-xl hover:-translate-y-1 transition-all">
                            <div className="mb-6 p-4 rounded-2xl bg-slate-50 dark:bg-slate-800 inline-block">
                                {feature.icon}
                            </div>
                            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-3">{feature.title}</h3>
                            <p className="text-slate-600 dark:text-slate-400 leading-relaxed">{feature.desc}</p>
                        </div>
                    ))}
                </div>
            </section>

        </main>
    );
}
