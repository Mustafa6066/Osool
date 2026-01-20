'use client';

import { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import DOMPurify from 'dompurify';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useTheme } from '@/contexts/ThemeContext';
import { streamChat } from '@/lib/api';
import ChartVisualization from './ChartVisualization';
import ContextualPane, { PropertyContext } from './chat/ContextualPane';
import InvitationModal from './InvitationModal';
import { User, LogOut, Gift, PlusCircle, History, Moon, Sun } from 'lucide-react';

// Utility for Material Symbols
const MaterialIcon = ({ name, className = '', size = '20px' }: { name: string, className?: string, size?: string }) => (
    <span className={`material-symbols-outlined select-none ${className}`} style={{ fontSize: size }}>
        {name}
    </span>
);

const sanitizeContent = (content: string): string => {
    if (typeof window === 'undefined') return content;
    return DOMPurify.sanitize(content, {
        ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li', 'code', 'pre', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
        ALLOWED_ATTR: ['href', 'target', 'rel', 'class'],
        ALLOW_DATA_ATTR: false,
    });
};

// --- SVG Synapse Lines ---
const SynapseLines = () => (
    <svg className="absolute inset-0 w-full h-full pointer-events-none hidden lg:block z-0" xmlns="http://www.w3.org/2000/svg">
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
        <path className="synapse-line" d="M 50% 50% C 40% 45%, 30% 45%, 20% 40%" fill="none" opacity="0.6" stroke="url(#gradient-champagne)" strokeWidth="1"></path>
        <path className="synapse-line" d="M 50% 50% C 60% 45%, 70% 35%, 80% 30%" fill="none" opacity="0.6" stroke="url(#gradient-rose)" strokeWidth="1" style={{ animationDelay: '1s' }}></path>
        <path className="synapse-line" d="M 50% 50% C 60% 60%, 70% 65%, 75% 70%" fill="none" opacity="0.5" stroke="url(#gradient-sage)" strokeWidth="1" style={{ animationDelay: '2s' }}></path>
        <path className="synapse-line" d="M 50% 50% C 40% 60%, 30% 70%, 25% 75%" fill="none" opacity="0.4" stroke="url(#gradient-champagne)" strokeWidth="1" style={{ animationDelay: '1.5s' }}></path>
    </svg>
);

// --- Property Card Component ---
const PropertyCard = ({ property, index = 0 }: { property: any, index?: number }) => {
    const topOffset = 18 + (index * 28);

    return (
        <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 + (index * 0.15), duration: 0.8 }}
            className="hidden lg:block absolute w-72 transform transition-transform hover:scale-105 duration-700 z-10"
            style={{ left: '2%', top: `${topOffset}%` }}
        >
            <div className="relative glass-panel rounded-2xl p-4 group hover:border-[#A3B18A]/30 transition-colors bg-white/90 dark:bg-[#1C212B]/90 border border-slate-200 dark:border-white/10">
                <div className="absolute -top-[1px] -left-[1px] w-4 h-4 border-t border-l border-[#A3B18A]/60 rounded-tl-lg"></div>

                {/* Image */}
                <div className="relative overflow-hidden rounded-xl mb-3 h-28 bg-slate-200 dark:bg-[#1C212B]/50">
                    {property.image_url ? (
                        <img src={property.image_url} alt={property.title} className="w-full h-full object-cover opacity-90 group-hover:opacity-100 hologram-img" />
                    ) : (
                        <div className="w-full h-full bg-slate-300 dark:bg-slate-800 relative overflow-hidden">
                            <div className="absolute inset-0 bg-gradient-to-tr from-[#A3B18A]/20 to-transparent"></div>
                            <MaterialIcon name="apartment" className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-slate-400 dark:text-white/20" size="40px" />
                        </div>
                    )}
                    <div className="absolute top-2 left-2 px-2 py-0.5 bg-[#1C212B]/60 border border-white/20 text-white text-[8px] font-bold uppercase rounded backdrop-blur-md tracking-wider">
                        Top Pick
                    </div>
                </div>

                {/* Content */}
                <div className="space-y-2">
                    <div className="flex justify-between items-start">
                        <div>
                            <h3 className="text-sm font-medium leading-tight text-slate-800 dark:text-slate-100 font-sans">{property.title}</h3>
                            <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5 font-display uppercase tracking-wide">{property.location}</p>
                        </div>
                        <div className="flex items-center gap-0.5 text-[#E6D5B8]">
                            <MaterialIcon name="star" size="12px" />
                            <span className="text-xs font-bold">{property.rating || 5}</span>
                        </div>
                    </div>
                    <div className="text-lg font-light text-[#A3B18A] font-display">
                        {typeof property.price === 'number' ? property.price.toLocaleString() : property.price} <span className="text-[10px] text-slate-500">EGP</span>
                    </div>
                    <div className="grid grid-cols-3 gap-1 pt-2 border-t border-slate-200 dark:border-white/5">
                        <div className="text-center">
                            <MaterialIcon name="bed" className="text-slate-400" size="12px" />
                            <p className="text-[9px] font-semibold text-slate-600 dark:text-slate-300">{property.bedrooms} Bed</p>
                        </div>
                        <div className="text-center">
                            <MaterialIcon name="bathtub" className="text-slate-400" size="12px" />
                            <p className="text-[9px] font-semibold text-slate-600 dark:text-slate-300">{property.bathrooms} Bath</p>
                        </div>
                        <div className="text-center">
                            <MaterialIcon name="square_foot" className="text-slate-400" size="12px" />
                            <p className="text-[9px] font-semibold text-slate-600 dark:text-slate-300">{property.size_sqm}m²</p>
                        </div>
                    </div>
                </div>

                {/* Connector */}
                <div className="absolute top-1/2 -right-10 w-10 h-[1px] bg-gradient-to-r from-slate-300 dark:from-white/20 to-transparent"></div>
                <div className="absolute top-1/2 -right-[42px] w-1.5 h-1.5 rounded-full bg-slate-300 dark:bg-white/20"></div>
            </div>
        </motion.div>
    );
};

