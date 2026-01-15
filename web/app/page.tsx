"use client";

import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, Bot, TrendingUp, BarChart3, MessageCircle, Sparkles, ChevronRight, Globe } from "lucide-react";
import { useState, useEffect } from "react";
import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";

// Animated counter for stats
function AnimatedNumber({ value, suffix = "" }: { value: number; suffix?: string }) {
    const [count, setCount] = useState(0);

    useEffect(() => {
        const duration = 2000;
        const steps = 60;
        const increment = value / steps;
        let current = 0;

        const timer = setInterval(() => {
            current += increment;
            if (current >= value) {
                setCount(value);
                clearInterval(timer);
            } else {
                setCount(Math.floor(current));
            }
        }, duration / steps);

        return () => clearInterval(timer);
    }, [value]);

    return <span>{count.toLocaleString()}{suffix}</span>;
}

// Floating particles background (Hydration Safe)
function FloatingParticles() {
    const [particles, setParticles] = useState<Array<{
        id: number;
        initialX: number;
        initialY: number;
        animateY: number;
        duration: number;
    }>>([]);

    useEffect(() => {
        // Generate particles only on client to avoid hydration mismatch
        const width = typeof window !== 'undefined' ? window.innerWidth : 1000;
        const newParticles = [...Array(20)].map((_, i) => ({
            id: i,
            initialX: Math.random() * width,
            initialY: Math.random() * 600,
            animateY: Math.random() * 600,
            duration: 10 + Math.random() * 10
        }));
        setParticles(newParticles);
    }, []);

    return (
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
            {particles.map((p) => (
                <motion.div
                    key={p.id}
                    className="absolute w-1 h-1 bg-purple-500/30 rounded-full"
                    initial={{
                        x: p.initialX,
                        y: p.initialY,
                    }}
                    animate={{
                        y: [null, p.animateY],
                        opacity: [0.2, 0.5, 0.2],
                    }}
                    transition={{
                        duration: p.duration,
                        repeat: Infinity,
                        ease: "linear",
                    }}
                />
            ))}
        </div>
    );
}

