'use client';

import { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import DOMPurify from 'dompurify';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { streamChat } from '@/lib/api';
import ChartVisualization from './ChartVisualization';
import ContextualPane, { PropertyContext } from './chat/ContextualPane';
import ThemeToggle from './ThemeToggle';
import InvitationModal from './InvitationModal';
import { User, LogOut, Gift, PlusCircle, History } from 'lucide-react';

// Utility for Material Symbols
const MaterialIcon = ({ name, className = '', size = '20px' }: { name: string, className?: string, size?: string }) => (
    <span className={`material-symbols-outlined select-none ${className}`} style={{ fontSize: size }}>
        {name}
    </span>
);

/**
 * Sanitize content to prevent XSS attacks.
 */
const sanitizeContent = (content: string): string => {
    if (typeof window === 'undefined') return content;
    return DOMPurify.sanitize(content, {
        ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li', 'code', 'pre', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
        ALLOWED_ATTR: ['href', 'target', 'rel', 'class'],
        ALLOW_DATA_ATTR: false,
    });
};

// --- SVG Synapse Lines Component ---
const SynapseLines = () => (
    <svg className="absolute inset-0 w-full h-full pointer-events-none hidden lg:block z-0" xmlns="http://www.w3.org/2000/svg">
        <path className="synapse-line" d="M 50% 50% C 40% 45%, 30% 45%, 20% 40%" fill="none" opacity="0.6" stroke="url(#gradient-champagne)" strokeWidth="1"></path>
        <path className="synapse-line" d="M 50% 50% C 60% 45%, 70% 35%, 80% 30%" fill="none" opacity="0.6" stroke="url(#gradient-rose)" strokeWidth="1" style={{ animationDelay: '1s' }}></path>
        <path className="synapse-line" d="M 50% 50% C 60% 60%, 70% 65%, 75% 70%" fill="none" opacity="0.5" stroke="url(#gradient-sage)" strokeWidth="1" style={{ animationDelay: '2s' }}></path>
        <path className="synapse-line" d="M 50% 50% C 40% 60%, 30% 70%, 25% 75%" fill="none" opacity="0.4" stroke="url(#gradient-champagne)" strokeWidth="1" style={{ animationDelay: '1.5s' }}></path>
        <defs>
            <linearGradient id="gradient-champagne" x1="0%" x2="100%" y1="0%" y2="0%">
                <stop offset="0%" style={{ stopColor: '#E6D5B8', stopOpacity: 0 }}></stop>
                <stop offset="50%" style={{ stopColor: '#E6D5B8', stopOpacity: 0.8 }}></stop>
                <stop offset="100%" style={{ stopColor: '#E6D5B8', stopOpacity: 0 }}></stop>
            </linearGradient>
            <linearGradient id="gradient-rose" x1="0%" x2="100%" y1="0%" y2="0%">
                <stop offset="0%" style={{ stopColor: '#D4A3A3', stopOpacity: 0 }}></stop>
                <stop offset="50%" style={{ stopColor: '#D4A3A3', stopOpacity: 0.8 }}></stop>
                <stop offset="100%" style={{ stopColor: '#D4A3A3', stopOpacity: 0 }}></stop>
            </linearGradient>
            <linearGradient id="gradient-sage" x1="0%" x2="100%" y1="0%" y2="0%">
                <stop offset="0%" style={{ stopColor: '#A3B18A', stopOpacity: 0 }}></stop>
                <stop offset="50%" style={{ stopColor: '#A3B18A', stopOpacity: 0.8 }}></stop>
                <stop offset="100%" style={{ stopColor: '#A3B18A', stopOpacity: 0 }}></stop>
            </linearGradient>
        </defs>
    </svg>
);

// --- Floating Property Card Component ---
const FloatingPropertyCard = ({ property }: { property?: any }) => {
    // Use provided property or default demo data
    const data = property || {
        title: 'Apartment in El Patio 7',
        location: 'New Cairo',
        price: 18150000,
        bedrooms: 3,
        bathrooms: 3,
        size_sqm: 165,
        rating: 5.0,
        image_url: null
    };

    return (
        <motion.div
            initial={{ opacity: 0, x: -50 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2, duration: 0.8 }}
            className="hidden lg:block absolute left-[10%] top-[25%] w-80 transform transition-transform hover:scale-105 duration-700 z-0 pointer-events-none xl:pointer-events-auto"
        >
            <div className="relative glass-panel rounded-2xl p-5 group hover:border-[var(--color-primary)]/30 transition-colors">
                <div className="absolute -top-[1px] -left-[1px] w-4 h-4 border-t border-l border-[var(--color-primary)]/60 rounded-tl-lg"></div>
                <div className="relative overflow-hidden rounded-xl mb-4 h-44 bg-[var(--color-surface-dark)]/50">
                    {data.image_url ? (
                        <img src={data.image_url} alt={data.title} className="w-full h-full object-cover opacity-90 group-hover:opacity-100 hologram-img" />
                    ) : (
                        <div className="w-full h-full bg-slate-800 relative overflow-hidden">
                            <div className="absolute inset-0 bg-gradient-to-tr from-[var(--color-primary)]/20 to-transparent"></div>
                            <MaterialIcon name="apartment" className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-white/20" size="64px" />
                        </div>
                    )}
                    <div className="absolute top-3 left-3 px-3 py-1 bg-[var(--color-surface-dark)]/40 border border-white/20 text-white text-[10px] font-bold uppercase rounded-md backdrop-blur-md tracking-wider">
                        Top Pick
                    </div>
                </div>
                <div className="space-y-3">
                    <div className="flex justify-between items-start">
                        <div>
                            <h3 className="text-lg font-medium leading-tight text-slate-800 dark:text-slate-100 font-sans">{data.title}</h3>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-display uppercase tracking-wide">{data.location}</p>
                        </div>
                        <div className="flex items-center gap-1 text-[var(--color-tertiary)]">
                            <MaterialIcon name="star" size="14px" className="text-[var(--color-tertiary)]" />
                            <span className="text-sm font-bold">{data.rating || 5.0}</span>
                        </div>
                    </div>
                    <div className="text-2xl font-light text-[var(--color-primary)] font-display">
                        {typeof data.price === 'number' ? data.price.toLocaleString() : data.price} <span className="text-base text-slate-500">EGP</span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 mt-4 pt-4 border-t border-slate-200 dark:border-white/5">
                        <div className="text-center">
                            <MaterialIcon name="bed" className="text-slate-400" size="16px" />
                            <p className="text-xs font-semibold text-slate-600 dark:text-slate-300">{data.bedrooms} Bed</p>
                        </div>
                        <div className="text-center">
                            <MaterialIcon name="bathtub" className="text-slate-400" size="16px" />
                            <p className="text-xs font-semibold text-slate-600 dark:text-slate-300">{data.bathrooms} Bath</p>
                        </div>
                        <div className="text-center">
                            <MaterialIcon name="square_foot" className="text-slate-400" size="16px" />
                            <p className="text-xs font-semibold text-slate-600 dark:text-slate-300">{data.size_sqm}m²</p>
                        </div>
                    </div>
                </div>
                {/* Connector Line (Right) */}
                <div className="absolute top-1/2 -right-16 w-16 h-[1px] bg-gradient-to-r from-white/20 to-transparent"></div>
                <div className="absolute top-1/2 -right-[66px] w-2 h-2 rounded-full bg-white/20 blur-[1px]"></div>
            </div>
        </motion.div>
    );
};

// --- Listing Insights Panel Component ---
const ListingInsightsPanel = ({ property }: { property?: any }) => {
    const capRate = property?.cap_rate || 8;
    const pricePerSqm = property ? Math.round(property.price / property.size_sqm) : 110000;
    const walkScore = property?.walk_score || 85;

    return (
        <motion.div
            initial={{ opacity: 0, x: 50 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4, duration: 0.8 }}
            className="hidden lg:block absolute right-[5%] top-[20%] w-72 transform transition-transform hover:scale-105 duration-700 z-0 pointer-events-none xl:pointer-events-auto"
        >
            <div className="relative glass-panel rounded-2xl p-6 hover:border-[var(--color-secondary)]/30 transition-colors group">
                <div className="absolute -bottom-[1px] -right-[1px] w-4 h-4 border-b border-r border-[var(--color-secondary)]/60 rounded-br-lg"></div>
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400">Listing Insights</h3>
                    <MaterialIcon name="analytics" className="text-[var(--color-secondary)]/70" size="18px" />
                </div>
                <div className="space-y-6">
                    <div>
                        <div className="flex justify-between text-xs text-slate-500 mb-2 font-display uppercase tracking-wider">
                            <span>Cap Rate</span>
                            <span className="text-[var(--color-primary)]">High</span>
                        </div>
                        <div className="text-3xl font-light dark:text-white font-display">{capRate}%</div>
                        <div className="w-full bg-slate-200 dark:bg-white/5 h-1.5 mt-2 rounded-full overflow-hidden">
                            <div className="bg-gradient-to-r from-[var(--color-secondary)] to-[var(--color-primary)] h-full rounded-full opacity-80" style={{ width: `${capRate * 10}%` }}></div>
                        </div>
                    </div>
                    <div>
                        <div className="flex justify-between text-xs text-slate-500 mb-1 font-display uppercase tracking-wider">
                            <span>Price / SQM</span>
                        </div>
                        <div className="text-2xl font-light dark:text-white font-display">{pricePerSqm.toLocaleString()} <span className="text-sm text-slate-500">EGP</span></div>
                    </div>
                    <div>
                        <div className="flex justify-between text-xs text-slate-500 mb-2 font-display uppercase tracking-wider">
                            <span>Walk Score</span>
                            <span className="text-[var(--color-tertiary)] font-bold">{walkScore}/100</span>
                        </div>
                        <div className="h-16 w-full flex items-end gap-1 mt-2">
                            <div className="w-1/6 bg-[var(--color-secondary)] h-[40%] rounded-t-sm opacity-20"></div>
                            <div className="w-1/6 bg-[var(--color-secondary)] h-[60%] rounded-t-sm opacity-30"></div>
                            <div className="w-1/6 bg-[var(--color-secondary)] h-[30%] rounded-t-sm opacity-40"></div>
                            <div className="w-1/6 bg-[var(--color-primary)] h-[80%] rounded-t-sm opacity-50"></div>
                            <div className="w-1/6 bg-[var(--color-primary)] h-[90%] rounded-t-sm opacity-70"></div>
                            <div className="w-1/6 bg-[var(--color-primary)] h-[50%] rounded-t-sm opacity-90"></div>
                        </div>
                    </div>
                </div>
                <div className="absolute top-1/2 -left-16 w-16 h-[1px] bg-gradient-to-l from-white/20 to-transparent"></div>
            </div>
        </motion.div>
    );
};

// --- ROI Panel Component ---
const ROIPanel = ({ roi }: { roi?: number }) => (
    <motion.div
        initial={{ opacity: 0, y: 50 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6, duration: 0.8 }}
        className="hidden lg:block absolute right-[15%] bottom-[15%] w-64 transform transition-transform hover:scale-105 duration-700 z-0 pointer-events-none xl:pointer-events-auto"
    >
        <div className="relative glass-panel rounded-2xl p-5 hover:border-[var(--color-primary)]/40 transition-colors">
            <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-bold tracking-widest uppercase text-slate-400">Proj. Annual ROI</span>
                <MaterialIcon name="trending_up" className="text-[var(--color-primary)] text-sm" />
            </div>
            <div className="text-3xl font-light text-[var(--color-primary)] font-display">{roi || 12.5}%</div>
            <p className="text-[10px] text-slate-500 mt-2 leading-tight">Based on recent market trends in New Cairo.</p>
            {/* Connector Line (Top) */}
            <div className="absolute -top-12 left-1/2 w-[1px] h-12 bg-gradient-to-b from-transparent to-white/20"></div>
        </div>
    </motion.div>
);

// --- Floating Control Buttons ---
const FloatingControls = () => (
    <div className="hidden lg:flex absolute left-8 bottom-24 flex-col gap-3 z-50">
        <button className="w-11 h-11 rounded-xl bg-white/5 dark:bg-[var(--color-surface-dark)]/50 border border-slate-200 dark:border-white/10 text-slate-500 dark:text-slate-400 backdrop-blur-md flex items-center justify-center hover:bg-[var(--color-primary)]/20 hover:text-[var(--color-primary)] hover:border-[var(--color-primary)]/30 transition-all shadow-lg">
            <MaterialIcon name="add" className="text-xl" />
        </button>
        <button className="w-11 h-11 rounded-xl bg-white/5 dark:bg-[var(--color-surface-dark)]/50 border border-slate-200 dark:border-white/10 text-slate-500 dark:text-slate-400 backdrop-blur-md flex items-center justify-center hover:bg-[var(--color-primary)]/20 hover:text-[var(--color-primary)] hover:border-[var(--color-primary)]/30 transition-all shadow-lg">
            <MaterialIcon name="remove" className="text-xl" />
        </button>
        <button className="w-11 h-11 rounded-xl bg-white/5 dark:bg-[var(--color-surface-dark)]/50 border border-slate-200 dark:border-white/10 text-slate-500 dark:text-slate-400 backdrop-blur-md flex items-center justify-center hover:bg-[var(--color-primary)]/20 hover:text-[var(--color-primary)] hover:border-[var(--color-primary)]/30 transition-all shadow-lg">
            <MaterialIcon name="my_location" className="text-xl" />
        </button>
    </div>
);

// --- Main Chat Interface ---
export default function ChatInterface() {
    const { user, isAuthenticated, logout } = useAuth();
    const { language } = useLanguage();
    const [messages, setMessages] = useState<any[]>([]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [selectedProperty, setSelectedProperty] = useState<PropertyContext | null>(null);
    const [currentProperty, setCurrentProperty] = useState<any>(null); // For floating cards
    const [sessionId, setSessionId] = useState(() => `session-${Date.now()}`);
    const [isUserMenuOpen, setUserMenuOpen] = useState(false);
    const [isInvitationModalOpen, setInvitationModalOpen] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Get the latest AI message content and properties
    const latestAiMessage = useMemo(() => {
        const aiMessages = messages.filter(m => m.role === 'amr');
        return aiMessages.length > 0 ? aiMessages[aiMessages.length - 1] : null;
    }, [messages]);

    const displayProperty = currentProperty || latestAiMessage?.properties?.[0] || null;

    // Adapt backend property model to UI Context model
    const handleSelectProperty = (prop: any) => {
        setCurrentProperty(prop);
        setSelectedProperty({
            title: prop.title,
            address: prop.location,
            price: `${prop.price.toLocaleString()} EGP`,
            metrics: {
                bedrooms: prop.bedrooms,
                size: prop.size_sqm,
                wolfScore: prop.wolf_score || 75,
                capRate: "8%",
                pricePerSqFt: `${Math.round(prop.price / prop.size_sqm).toLocaleString()}`
            },
            aiRecommendation: prop.aiRecommendation || "This property shows strong appreciation potential based on recent market trends.",
            tags: ["High Growth", "Value Pick"],
            agent: {
                name: "Amr The Agent",
                title: "Senior Consultant"
            }
        });
    };

    // Auto-scroll
    useEffect(() => {
        if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }, [messages, isTyping]);

    const handleSend = async () => {
        if (!input.trim() || isTyping) return;
        const userMsg = { role: 'user', content: input, id: Date.now().toString() };
        setMessages((prev) => [...prev, userMsg]);
        setInput('');
        setIsTyping(true);

        const aiMsgId = (Date.now() + 1).toString();
        setMessages((prev) => [...prev, { role: 'amr', content: '', id: aiMsgId, isTyping: true }]);

        let fullResponse = '';
        try {
            await streamChat(userMsg.content, sessionId, {
                onToken: (token) => {
                    fullResponse += token;
                    setMessages((prev) => prev.map((m) => (m.id === aiMsgId ? { ...m, content: fullResponse } : m)));
                },
                onToolStart: () => { },
                onToolEnd: () => { },
                onComplete: (data) => {
                    setMessages((prev) => prev.map((m) => m.id === aiMsgId ? { ...m, content: fullResponse, properties: data.properties, visualizations: data.ui_actions, isTyping: false } : m));
                    // Auto-select first property for floating cards
                    if (data.properties && data.properties.length > 0) {
                        handleSelectProperty(data.properties[0]);
                    }
                    setIsTyping(false);
                },
                onError: (err) => {
                    setMessages((prev) => prev.map((m) => m.id === aiMsgId ? { ...m, content: fullResponse + '\n\n[Error]', isTyping: false } : m));
                    setIsTyping(false);
                }
            }, language === 'ar' ? 'ar' : 'auto');
        } catch (e) { setIsTyping(false); }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const getUserName = (): string => {
        if (user?.full_name) return user.full_name;
        if (user?.email) return user.email.split('@')[0];
        return 'Mustafa';
    };

    const handleNewSession = () => {
        setMessages([]);
        setSelectedProperty(null);
        setCurrentProperty(null);
        setInput('');
        setIsTyping(false);
        setSessionId(`session-${Date.now()}`);
    };

    // Get display content - either latest AI message or welcome message
    const getDisplayContent = () => {
        if (latestAiMessage) {
            return sanitizeContent(latestAiMessage.content || '');
        }
        return null;
    };

    const displayContent = getDisplayContent();
    const showProcessing = isTyping || (latestAiMessage?.isTyping);

    return (
        <div className="bg-[var(--color-background)] dark:bg-[var(--color-background-dark)] text-slate-700 dark:text-[var(--color-text-off-white)] font-sans transition-colors duration-500 overflow-hidden h-screen w-screen relative selection:bg-[var(--color-primary)] selection:text-white">
            {/* Grid Background */}
            <div className="absolute inset-0 z-0 pointer-events-none opacity-40 dark:opacity-100 bg-grid-light dark:bg-grid-dark grid-bg"></div>
            <div className="absolute inset-0 z-0 bg-gradient-to-b from-[var(--color-background-light)]/50 via-transparent to-[var(--color-background-light)]/80 dark:from-[var(--color-background-dark)]/50 dark:via-transparent dark:to-[var(--color-background-dark)]/90 pointer-events-none"></div>

            {/* Navigation Bar */}
            <nav className="absolute top-0 left-0 w-full z-50 p-8 flex justify-between items-center">
                <div className="flex items-center gap-3">
                    <Link href="/" className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full border border-[var(--color-primary)]/30 bg-[var(--color-primary)]/10 flex items-center justify-center backdrop-blur-md">
                            <MaterialIcon name="hub" className="text-[var(--color-primary)]" size="18px" />
                        </div>
                        <span className="text-xl font-display font-medium tracking-widest uppercase text-slate-800 dark:text-gray-200">
                            Osool<span className="text-[var(--color-primary)] font-bold">AI</span>
                        </span>
                    </Link>
                </div>
                <div className="flex gap-4">
                    <ThemeToggle />
                    <Link
                        href="/dashboard"
                        className="px-5 py-2 rounded-full border border-slate-300 dark:border-white/10 text-sm hover:bg-white/5 transition text-slate-600 dark:text-slate-300 font-display tracking-wide flex items-center gap-2"
                    >
                        <History size={16} />
                        <span className="hidden sm:inline">History</span>
                    </Link>
                    <button
                        onClick={handleNewSession}
                        className="px-5 py-2 rounded-full bg-slate-800 dark:bg-white/10 text-white dark:text-[var(--color-tertiary)] border border-transparent dark:border-[var(--color-tertiary)]/20 text-sm font-medium tracking-wide hover:bg-slate-700 dark:hover:bg-white/20 transition shadow-lg shadow-black/10 flex items-center gap-2"
                    >
                        <PlusCircle size={16} />
                        <span className="hidden sm:inline">New Session</span>
                    </button>
                    {/* User Menu (if authenticated) */}
                    {isAuthenticated && (
                        <div className="relative">
                            <button
                                onClick={() => setUserMenuOpen(!isUserMenuOpen)}
                                className="w-10 h-10 rounded-full border border-slate-300 dark:border-white/10 hover:bg-white/5 transition text-slate-600 dark:text-slate-300 backdrop-blur-sm bg-white/5 flex items-center justify-center"
                            >
                                <User size={18} />
                            </button>

                            {/* Dropdown */}
                            <AnimatePresence>
                                {isUserMenuOpen && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                        animate={{ opacity: 1, y: 0, scale: 1 }}
                                        exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                        className="absolute right-0 mt-2 w-56 rounded-xl bg-[var(--color-surface)] dark:bg-[var(--color-surface-dark)] border border-[var(--color-border)] shadow-xl overflow-hidden z-[60]"
                                    >
                                        <div className="p-3 border-b border-[var(--color-border)]">
                                            <p className="text-sm font-medium text-[var(--color-text-primary)]">{user?.full_name || 'User'}</p>
                                            <p className="text-xs text-[var(--color-text-muted)]">{user?.email}</p>
                                        </div>
                                        <div className="p-2 space-y-1">
                                            <button
                                                onClick={() => setInvitationModalOpen(true)}
                                                className="flex items-center gap-2 w-full px-3 py-2 text-sm rounded-lg hover:bg-[var(--color-background-light)] dark:hover:bg-white/5 transition-colors text-green-600"
                                            >
                                                <Gift size={16} />
                                                Invite Friends
                                            </button>
                                            <div className="h-px bg-[var(--color-border)] my-1"></div>
                                            <button
                                                onClick={() => logout()}
                                                className="flex items-center gap-2 w-full px-3 py-2 text-sm rounded-lg hover:bg-red-50 dark:hover:bg-red-900/10 transition-colors text-red-500"
                                            >
                                                <LogOut size={16} />
                                                Sign Out
                                            </button>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    )}
                </div>
            </nav>

            {/* Main Content Area */}
            <main className="relative z-10 w-full h-full flex items-center justify-center">
                {/* SVG Synapse Lines */}
                <SynapseLines />

                {/* Left: Floating Property Card (Always visible) */}
                <FloatingPropertyCard property={displayProperty} />

                {/* Right: Listing Insights Panel (Always visible) */}
                <ListingInsightsPanel property={displayProperty} />

                {/* Bottom Right: ROI Panel (Always visible) */}
                <ROIPanel roi={displayProperty?.roi || 12.5} />

                {/* Bottom Left: Control Buttons */}
                <FloatingControls />

                {/* Center: Main Content Panel */}
                <div className="relative z-20 w-full max-w-2xl mx-4 lg:mx-0 transform transition-all duration-700">
                    <div className="absolute -inset-1 bg-gradient-to-r from-[var(--color-primary)]/20 via-[var(--color-tertiary)]/10 to-[var(--color-secondary)]/20 rounded-3xl blur-xl opacity-30 dark:opacity-40 animate-pulse"></div>
                    <div className="relative glass-panel bg-white/80 dark:bg-[var(--color-surface-dark)]/40 rounded-2xl p-6 lg:p-10 shadow-soft-glow max-h-[60vh] overflow-y-auto no-scrollbar">
                        {/* Header */}
                        <div className="flex items-center gap-4 mb-8 border-b border-slate-200 dark:border-white/5 pb-6">
                            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[var(--color-primary)]/20 to-[var(--color-surface-dark)] border border-[var(--color-primary)]/20 flex items-center justify-center">
                                <MaterialIcon name="auto_awesome" className="text-[var(--color-primary)] font-light" />
                            </div>
                            <div>
                                <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-slate-400 dark:text-slate-400 mb-1">Agentic Core</h2>
                                <span className="text-sm text-[var(--color-primary)]/80 font-display flex items-center gap-2">
                                    {showProcessing ? 'Processing Market Data' : 'Analysis Complete'}
                                    {showProcessing && (
                                        <span className="flex space-x-1">
                                            <span className="w-1 h-1 bg-[var(--color-primary)] rounded-full animate-bounce" style={{ animationDelay: '0s' }}></span>
                                            <span className="w-1 h-1 bg-[var(--color-primary)] rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                                            <span className="w-1 h-1 bg-[var(--color-primary)] rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
                                        </span>
                                    )}
                                </span>
                            </div>
                        </div>

                        {/* Content */}
                        <div className="text-right font-sans text-lg leading-loose text-slate-700 dark:text-[var(--color-text-off-white)] space-y-6" dir="rtl">
                            {displayContent ? (
                                <div className="prose dark:prose-invert max-w-none">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {displayContent}
                                    </ReactMarkdown>
                                </div>
                            ) : (
                                <>
                                    <p className="text-slate-900 dark:text-white font-medium">
                                        أهلاً بيك يا {getUserName()}! التجمع الخامس اختيار ممتاز.
                                    </p>
                                    <p className="text-slate-600 dark:text-gray-300 font-light">
                                        بص، متوسط أسعار الشقق في التجمع الخامس بيبدأ من <span className="text-[var(--color-tertiary)] font-bold px-1">5.4</span> مليون جنيه لحد <span className="text-[var(--color-tertiary)] font-bold px-1">18.1</span> مليون جنيه. الفرق ده بيكون حسب المطور والموقع.
                                    </p>
                                    <div className="p-4 bg-[var(--color-primary)]/5 border border-[var(--color-primary)]/10 rounded-xl relative overflow-hidden group">
                                        <div className="absolute top-0 right-0 w-1 h-full bg-[var(--color-primary)]/40"></div>
                                        <p className="text-slate-700 dark:text-gray-200">
                                            من الخيارات اللي عندي دلوقتي، في شقة في مشروع <span className="font-bold text-[var(--color-primary)]">السراي</span> بسعر 5.38 مليون جنيه، مساحتها 81 متر مربع، 1 نوم و2 حمام. الشقة دي الـ AI بتاعي قيمها بـ 50 على 100، يعني لقطة.
                                        </p>
                                    </div>
                                    <p className="text-sm text-slate-500 dark:text-slate-500 mt-6 font-display tracking-wide">
                                        تحب نحجز ميعاد معاينة للشقة دي يا {getUserName()}؟ عشان تشوفها على الطبيعة وأقدر أجبلك تفاصيل القسط الشهري.
                                    </p>
                                </>
                            )}
                        </div>

                        {/* Action Buttons */}
                        <div className="mt-8 flex flex-wrap gap-4 justify-end" dir="rtl">
                            <button className="px-5 py-2.5 bg-slate-100 dark:bg-white/5 hover:bg-slate-200 dark:hover:bg-white/10 border border-transparent dark:border-white/5 rounded-xl text-sm text-slate-600 dark:text-slate-300 transition-all flex items-center gap-2 shadow-sm">
                                <MaterialIcon name="calendar_today" size="18px" />
                                حجز معاينة
                            </button>
                            <button className="px-5 py-2.5 bg-[var(--color-primary)]/10 border border-[var(--color-primary)]/30 text-[var(--color-primary)] hover:bg-[var(--color-primary)]/20 rounded-xl text-sm transition-all flex items-center gap-2 shadow-sm">
                                <MaterialIcon name="visibility" size="18px" />
                                عرض التفاصيل
                            </button>
                        </div>
                    </div>
                </div>
            </main>

            {/* Floating Input Area (Pill Design) */}
            <div className="absolute bottom-10 left-1/2 -translate-x-1/2 w-full max-w-2xl px-6 z-50">
                <div className="relative group">
                    <div className="absolute -inset-1 bg-gradient-to-r from-[var(--color-primary)]/30 via-[var(--color-tertiary)]/20 to-[var(--color-secondary)]/30 rounded-full blur-xl opacity-20 group-hover:opacity-40 transition duration-700"></div>
                    <div className="relative flex items-center bg-white dark:bg-[var(--color-surface-dark)]/80 backdrop-blur-xl border border-slate-200 dark:border-white/10 rounded-full shadow-2xl overflow-hidden transition-colors hover:border-[var(--color-primary)]/20">
                        {/* Add Button */}
                        <button className="pl-5 pr-3 text-slate-400 hover:text-[var(--color-primary)] transition">
                            <MaterialIcon name="add_circle" />
                        </button>

                        {/* Text Input */}
                        <input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            className="w-full py-4 bg-transparent border-none focus:ring-0 text-slate-700 dark:text-gray-200 placeholder-slate-400 font-sans text-base tracking-wide"
                            placeholder="Ask about properties, market trends..."
                            type="text"
                            disabled={isTyping}
                        />

                        {/* Mic Button */}
                        <button className="p-3 text-slate-400 hover:text-[var(--color-primary)] transition">
                            <MaterialIcon name="mic" />
                        </button>

                        {/* Send Button */}
                        <button
                            onClick={handleSend}
                            disabled={!input.trim() || isTyping}
                            className="mr-2 p-2.5 bg-slate-100 dark:bg-white/10 rounded-full text-slate-500 dark:text-[var(--color-tertiary)] hover:bg-[var(--color-primary)] hover:text-white dark:hover:bg-[var(--color-primary)] dark:hover:text-white transition shadow-inner disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <MaterialIcon name="arrow_upward" className="text-lg" />
                        </button>
                    </div>
                    <div className="text-center mt-3">
                        <p className="text-[10px] text-slate-400 dark:text-slate-500 tracking-widest uppercase font-display opacity-70">AI insights require independent verification</p>
                    </div>
                </div>
            </div>

            {/* Right Contextual Pane (Slide-over) */}
            <ContextualPane
                isOpen={!!selectedProperty}
                onClose={() => setSelectedProperty(null)}
                property={selectedProperty}
                isRTL={language === 'ar'}
            />

            {/* Invitation Modal */}
            <InvitationModal
                isOpen={isInvitationModalOpen}
                onClose={() => setInvitationModalOpen(false)}
            />
        </div>
    );
}