// --- Listing Insights Panel ---
const ListingInsightsPanel = ({ property }: { property?: any }) => {
    const capRate = property?.cap_rate || 8;
    const pricePerSqm = property ? Math.round(property.price / property.size_sqm) : 110000;
    const walkScore = property?.walk_score || 85;

    return (
        <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4, duration: 0.8 }}
            className="hidden lg:block absolute right-[2%] top-[16%] w-64 z-10"
        >
            <div className="relative glass-panel rounded-2xl p-5 hover:border-[#D4A3A3]/30 transition-colors bg-white/90 dark:bg-[#1C212B]/90 border border-slate-200 dark:border-white/10">
                <div className="absolute -bottom-[1px] -right-[1px] w-3 h-3 border-b border-r border-[#D4A3A3]/60 rounded-br-lg"></div>

                <div className="flex justify-between items-center mb-5">
                    <h3 className="text-[10px] font-bold uppercase tracking-widest text-slate-500 dark:text-slate-400">Listing Insights</h3>
                    <MaterialIcon name="analytics" className="text-[#D4A3A3]/70" size="16px" />
                </div>

                <div className="space-y-5">
                    {/* Cap Rate */}
                    <div>
                        <div className="flex justify-between text-[10px] text-slate-500 dark:text-slate-400 mb-1.5 font-display uppercase tracking-wider">
                            <span>Cap Rate</span>
                            <span className="text-[#A3B18A] font-semibold">High</span>
                        </div>
                        <div className="text-2xl font-light text-slate-800 dark:text-white font-display">{capRate}%</div>
                        <div className="w-full bg-slate-200 dark:bg-white/10 h-1.5 mt-2 rounded-full overflow-hidden">
                            <div className="bg-gradient-to-r from-[#D4A3A3] to-[#A3B18A] h-full rounded-full opacity-80" style={{ width: `${capRate * 10}%` }}></div>
                        </div>
                    </div>

                    {/* Price/SQM */}
                    <div>
                        <div className="text-[10px] text-slate-500 dark:text-slate-400 mb-1.5 font-display uppercase tracking-wider">
                            Price / SQM
                        </div>
                        <div className="text-xl font-light text-slate-800 dark:text-white font-display">
                            {pricePerSqm.toLocaleString()} <span className="text-[10px] text-slate-500">EGP</span>
                        </div>
                    </div>

                    {/* Walk Score */}
                    <div>
                        <div className="flex justify-between text-[10px] text-slate-500 dark:text-slate-400 mb-1.5 font-display uppercase tracking-wider">
                            <span>Walk Score</span>
                            <span className="text-[#E6D5B8] font-bold">{walkScore}/100</span>
                        </div>
                        <div className="h-14 w-full flex items-end gap-1">
                            <div className="flex-1 bg-[#D4A3A3] h-[40%] rounded-t opacity-30"></div>
                            <div className="flex-1 bg-[#D4A3A3] h-[60%] rounded-t opacity-40"></div>
                            <div className="flex-1 bg-[#D4A3A3] h-[30%] rounded-t opacity-50"></div>
                            <div className="flex-1 bg-[#A3B18A] h-[80%] rounded-t opacity-60"></div>
                            <div className="flex-1 bg-[#A3B18A] h-[90%] rounded-t opacity-80"></div>
                            <div className="flex-1 bg-[#A3B18A] h-[50%] rounded-t opacity-100"></div>
                        </div>
                    </div>
                </div>

                <div className="absolute top-1/2 -left-10 w-10 h-[1px] bg-gradient-to-l from-slate-300 dark:from-white/20 to-transparent"></div>
            </div>
        </motion.div>
    );
};