// AMR Avatar Component
function AMRAvatar() {
    return (
        <motion.div
            className="relative"
            animate={{ y: [0, -10, 0] }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
        >
            <div className="relative w-32 h-32 mx-auto">
                {/* Glow effect */}
                <div className="absolute inset-0 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full blur-2xl opacity-50" />

                {/* Main avatar */}
                <div className="relative w-32 h-32 rounded-full bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center border-4 border-white/20 shadow-2xl">
                    <Bot className="w-16 h-16 text-white" />
                </div>

                {/* Status indicator */}
                <div className="absolute bottom-2 right-2 w-6 h-6 bg-green-500 rounded-full border-4 border-[#0a0a0a] flex items-center justify-center">
                    <span className="animate-ping absolute w-full h-full rounded-full bg-green-400 opacity-75" />
                </div>
            </div>

            {/* Name badge */}
            <motion.div
                className="mt-4 text-center"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
            >
                <h3 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                    عمرو • Amr
                </h3>
                <p className="text-gray-400 text-sm mt-1">AI Real Estate Advisor</p>
            </motion.div>
        </motion.div>
    );
}

// Chat preview bubble
function ChatPreview() {
    const messages = [
        { role: "user", text: "عايز شقة في التجمع 3 غرف", isArabic: true },
        { role: "amr", text: "تمام! لقيتلك 8 شقق مناسبة لميزانيتك...", isArabic: true },
        { role: "user", text: "Show me ROI analysis", isArabic: false },
        { role: "amr", text: "This property offers 8.5% annual yield 📊", isArabic: false },
    ];

    const [visibleMessages, setVisibleMessages] = useState(0);

    useEffect(() => {
        const timer = setInterval(() => {
            setVisibleMessages(prev => (prev + 1) % (messages.length + 1));
        }, 2000);
        return () => clearInterval(timer);
    }, []);

    return (
        <div className="bg-[#1a1c2e]/80 backdrop-blur-xl rounded-2xl p-4 border border-white/10 shadow-2xl max-w-sm mx-auto">
            <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/10">
                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-600 to-blue-600 flex items-center justify-center">
                    <Bot className="w-4 h-4 text-white" />
                </div>
                <div>
                    <p className="text-white font-medium text-sm">Amr</p>
                    <p className="text-green-400 text-xs">● Online</p>
                </div>
            </div>

            <div className="space-y-3 min-h-[140px]">
                <AnimatePresence mode="popLayout">
                    {messages.slice(0, visibleMessages).map((msg, idx) => (
                        <motion.div
                            key={idx}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`max-w-[80%] px-3 py-2 rounded-xl text-sm ${msg.role === 'user'
                                    ? 'bg-purple-600 text-white rounded-br-none'
                                    : 'bg-white/10 text-gray-200 rounded-bl-none'
                                    }`}
                                dir={msg.isArabic ? 'rtl' : 'ltr'}
                            >
                                {msg.text}
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>
        </div>
    );
}

export default function Home() {
    return (
        <main className="min-h-screen bg-[#0a0a0a] text-white overflow-hidden">
            <Navigation />
            <FloatingParticles />

            {/* Hero Section */}
            <section className="relative pt-28 pb-24 px-4">
                {/* Background gradients */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-purple-600/20 blur-[150px] rounded-full opacity-40 pointer-events-none" />
                <div className="absolute top-40 right-0 w-[400px] h-[400px] bg-blue-600/15 blur-[100px] rounded-full pointer-events-none" />

                <div className="container mx-auto relative z-10">
                    <div className="grid lg:grid-cols-2 gap-16 items-center">
                        {/* Left: Text Content */}
                        <div className="text-center lg:text-left">
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.6 }}
                                className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-purple-500/30 bg-purple-500/10 backdrop-blur-sm mb-6"
                            >
                                <Sparkles className="w-4 h-4 text-purple-400" />
                                <span className="text-sm font-medium text-purple-300">Phase One • The Agentic Era</span>
                            </motion.div>

                            <motion.h1
                                initial={{ opacity: 0, y: 30 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.7, delay: 0.1 }}
                                className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-6"
                            >
                                Meet{" "}
                                <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-blue-400 to-purple-400 animate-gradient">
                                    Amr
                                </span>
                                <br />
                                <span className="text-gray-300">Your AI Agent</span>
                            </motion.h1>

                            <motion.p
                                initial={{ opacity: 0, y: 30 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.7, delay: 0.2 }}
                                className="text-lg md:text-xl text-gray-400 max-w-lg mx-auto lg:mx-0 mb-8 leading-relaxed"
                            >
                                The first AI that{" "}
                                <span className="text-white font-medium">speaks Egyptian Arabic</span>,
                                understands market psychology, and leads you to a{" "}
                                <span className="text-purple-400 font-medium">successful property deal</span>.
                            </motion.p>

                            <motion.div
                                initial={{ opacity: 0, y: 30 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.7, delay: 0.3 }}
                                className="flex flex-col sm:flex-row items-center gap-4 justify-center lg:justify-start"
                            >
                                <Link
                                    href="/chat"
                                    className="group relative px-8 py-4 rounded-full bg-gradient-to-r from-purple-600 to-blue-600 text-white font-bold text-lg transition-all hover:scale-105 active:scale-95 shadow-lg shadow-purple-500/30 hover:shadow-purple-500/50 flex items-center gap-2"
                                >
                                    <MessageCircle className="w-5 h-5" />
                                    Talk to Amr
                                    <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
                                </Link>

                                <Link
                                    href="/login"
                                    className="px-8 py-4 rounded-full border border-white/20 text-white font-medium hover:bg-white/5 transition-all flex items-center gap-2"
                                >
                                    Sign In
                                    <ChevronRight className="w-4 h-4" />
                                </Link>
                            </motion.div>
                        </div>

                        {/* Right: AMR Avatar + Chat Preview */}
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ duration: 0.8, delay: 0.4 }}
                            className="hidden lg:flex flex-col items-center gap-8"
                        >
                            <AMRAvatar />
                            <ChatPreview />
                        </motion.div>
                    </div>
                </div>
            </section>

            {/* Stats Section */}
            <section className="py-16 border-y border-white/5 bg-gradient-to-b from-transparent to-purple-900/5">
                <div className="container mx-auto px-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                        {[
                            { value: 3274, label: "Properties", suffix: "+" },
                            { value: 95, label: "Match Accuracy", suffix: "%" },
                            { value: 24, label: "Response Time", suffix: "h" },
                            { value: 2, label: "Languages", suffix: "" },
                        ].map((stat, idx) => (
                            <motion.div
                                key={idx}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: idx * 0.1 }}
                                className="text-center"
                            >
                                <div className="text-3xl md:text-4xl font-bold text-white mb-1">
                                    <AnimatedNumber value={stat.value} suffix={stat.suffix} />
                                </div>
                                <div className="text-gray-500 text-sm">{stat.label}</div>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section className="py-24 px-4">
                <div className="container mx-auto">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="text-center mb-16"
                    >
                        <h2 className="text-3xl md:text-5xl font-bold mb-4">
                            Why Amr <span className="text-purple-400">Beats</span> the Competition
                        </h2>
                        <p className="text-gray-400 max-w-2xl mx-auto">
                            Powered by a hybrid brain combining GPT-4o&apos;s speed, Claude&apos;s reasoning,
                            and XGBoost&apos;s precision. No other platform comes close.
                        </p>
                    </motion.div>

                    <div className="grid md:grid-cols-3 gap-6">
                        <FeatureCard
                            icon={<Globe className="w-8 h-8 text-purple-400" />}
                            title="Bilingual AI"
                            desc="عمرو بيفهمك - Amr speaks Egyptian Arabic naturally, not formal MSA. First of its kind in real estate."
                            gradient="from-purple-500/20 to-blue-500/20"
                        />
                        <FeatureCard
                            icon={<TrendingUp className="w-8 h-8 text-emerald-400" />}
                            title="Investment Analysis"
                            desc="Real-time ROI calculations, rental yield forecasts, and market trend analysis powered by ML."
                            gradient="from-emerald-500/20 to-teal-500/20"
                        />
                        <FeatureCard
                            icon={<BarChart3 className="w-8 h-8 text-blue-400" />}
                            title="Visual Intelligence"
                            desc="Charts, comparisons, and scorecards. Amr doesn't just talk - he shows you data."
                            gradient="from-blue-500/20 to-cyan-500/20"
                        />
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-24 px-4 relative">
                <div className="absolute inset-0 bg-gradient-to-t from-purple-900/20 to-transparent pointer-events-none" />
                <div className="container mx-auto relative z-10">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        viewport={{ once: true }}
                        className="bg-gradient-to-br from-purple-900/30 to-blue-900/30 rounded-3xl p-12 md:p-16 border border-white/10 backdrop-blur-sm text-center"
                    >
                        <h2 className="text-3xl md:text-5xl font-bold mb-6">
                            Ready to Find Your <span className="text-purple-400">Dream Property</span>?
                        </h2>
                        <p className="text-gray-400 text-lg mb-8 max-w-xl mx-auto">
                            Join thousands of Egyptians who trust Amr for their real estate decisions.
                            Start your journey today - it&apos;s free.
                        </p>
                        <Link
                            href="/chat"
                            className="inline-flex items-center gap-2 px-10 py-5 rounded-full bg-white text-black font-bold text-lg transition-all hover:scale-105 active:scale-95 shadow-2xl shadow-white/20"
                        >
                            <MessageCircle className="w-5 h-5" />
                            Start Chatting with Amr
                            <ArrowRight className="w-5 h-5" />
                        </Link>
                    </motion.div>
                </div>
            </section>

            <Footer />
        </main>
    );
}

function FeatureCard({ icon, title, desc, gradient }: { icon: React.ReactNode; title: string; desc: string; gradient: string }) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            whileHover={{ y: -5, scale: 1.02 }}
            className={`relative p-8 rounded-3xl border border-white/10 bg-gradient-to-br ${gradient} backdrop-blur-sm overflow-hidden group`}
        >
            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative z-10">
                <div className="mb-5 p-3 rounded-2xl bg-white/5 w-fit">{icon}</div>
                <h3 className="text-xl font-bold mb-3 text-white">{title}</h3>
                <p className="text-gray-400 leading-relaxed">{desc}</p>
            </div>
        </motion.div>
    );
}
