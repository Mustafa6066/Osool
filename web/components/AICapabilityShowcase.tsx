"use client";

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, TrendingUp, Building2, Calculator, MapPin, ChevronRight } from 'lucide-react';

const DEMOS = [
    {
        category: 'Price Analysis',
        icon: TrendingUp,
        color: 'emerald',
        question: "What's the average price per sqm in New Capital right now?",
        answer: {
            headline: "New Capital — Price Intelligence Report",
            points: [
                { label: "Average price/sqm", value: "EGP 28,000–35,000", highlight: true },
                { label: "YoY price growth", value: "+22% (2023–2024)" },
                { label: "Best-value zone", value: "R7 & R8 districts" },
                { label: "Premium zone premium", value: "+40% in Downtown District" },
            ],
            insight: "Prices in the New Capital have outpaced Greater Cairo by 2.1× over the past 3 years, driven by government infrastructure investment. Entry-level units in R7 still offer the best risk-adjusted value.",
            confidence: 94,
        },
    },
    {
        category: 'ROI Forecast',
        icon: Calculator,
        color: 'blue',
        question: "If I buy a 120 sqm apartment in Sheikh Zayed for EGP 4.2M, what's my ROI?",
        answer: {
            headline: "ROI Projection — Sheikh Zayed",
            points: [
                { label: "Current market value", value: "EGP 4.2M (fair value)", highlight: true },
                { label: "Projected 5-yr value", value: "EGP 6.8–7.4M (+62%)" },
                { label: "Annual rental yield", value: "7.2% (EGP 302K/yr)" },
                { label: "Break-even (rental)", value: "13.9 years" },
            ],
            insight: "Sheikh Zayed delivers strong rental stability due to proximity to 6th of October industrial zones. For capital appreciation plays, New Capital slightly outperforms, but SZ offers lower vacancy risk.",
            confidence: 89,
        },
    },
    {
        category: 'Developer Audit',
        icon: Building2,
        color: 'violet',
        question: "Is EMAAR Egypt reliable? How do they compare to SODIC on delivery?",
        answer: {
            headline: "Developer Comparison — EMAAR vs. SODIC",
            points: [
                { label: "EMAAR delivery score", value: "91/100 — Excellent", highlight: true },
                { label: "SODIC delivery score", value: "88/100 — Very Good" },
                { label: "EMAAR avg. delay", value: "3.2 months (industry: 8.1)" },
                { label: "SODIC resale premium", value: "+18% above area average" },
            ],
            insight: "EMAAR leads on construction quality and finishing consistency; SODIC excels at community design and resale liquidity. Both carry low counterparty risk. Choose EMAAR for peace-of-mind delivery; SODIC for long-term brand premium.",
            confidence: 97,
        },
    },
    {
        category: 'Area Scout',
        icon: MapPin,
        color: 'amber',
        question: "Which area is best for a 2–5 year flip strategy under EGP 5M?",
        answer: {
            headline: "Top Flip Opportunities — Under EGP 5M",
            points: [
                { label: "#1 pick", value: "New Alamein (Coast)", highlight: true },
                { label: "Projected capital gain", value: "+45–60% by 2027" },
                { label: "#2 pick", value: "6th of October — Smart Village corridor" },
                { label: "Liquidity risk", value: "Low — 3 active buyer pools" },
            ],
            insight: "New Alamein's ongoing resort masterplan and Mediterranean access make it the strongest short-cycle flip market. Entry is still below peak. 6th of October offers better rental yield while you wait.",
            confidence: 91,
        },
    },
];

const COLOR_MAP: Record<string, { badge: string; pill: string; dot: string; tab: string; bar: string }> = {
    emerald: {
        badge: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-600 dark:text-emerald-400',
        pill: 'bg-emerald-500/8 text-emerald-600 dark:text-emerald-400',
        dot: 'bg-emerald-500',
        tab: 'border-emerald-500 text-emerald-600 dark:text-emerald-400',
        bar: 'bg-emerald-500',
    },
    blue: {
        badge: 'bg-blue-500/10 border-blue-500/20 text-blue-600 dark:text-blue-400',
        pill: 'bg-blue-500/8 text-blue-600 dark:text-blue-400',
        dot: 'bg-blue-500',
        tab: 'border-blue-500 text-blue-600 dark:text-blue-400',
        bar: 'bg-blue-500',
    },
    violet: {
        badge: 'bg-violet-500/10 border-violet-500/20 text-violet-600 dark:text-violet-400',
        pill: 'bg-violet-500/8 text-violet-600 dark:text-violet-400',
        dot: 'bg-violet-500',
        tab: 'border-violet-500 text-violet-600 dark:text-violet-400',
        bar: 'bg-violet-500',
    },
    amber: {
        badge: 'bg-amber-500/10 border-amber-500/20 text-amber-600 dark:text-amber-400',
        pill: 'bg-amber-500/8 text-amber-600 dark:text-amber-400',
        dot: 'bg-amber-500',
        tab: 'border-amber-500 text-amber-600 dark:text-amber-400',
        bar: 'bg-amber-500',
    },
};