// --- ROI Panel ---
const ROIPanel = ({ roi = 12.5 }: { roi?: number }) => (
    <motion.div
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6, duration: 0.8 }}
        className="hidden lg:block absolute right-[10%] bottom-[16%] w-52 z-10"
    >
        <div className="relative glass-panel rounded-2xl p-4 hover:border-[#A3B18A]/40 transition-colors bg-white/90 dark:bg-[#1C212B]/90 border border-slate-200 dark:border-white/10">
            <div className="flex items-center justify-between mb-2">
                <span className="text-[9px] font-bold tracking-widest uppercase text-slate-500 dark:text-slate-400">Proj. Annual ROI</span>
                <MaterialIcon name="trending_up" className="text-[#A3B18A]" size="14px" />
            </div>
            <div className="text-2xl font-light text-[#A3B18A] font-display">{roi}%</div>
            <p className="text-[9px] text-slate-500 dark:text-slate-400 mt-1">Based on recent market trends in New Cairo.</p>
            <div className="absolute -top-8 left-1/2 w-[1px] h-8 bg-gradient-to-b from-transparent to-slate-300 dark:to-white/20"></div>
        </div>
    </motion.div>
);

// --- Floating Controls ---
const FloatingControls = () => (
    <div className="hidden lg:flex absolute left-6 bottom-28 flex-col gap-2 z-50">
        {['add', 'remove', 'my_location'].map((icon) => (
            <button key={icon} className="w-10 h-10 rounded-xl bg-white/80 dark:bg-[#1C212B]/50 border border-slate-200 dark:border-white/10 text-slate-500 dark:text-slate-400 backdrop-blur-md flex items-center justify-center hover:bg-[#A3B18A]/20 hover:text-[#A3B18A] hover:border-[#A3B18A]/30 transition-all shadow-lg">
                <MaterialIcon name={icon} size="18px" />
            </button>
        ))}
    </div>
);

