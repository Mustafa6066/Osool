'use client';

import { BarChart2, Percent, Ruler, Footprints, Lightbulb, MessageCircle, Phone, ExternalLink, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface PropertyContext {
    title: string;
    address: string;
    price: string;
    metrics: {
        capRate: string;
        pricePerSqFt: string;
        walkScore: number;
    };
    aiRecommendation: string;
    tags: string[];
    agent?: {
        name: string;
        title: string;
        avatar?: string;
    };
}

interface ContextualPaneProps {
    isOpen?: boolean;
    onClose?: () => void;
    property?: PropertyContext | null;
}

export default function ContextualPane({
    isOpen = true,
    onClose,
    property = {
        title: 'The Harbor View Residence',
        address: '240 Seaport Blvd, Boston, MA',
        price: '$2,450,000',
        metrics: {
            capRate: '4.8%',
            pricePerSqFt: '$1,361',
            walkScore: 98,
        },
        aiRecommendation: 'This property is priced 3% below market value for similar luxury condos in Seaport. High rental yield expected due to tech hub expansion.',
        tags: ['High Appreciation', 'Tech Zone'],
        agent: {
            name: 'Sarah Jenkins',
            title: 'Senior Broker - Elliman',
        },
    },
}: ContextualPaneProps) {
    if (!property) return null;

    const paneContent = (
        <>
            {/* Context Header */}
            <div className="px-5 py-4 border-b border-gray-200 dark:border-[var(--chat-border-dark)] flex justify-between items-center sticky top-0 bg-white/80 dark:bg-[#131d20]/80 backdrop-blur z-10">
                <h2 className="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <BarChart2 size={20} className="text-[var(--chat-primary)] dark:text-[var(--chat-teal-accent)]" />
                    Listing Insights
                </h2>
                <button
                    onClick={onClose}
                    className="text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                >
                    <X size={20} />
                </button>
            </div>

            <div className="p-5 space-y-8">
                {/* Map Module */}
                <div className="space-y-3">
                    <div className="flex justify-between items-center">
                        <h3 className="text-[11px] font-bold text-gray-500 dark:text-[var(--chat-text-secondary)] uppercase tracking-wider">
                            Location
                        </h3>
                        <a href="#" className="text-[11px] text-[var(--chat-primary)] dark:text-[var(--chat-teal-accent)] font-bold hover:underline flex items-center gap-1">
                            View Larger <ExternalLink size={12} />
                        </a>
                    </div>
                    <div className="aspect-[4/3] rounded-xl overflow-hidden relative shadow-md border border-gray-200 dark:border-[var(--chat-border-dark)] bg-slate-100 dark:bg-slate-800 group">
                        {/* Map placeholder with gradient overlay */}
                        <div className="w-full h-full bg-gradient-to-br from-slate-200 to-slate-300 dark:from-slate-700 dark:to-slate-800 transition-transform duration-700 group-hover:scale-110">
                            <div className="absolute inset-0 bg-[var(--chat-primary)]/10 mix-blend-multiply"></div>
                        </div>
                        {/* Map Pin Animation */}
                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                            <div className="relative group/pin cursor-pointer">
                                <div className="w-12 h-12 bg-[var(--chat-primary)]/30 rounded-full animate-ping absolute -top-4 -left-4"></div>
                                <div className="w-4 h-4 bg-[var(--chat-primary)] dark:bg-[var(--chat-teal-accent)] rounded-full border-2 border-white dark:border-[var(--chat-background-dark)] shadow-lg relative z-10"></div>
                            </div>
                        </div>
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-2 bg-gray-50 dark:bg-white/5 p-2 rounded-lg">
                        <Footprints size={16} />
                        <span><span className="font-bold text-gray-900 dark:text-white">0.2 mi</span> from Financial District</span>
                    </p>
                </div>

                {/* Stats Grid */}
                <div>
                    <h3 className="text-[11px] font-bold text-gray-500 dark:text-[var(--chat-text-secondary)] uppercase tracking-wider mb-3">
                        Key Metrics
                    </h3>
                    <div className="grid grid-cols-2 gap-3">
                        <div className="metric-card">
                            <div className="flex items-center gap-1.5 mb-1 text-gray-500 dark:text-[var(--chat-text-secondary)]">
                                <Percent size={16} />
                                <p className="text-[10px] uppercase font-bold">Cap Rate</p>
                            </div>
                            <p className="text-xl font-bold text-gray-900 dark:text-white tracking-tight">{property.metrics.capRate}</p>
                        </div>
                        <div className="metric-card">
                            <div className="flex items-center gap-1.5 mb-1 text-gray-500 dark:text-[var(--chat-text-secondary)]">
                                <Ruler size={16} />
                                <p className="text-[10px] uppercase font-bold">Price / SqFt</p>
                            </div>
                            <p className="text-xl font-bold text-gray-900 dark:text-white tracking-tight">{property.metrics.pricePerSqFt}</p>
                        </div>
                        <div className="metric-card col-span-2">
                            <div className="flex justify-between items-end mb-2">
                                <div className="flex items-center gap-1.5 text-gray-500 dark:text-[var(--chat-text-secondary)]">
                                    <Footprints size={16} />
                                    <p className="text-[10px] uppercase font-bold">Walk Score</p>
                                </div>
                                <span className="text-xl font-bold text-gray-900 dark:text-white">{property.metrics.walkScore}/100</span>
                            </div>
                            <div className="h-2 w-full bg-gray-100 dark:bg-black/40 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-green-400 to-green-600 rounded-full shadow-[0_0_10px_rgba(34,197,94,0.5)]"
                                    style={{ width: `${property.metrics.walkScore}%` }}
                                ></div>
                            </div>
                            <p className="text-[10px] text-gray-400 mt-2 text-right">"Walker's Paradise"</p>
                        </div>
                    </div>
                </div>

                {/* AI Insight Widget */}
                <div className="ai-recommendation-card p-5">
                    <div className="relative z-10">
                        <div className="flex items-center gap-2 mb-3">
                            <div className="size-6 rounded bg-white/20 flex items-center justify-center backdrop-blur-sm">
                                <Lightbulb size={16} />
                            </div>
                            <h3 className="text-sm font-bold">AI Recommendation</h3>
                        </div>
                        <p className="text-sm text-white/90 leading-relaxed font-light mb-4">
                            {property.aiRecommendation}
                        </p>
                        <div className="flex flex-wrap gap-2">
                            {property.tags.map((tag, index) => (
                                <span
                                    key={index}
                                    className="px-2 py-1 bg-white/10 backdrop-blur-md rounded text-[10px] font-medium border border-white/20"
                                >
                                    {tag}
                                </span>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Agent Contact */}
                {property.agent && (
                    <div className="bg-white dark:bg-[var(--chat-surface-dark)] p-4 rounded-xl border border-gray-200 dark:border-[var(--chat-border-dark)] shadow-sm flex items-center gap-3">
                        <div className="size-12 rounded-full bg-gradient-to-br from-[var(--chat-primary)] to-teal-600 flex items-center justify-center text-white font-bold border-2 border-white dark:border-[var(--chat-background-dark)] shadow-sm">
                            {property.agent.name.split(' ').map(n => n[0]).join('')}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-bold text-gray-900 dark:text-white truncate">{property.agent.name}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{property.agent.title}</p>
                        </div>
                        <div className="flex gap-2">
                            <button className="size-8 flex items-center justify-center rounded-full bg-gray-100 dark:bg-white/5 hover:bg-[var(--chat-primary)] hover:text-white dark:hover:bg-[var(--chat-primary)] transition-colors text-gray-600 dark:text-white">
                                <MessageCircle size={18} />
                            </button>
                            <button className="size-8 flex items-center justify-center rounded-full bg-gray-100 dark:bg-white/5 hover:bg-[var(--chat-primary)] hover:text-white dark:hover:bg-[var(--chat-primary)] transition-colors text-gray-600 dark:text-white">
                                <Phone size={18} />
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </>
    );

    return (
        <>
            {/* Desktop Pane */}
            <aside className="chat-contextual-pane bg-white/60 dark:bg-[#131d20] backdrop-blur-md hidden xl:flex flex-col overflow-y-auto z-20 chat-scrollbar">
                {paneContent}
            </aside>

            {/* Mobile Pane Overlay */}
            <AnimatePresence>
                {isOpen && (
                    <>
                        {/* Backdrop - only show on mobile when explicitly opened */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={onClose}
                            className="fixed inset-0 bg-black/50 z-40 xl:hidden hidden"
                        />

                        {/* Mobile Pane */}
                        <motion.aside
                            initial={{ x: 340 }}
                            animate={{ x: 0 }}
                            exit={{ x: 340 }}
                            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                            className="fixed right-0 top-0 h-full w-[340px] bg-white/95 dark:bg-[#131d20] backdrop-blur-md flex flex-col z-50 xl:hidden hidden overflow-y-auto chat-scrollbar"
                        >
                            {paneContent}
                        </motion.aside>
                    </>
                )}
            </AnimatePresence>
        </>
    );
}