function TypingText({ text, speed = 18 }: { text: string; speed?: number }) {
    const [displayed, setDisplayed] = useState('');
    const [done, setDone] = useState(false);
    const idx = useRef(0);

    useEffect(() => {
        setDisplayed('');
        setDone(false);
        idx.current = 0;
        const timer = setInterval(() => {
            if (idx.current < text.length) {
                setDisplayed(text.slice(0, idx.current + 1));
                idx.current++;
            } else {
                setDone(true);
                clearInterval(timer);
            }
        }, speed);
        return () => clearInterval(timer);
    }, [text, speed]);

    return (
        <span>
            {displayed}
            {!done && <span className="inline-block w-0.5 h-3.5 bg-current ml-0.5 animate-pulse align-middle" />}
        </span>
    );
}

export default function AICapabilityShowcase() {
    const [active, setActive] = useState(0);
    const [animKey, setAnimKey] = useState(0);
    const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const startAutoAdvance = () => {
        timerRef.current = setInterval(() => {
            setActive(prev => {
                const next = (prev + 1) % DEMOS.length;
                setAnimKey(k => k + 1);
                return next;
            });
        }, 7000);
    };

    useEffect(() => {
        startAutoAdvance();
        return () => { if (timerRef.current) clearInterval(timerRef.current); };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleSelect = (i: number) => {
        if (timerRef.current) clearInterval(timerRef.current);
        setActive(i);
        setAnimKey(k => k + 1);
        startAutoAdvance();
    };

    const demo = DEMOS[active];
    const colors = COLOR_MAP[demo.color];
    const Icon = demo.icon;

    return (
        <section className="py-24 px-4 border-t border-[var(--color-border)]">
            <div className="max-w-5xl mx-auto">
                {/* Header */}
                <div className="flex flex-col gap-3 mb-12 items-center text-center">
                    <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border ${colors.badge} mb-1`}>
                        <Sparkles size={12} />
                        <span className="text-[10px] font-semibold uppercase tracking-widest">AI Capability Showcase</span>
                    </div>
                    <h2 className="text-3xl md:text-4xl font-medium tracking-tight max-w-2xl">
                        The answer quality that changes decisions
                    </h2>
                    <p className="text-[var(--color-text-secondary)] max-w-xl text-[15px] leading-relaxed">
                        Real questions, real intelligence. See how CoInvestor delivers
                        institutional-grade analysis in seconds.
                    </p>
                </div>

                {/* Category Tabs */}
                <div className="flex gap-2 flex-wrap justify-center mb-8">
                    {DEMOS.map((d, i) => {
                        const C = COLOR_MAP[d.color];
                        const DIcon = d.icon;
                        const isActive = i === active;
                        return (
                            <button
                                key={d.category}
                                onClick={() => handleSelect(i)}
                                className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold border transition-all duration-200
                                    ${isActive
                                        ? `${C.tab} bg-[var(--color-surface)] border-current shadow-sm`
                                        : 'border-[var(--color-border)] text-[var(--color-text-muted)] hover:border-[var(--color-border-hover,var(--color-border))] hover:text-[var(--color-text-primary)]'
                                    }`}
                            >
                                <DIcon size={13} />
                                {d.category}
                            </button>
                        );
                    })}
                </div>

                {/* Chat Window */}
                <div className="bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] shadow-xl shadow-black/5 dark:shadow-black/20 overflow-hidden">
                    {/* Window chrome */}
                    <div className="flex items-center gap-2 px-5 py-3 border-b border-[var(--color-border)] bg-[var(--color-background)]">
                        <div className="flex gap-1.5">
                            <div className="w-3 h-3 rounded-full bg-red-400/40" />
                            <div className="w-3 h-3 rounded-full bg-yellow-400/40" />
                            <div className="w-3 h-3 rounded-full bg-emerald-400/40" />
                        </div>
                        <div className="flex-1 flex justify-center">
                            <div className="flex items-center gap-1.5 px-3 py-0.5 bg-[var(--color-surface)] rounded text-[10px] font-mono text-[var(--color-text-muted)] border border-[var(--color-border)]">
                                <span className={`w-1.5 h-1.5 rounded-full ${colors.dot} animate-pulse`} />
                                CoInvestor — {demo.category}
                            </div>
                        </div>
                    </div>

                    <div className="p-5 md:p-8 flex flex-col gap-5 min-h-[420px]">
                        {/* User message */}
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={`q-${animKey}`}
                                initial={{ opacity: 0, y: 12 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -8 }}
                                transition={{ duration: 0.3 }}
                                className="flex justify-end"
                            >
                                <div className="bg-[var(--color-background)] border border-[var(--color-border)] rounded-2xl rounded-br-sm px-4 py-3 text-sm text-[var(--color-text-primary)] max-w-lg shadow-sm">
                                    {demo.question}
                                </div>
                            </motion.div>
                        </AnimatePresence>

                        {/* AI response */}
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={`a-${animKey}`}
                                initial={{ opacity: 0, y: 16 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -8 }}
                                transition={{ duration: 0.35, delay: 0.25 }}
                                className="flex flex-col gap-4"
                            >
                                {/* AI header */}
                                <div className="flex items-center gap-2.5">
                                    <div className={`w-8 h-8 rounded-xl flex items-center justify-center ${colors.pill}`}>
                                        <Icon size={15} />
                                    </div>
                                    <div>
                                        <span className="text-xs font-semibold text-[var(--color-text-primary)]">CoInvestor</span>
                                        <span className="text-[10px] text-[var(--color-text-muted)] ml-2">AI Analysis</span>
                                    </div>
                                </div>

                                {/* Answer card */}
                                <div className="bg-[var(--color-background)] rounded-xl border border-[var(--color-border)] p-5 flex flex-col gap-4">
                                    {/* Headline */}
                                    <div className={`text-xs font-semibold uppercase tracking-wider ${colors.pill.split(' ').filter(c => c.startsWith('text-')).join(' ')}`}>
                                        {demo.answer.headline}
                                    </div>

                                    {/* Data points grid */}
                                    <div className="grid grid-cols-2 gap-2.5">
                                        {demo.answer.points.map((pt, pi) => (
                                            <motion.div
                                                key={pi}
                                                initial={{ opacity: 0, x: -8 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                transition={{ delay: 0.4 + pi * 0.08 }}
                                                className={`rounded-lg p-3 border ${pt.highlight
                                                    ? `${colors.badge} border-current`
                                                    : 'border-[var(--color-border)] bg-[var(--color-surface)]'
                                                    }`}
                                            >
                                                <p className="text-[9px] uppercase tracking-wider text-[var(--color-text-muted)] mb-0.5 font-medium">{pt.label}</p>
                                                <p className={`text-sm font-semibold ${pt.highlight ? '' : 'text-[var(--color-text-primary)]'}`}>{pt.value}</p>
                                            </motion.div>
                                        ))}
                                    </div>

                                    {/* Insight text */}
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        transition={{ delay: 0.85 }}
                                        className="text-sm text-[var(--color-text-secondary)] leading-relaxed border-t border-[var(--color-border)] pt-4"
                                    >
                                        <TypingText key={animKey} text={demo.answer.insight} speed={14} />
                                    </motion.div>

                                    {/* Confidence meter */}
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        transition={{ delay: 1 }}
                                        className="flex items-center gap-3"
                                    >
                                        <span className="text-[10px] text-[var(--color-text-muted)] shrink-0">Data confidence</span>
                                        <div className="flex-1 h-1 bg-[var(--color-border)] rounded-full overflow-hidden">
                                            <motion.div
                                                initial={{ width: 0 }}
                                                animate={{ width: `${demo.answer.confidence}%` }}
                                                transition={{ delay: 1.1, duration: 0.8, ease: 'easeOut' }}
                                                className={`h-full rounded-full ${colors.bar}`}
                                            />
                                        </div>
                                        <span className="text-[10px] font-semibold text-[var(--color-text-primary)] shrink-0">{demo.answer.confidence}%</span>
                                    </motion.div>
                                </div>
                            </motion.div>
                        </AnimatePresence>
                    </div>

                    {/* Footer */}
                    <div className="border-t border-[var(--color-border)] px-5 py-3 flex items-center justify-between bg-[var(--color-background)]">
                        <div className="flex items-center gap-2">
                            {DEMOS.map((d, i) => (
                                <button
                                    key={i}
                                    onClick={() => handleSelect(i)}
                                    title={d.category}
                                    aria-label={`Show ${d.category} example`}
                                    className={`rounded-full transition-all duration-300 ${i === active
                                        ? `w-6 h-1.5 ${colors.bar}`
                                        : 'w-1.5 h-1.5 bg-[var(--color-border)]'
                                        }`}
                                />
                            ))}
                        </div>
                        <a
                            href="/chat"
                            className={`flex items-center gap-1.5 text-xs font-semibold ${colors.tab.split(' ').filter(c => c.startsWith('text-')).join(' ')} hover:opacity-80 transition-opacity`}
                        >
                            Ask your own question
                            <ChevronRight size={13} />
                        </a>
                    </div>
                </div>

                {/* Trust strip */}
                <div className="mt-8 flex flex-wrap justify-center gap-x-8 gap-y-3">
                    {[
                        { label: 'Properties analyzed', value: '3,274+' },
                        { label: 'Data points per answer', value: '200+' },
                        { label: 'Answer accuracy', value: '94%' },
                        { label: 'Response time', value: '< 3 sec' },
                    ].map(item => (
                        <div key={item.label} className="text-center">
                            <div className="text-lg font-semibold text-[var(--color-text-primary)]">{item.value}</div>
                            <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider">{item.label}</div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