// --- Main Chat Interface ---
export default function ChatInterface() {
    const { user, isAuthenticated, logout } = useAuth();
    const { language } = useLanguage();
    const { theme, toggleTheme } = useTheme();
    const [messages, setMessages] = useState<any[]>([]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [selectedProperty, setSelectedProperty] = useState<PropertyContext | null>(null);
    const [displayProperties, setDisplayProperties] = useState<any[]>([]);
    const [visualizations, setVisualizations] = useState<any[]>([]);
    const [sessionId, setSessionId] = useState(() => `session-${Date.now()}`);
    const [isUserMenuOpen, setUserMenuOpen] = useState(false);
    const [isInvitationModalOpen, setInvitationModalOpen] = useState(false);

    // Default properties
    const defaultProperties = [
        { title: 'Apartment in Sarai', location: 'New Cairo', price: 5380970, bedrooms: 1, bathrooms: 2, size_sqm: 81, rating: 5 },
        { title: 'Apartment in Sarai', location: 'New Cairo', price: 7532757, bedrooms: 2, bathrooms: 2, size_sqm: 112, rating: 5 }
    ];

    const propertiesToShow = displayProperties.length > 0 ? displayProperties : defaultProperties;

    const latestAiMessage = useMemo(() => {
        const aiMessages = messages.filter(m => m.role === 'amr');
        return aiMessages.length > 0 ? aiMessages[aiMessages.length - 1] : null;
    }, [messages]);

    const handleSelectProperty = (prop: any) => {
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
            aiRecommendation: "Strong appreciation potential based on market trends.",
            tags: ["High Growth", "Value Pick"],
            agent: { name: "Amr The Agent", title: "Senior Consultant" }
        });
    };

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
                    if (data.properties?.length > 0) {
                        setDisplayProperties(data.properties.slice(0, 3));
                        handleSelectProperty(data.properties[0]);
                    }
                    if (data.ui_actions?.length > 0) {
                        setVisualizations(data.ui_actions);
                    }
                    setIsTyping(false);
                },
                onError: () => {
                    setMessages((prev) => prev.map((m) => m.id === aiMsgId ? { ...m, content: fullResponse + '\n\n[Error]', isTyping: false } : m));
                    setIsTyping(false);
                }
            }, language === 'ar' ? 'ar' : 'auto');
        } catch (e) { setIsTyping(false); }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
    };

    const getUserName = (): string => user?.full_name || user?.email?.split('@')[0] || 'Mustafa';

    const handleNewSession = () => {
        setMessages([]);
        setSelectedProperty(null);
        setDisplayProperties([]);
        setVisualizations([]);
        setInput('');
        setIsTyping(false);
        setSessionId(`session-${Date.now()}`);
    };

    const displayContent = latestAiMessage ? sanitizeContent(latestAiMessage.content || '') : null;
    const showProcessing = isTyping || latestAiMessage?.isTyping;

    return (
        <div className="bg-[#F2F2EF] dark:bg-[#14171F] text-slate-700 dark:text-[#E8E8E3] font-sans transition-colors duration-500 overflow-hidden h-screen w-screen relative selection:bg-[#A3B18A] selection:text-white">
            {/* Grid Background */}
            <div className="absolute inset-0 z-0 pointer-events-none opacity-40 dark:opacity-100 bg-grid-light dark:bg-grid-dark grid-bg"></div>
            <div className="absolute inset-0 z-0 bg-gradient-to-b from-[#F2F2EF]/50 via-transparent to-[#F2F2EF]/80 dark:from-[#14171F]/50 dark:via-transparent dark:to-[#14171F]/90 pointer-events-none"></div>

            {/* Navigation */}
            <nav className="absolute top-0 left-0 w-full z-50 p-6 lg:p-8 flex justify-between items-center">
                <Link href="/" className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full border border-[#A3B18A]/30 bg-[#A3B18A]/10 flex items-center justify-center backdrop-blur-md">
                        <MaterialIcon name="hub" className="text-[#A3B18A]" size="18px" />
                    </div>
                    <span className="text-xl font-display font-medium tracking-widest uppercase text-slate-800 dark:text-gray-200">
                        Osool<span className="text-[#A3B18A] font-bold">AI</span>
                    </span>
                </Link>

                <div className="flex gap-3 lg:gap-4">
                    {/* Theme Toggle */}
                    <button
                        onClick={toggleTheme}
                        className="p-2 rounded-full border border-slate-300 dark:border-white/10 hover:bg-slate-100 dark:hover:bg-white/5 transition-colors text-slate-500 dark:text-slate-400"
                    >
                        {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
                    </button>

                    <Link
                        href="/dashboard"
                        className="px-4 py-2 rounded-full border border-slate-300 dark:border-white/10 text-sm hover:bg-slate-100 dark:hover:bg-white/5 transition text-slate-600 dark:text-slate-300 font-display tracking-wide flex items-center gap-2"
                    >
                        <History size={16} />
                        <span className="hidden sm:inline">History</span>
                    </Link>

                    <button
                        onClick={handleNewSession}
                        className="px-4 py-2 rounded-full bg-slate-800 dark:bg-white/10 text-white dark:text-[#E6D5B8] border border-transparent dark:border-[#E6D5B8]/20 text-sm font-medium tracking-wide hover:bg-slate-700 dark:hover:bg-white/20 transition shadow-lg shadow-black/10 flex items-center gap-2"
                    >
                        <PlusCircle size={16} />
                        <span className="hidden sm:inline">New Session</span>
                    </button>

                    {isAuthenticated && (
                        <div className="relative">
                            <button
                                onClick={() => setUserMenuOpen(!isUserMenuOpen)}
                                className="w-10 h-10 rounded-full border border-slate-300 dark:border-white/10 hover:bg-slate-100 dark:hover:bg-white/5 transition text-slate-600 dark:text-slate-300 flex items-center justify-center"
                            >
                                <User size={18} />
                            </button>
                            <AnimatePresence>
                                {isUserMenuOpen && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                        animate={{ opacity: 1, y: 0, scale: 1 }}
                                        exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                        className="absolute right-0 mt-2 w-56 rounded-xl bg-white dark:bg-[#1C212B] border border-slate-200 dark:border-white/10 shadow-xl overflow-hidden z-[60]"
                                    >
                                        <div className="p-3 border-b border-slate-200 dark:border-white/10">
                                            <p className="text-sm font-medium text-slate-800 dark:text-white">{user?.full_name || 'User'}</p>
                                            <p className="text-xs text-slate-500">{user?.email}</p>
                                        </div>
                                        <div className="p-2 space-y-1">
                                            <button onClick={() => setInvitationModalOpen(true)} className="flex items-center gap-2 w-full px-3 py-2 text-sm rounded-lg hover:bg-slate-100 dark:hover:bg-white/5 text-green-600">
                                                <Gift size={16} /> Invite Friends
                                            </button>
                                            <button onClick={() => logout()} className="flex items-center gap-2 w-full px-3 py-2 text-sm rounded-lg hover:bg-red-50 dark:hover:bg-red-900/10 text-red-500">
                                                <LogOut size={16} /> Sign Out
                                            </button>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    )}
                </div>
            </nav>

            {/* Main Content */}
            <main className="relative z-10 w-full h-full flex items-center justify-center">
                <SynapseLines />

                {/* Property Cards - Left Side */}
                {propertiesToShow.slice(0, 2).map((prop, idx) => (
                    <PropertyCard key={idx} property={prop} index={idx} />
                ))}

                {/* Insights Panel - Right Side */}
                <ListingInsightsPanel property={propertiesToShow[0]} />

                {/* ROI Panel - Bottom Right */}
                <ROIPanel roi={12.5} />

                {/* Controls - Bottom Left */}
                <FloatingControls />

                {/* Central Panel */}
                <div className="relative z-20 w-full max-w-2xl mx-4 lg:mx-0">
                    <div className="absolute -inset-1 bg-gradient-to-r from-[#A3B18A]/20 via-[#E6D5B8]/10 to-[#D4A3A3]/20 rounded-3xl blur-xl opacity-30 dark:opacity-40 animate-pulse"></div>
                    <div className="relative glass-panel bg-white/80 dark:bg-[#1C212B]/40 rounded-2xl p-6 lg:p-8 shadow-soft-glow border border-slate-200 dark:border-white/10">
                        {/* Header */}
                        <div className="flex items-center gap-4 mb-6 border-b border-slate-200 dark:border-white/5 pb-5">
                            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-[#A3B18A]/20 to-slate-100 dark:to-[#1C212B] border border-[#A3B18A]/20 flex items-center justify-center">
                                <MaterialIcon name="auto_awesome" className="text-[#A3B18A]" size="20px" />
                            </div>
                            <div>
                                <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400 mb-0.5">Agentic Core</h2>
                                <span className="text-xs text-[#A3B18A]/80 font-display flex items-center gap-2">
                                    {showProcessing ? 'Processing Market Data' : 'Analysis Complete'}
                                    {showProcessing && (
                                        <span className="flex space-x-1">
                                            {[0, 0.2, 0.4].map((delay, i) => (
                                                <span key={i} className="w-1 h-1 bg-[#A3B18A] rounded-full animate-bounce" style={{ animationDelay: `${delay}s` }}></span>
                                            ))}
                                        </span>
                                    )}
                                </span>
                            </div>
                        </div>

                        {/* Content */}
                        <div className="text-right font-sans text-base leading-relaxed text-slate-700 dark:text-[#E8E8E3] space-y-4" dir="rtl">
                            {displayContent ? (
                                <div className="prose prose-slate dark:prose-invert prose-sm max-w-none">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{displayContent}</ReactMarkdown>
                                </div>
                            ) : (
                                <>
                                    <p className="text-slate-900 dark:text-white font-medium">
                                        أهلاً بيك يا {getUserName()}! التجمع الخامس اختيار ممتاز.
                                    </p>
                                    <p className="text-slate-600 dark:text-gray-300 font-light">
                                        بص، متوسط أسعار الشقق في التجمع الخامس بيبدأ من <span className="text-[#E6D5B8] font-bold">5.4</span> مليون جنيه لحد <span className="text-[#E6D5B8] font-bold">18.1</span> مليون جنيه.
                                    </p>
                                    <div className="p-3 bg-[#A3B18A]/5 dark:bg-[#A3B18A]/10 border border-[#A3B18A]/10 rounded-xl relative">
                                        <div className="absolute top-0 right-0 w-1 h-full bg-[#A3B18A]/40"></div>
                                        <p className="text-slate-700 dark:text-gray-200 text-sm">
                                            من الخيارات في شقة في <span className="font-bold text-[#A3B18A]">السراي</span> بسعر 5.38 مليون جنيه، مساحتها 81م² - Wolf Score: 68/100 - قيمة ممتازة!
                                        </p>
                                    </div>
                                    <p className="text-xs text-slate-500 font-display">تحب نحجز معاينة لإحدى الشقق دول؟</p>
                                </>
                            )}
                        </div>

                        {/* Charts */}
                        {visualizations.length > 0 && (
                            <div className="mt-5 space-y-3">
                                {visualizations.map((viz: any, idx: number) => {
                                    let chartType: any = viz.type || 'bar';
                                    let chartData = viz.data;
                                    if (viz.type === 'inflation_killer' && viz.data?.projections) {
                                        chartType = 'line';
                                        chartData = viz.data.projections;
                                    }
                                    if (!Array.isArray(chartData) || chartData.length === 0) return null;
                                    return (
                                        <div key={idx} className="glass-panel rounded-xl p-4 bg-white/50 dark:bg-white/5 border border-slate-200 dark:border-white/10">
                                            <ChartVisualization type={chartType} title={viz.title || 'Analysis'} data={chartData} labels={viz.labels || []} trend={viz.trend} subtitle={viz.subtitle} />
                                        </div>
                                    );
                                })}
                            </div>
                        )}

                        {/* Buttons */}
                        <div className="mt-6 flex flex-wrap gap-3 justify-end" dir="rtl">
                            <button className="px-4 py-2 bg-slate-100 dark:bg-white/5 hover:bg-slate-200 dark:hover:bg-white/10 border border-slate-200 dark:border-white/5 rounded-xl text-sm text-slate-600 dark:text-slate-300 transition-all flex items-center gap-2">
                                <MaterialIcon name="calendar_today" size="16px" /> حجز معاينة
                            </button>
                            <button className="px-4 py-2 bg-[#A3B18A]/10 border border-[#A3B18A]/30 text-[#A3B18A] hover:bg-[#A3B18A]/20 rounded-xl text-sm transition-all flex items-center gap-2">
                                <MaterialIcon name="visibility" size="16px" /> عرض التفاصيل
                            </button>
                        </div>
                    </div>
                </div>
            </main>

            {/* Input */}
            <div className="absolute bottom-8 left-1/2 -translate-x-1/2 w-full max-w-2xl px-6 z-50">
                <div className="relative group">
                    <div className="absolute -inset-1 bg-gradient-to-r from-[#A3B18A]/30 via-[#E6D5B8]/20 to-[#D4A3A3]/30 rounded-full blur-xl opacity-20 group-hover:opacity-40 transition duration-700"></div>
                    <div className="relative flex items-center bg-white dark:bg-[#1C212B]/80 backdrop-blur-xl border border-slate-200 dark:border-white/10 rounded-full shadow-2xl overflow-hidden hover:border-[#A3B18A]/20 transition-colors">
                        <button className="pl-4 pr-2 text-slate-400 hover:text-[#A3B18A] transition">
                            <MaterialIcon name="add_circle" size="22px" />
                        </button>
                        <input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            className="w-full py-3.5 bg-transparent border-none focus:ring-0 focus:outline-none text-slate-700 dark:text-gray-200 placeholder-slate-400 font-sans text-sm"
                            placeholder="Ask about properties, market trends..."
                            disabled={isTyping}
                        />
                        <button className="p-2 text-slate-400 hover:text-[#A3B18A] transition">
                            <MaterialIcon name="mic" size="20px" />
                        </button>
                        <button
                            onClick={handleSend}
                            disabled={!input.trim() || isTyping}
                            className="mr-2 p-2 bg-slate-100 dark:bg-white/10 rounded-full text-slate-500 dark:text-[#E6D5B8] hover:bg-[#A3B18A] hover:text-white transition disabled:opacity-50"
                        >
                            <MaterialIcon name="arrow_upward" size="18px" />
                        </button>
                    </div>
                    <p className="text-center mt-2 text-[9px] text-slate-400 dark:text-slate-500 tracking-widest uppercase font-display opacity-70">
                        AI insights require independent verification
                    </p>
                </div>
            </div>

            <ContextualPane isOpen={!!selectedProperty} onClose={() => setSelectedProperty(null)} property={selectedProperty} isRTL={language === 'ar'} />
            <InvitationModal isOpen={isInvitationModalOpen} onClose={() => setInvitationModalOpen(false)} />
        </div>
    );
}
