'use client';

import { useState, useMemo, useCallback, useEffect } from 'react';
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
import { User, LogOut, Gift, PlusCircle, History } from 'lucide-react';

const MaterialIcon = ({ name, className = '', size = '20px' }: { name: string, className?: string, size?: string }) => (
    <span className={`material-symbols-outlined select-none ${className}`} style={{ fontSize: size }}>{name}</span>
);

const sanitizeContent = (content: string): string => {
    if (typeof window === 'undefined') return content;
    return DOMPurify.sanitize(content, {
        ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li', 'code', 'pre', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
        ALLOWED_ATTR: ['href', 'target', 'rel', 'class'],
    });
};

// --- Response Type Detection ---
type ResponseType = 'greeting' | 'property_recommendation' | 'market_analysis' | 'comparison' | 'general' | 'loading';

const detectResponseType = (content: string, properties: any[], visualizations: any[]): ResponseType => {
    if (!content) return 'loading';
    const lowerContent = content.toLowerCase();

    if (properties && properties.length > 1) return 'comparison';
    if (properties && properties.length === 1) return 'property_recommendation';
    if (visualizations && visualizations.length > 0) return 'market_analysis';
    if (lowerContent.includes('أهلاً') || lowerContent.includes('مرحبا') || lowerContent.includes('hello')) return 'greeting';
    if (lowerContent.includes('سعر') || lowerContent.includes('متوسط') || lowerContent.includes('trend') || lowerContent.includes('market')) return 'market_analysis';

    return 'general';
};

// --- Smart Action Buttons based on context ---
const getContextualActions = (responseType: ResponseType, hasProperties: boolean): Array<{ label: string, icon: string, primary?: boolean }> => {
    switch (responseType) {
        case 'property_recommendation':
            return [
                { label: 'حجز معاينة', icon: 'calendar_today' },
                { label: 'عرض التفاصيل', icon: 'visibility', primary: true },
                { label: 'مقارنة الأسعار', icon: 'compare_arrows' }
            ];
        case 'comparison':
            return [
                { label: 'حجز معاينة', icon: 'calendar_today' },
                { label: 'تحليل مفصل', icon: 'analytics', primary: true },
                { label: 'حفظ المقارنة', icon: 'bookmark' }
            ];
        case 'market_analysis':
            return [
                { label: 'تحميل التقرير', icon: 'download' },
                { label: 'عرض المزيد', icon: 'expand_more', primary: true }
            ];
        case 'greeting':
            return [
                { label: 'ابحث عن عقار', icon: 'search', primary: true },
                { label: 'تحليل السوق', icon: 'trending_up' }
            ];
        default:
            return hasProperties ? [
                { label: 'حجز معاينة', icon: 'calendar_today' },
                { label: 'عرض التفاصيل', icon: 'visibility', primary: true }
            ] : [];
    }
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

// --- Smart Property Card with animations ---
const PropertyCard = ({ property, index = 0, isActive = false, onClick }: { property: any, index?: number, isActive?: boolean, onClick?: () => void }) => {
    const topOffset = 20 + (index * 25);

    return (
        <motion.div
            initial={{ opacity: 0, x: -80, scale: 0.9 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: -80, scale: 0.9 }}
            transition={{ delay: 0.1 + (index * 0.15), duration: 0.6, type: 'spring' }}
            whileHover={{ scale: 1.03 }}
            className={`hidden lg:block absolute w-80 transform transition-all duration-300 cursor-pointer z-10 ${isActive ? 'ring-2 ring-[#A3B18A]/50' : ''}`}
            style={{ left: '10%', top: `${topOffset}%` }}
            onClick={onClick}
        >
            <div className="relative glass-panel rounded-2xl p-5 group hover:border-[#A3B18A]/30 transition-colors">
                <div className="absolute -top-[1px] -left-[1px] w-4 h-4 border-t border-l border-[#A3B18A]/60 rounded-tl-lg"></div>

                {/* Active indicator */}
                {isActive && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="absolute -top-2 -right-2 w-6 h-6 bg-[#A3B18A] rounded-full flex items-center justify-center shadow-lg"
                    >
                        <MaterialIcon name="check" className="text-white" size="14px" />
                    </motion.div>
                )}

                <div className="relative overflow-hidden rounded-xl mb-4 h-44 bg-slate-200/50 dark:bg-[#1C212B]/50">
                    {property.image_url ? (
                        <img alt="Property" className="w-full h-full object-cover opacity-90 group-hover:opacity-100 hologram-img transition-all duration-500" src={property.image_url} />
                    ) : (
                        <div className="w-full h-full bg-slate-300 dark:bg-slate-800 flex items-center justify-center">
                            <MaterialIcon name="apartment" className="text-slate-400 dark:text-white/20" size="48px" />
                        </div>
                    )}
                    <div className="absolute top-3 left-3 px-3 py-1 bg-slate-800/40 dark:bg-[#1C212B]/60 border border-slate-300/20 dark:border-white/20 text-white dark:text-[#E8E8E3] text-[10px] font-bold uppercase rounded-md backdrop-blur-md tracking-wider">
                        {property.tag || 'Top Pick'}
                    </div>
                    {property.wolf_score && (
                        <div className="absolute bottom-3 right-3 px-2 py-1 bg-[#A3B18A]/90 text-white text-[10px] font-bold rounded backdrop-blur-md">
                            Wolf Score: {property.wolf_score}
                        </div>
                    )}
                </div>
                <div className="space-y-3">
                    <div className="flex justify-between items-start">
                        <div>
                            <h3 className="text-lg font-medium leading-tight text-slate-800 dark:text-slate-100 font-sans">{property.title}</h3>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-display uppercase tracking-wide">{property.location}</p>
                        </div>
                        <div className="flex items-center gap-1 text-[#E6D5B8]">
                            <MaterialIcon name="star" className="text-sm" />
                            <span className="text-sm font-bold">{property.rating || 5.0}</span>
                        </div>
                    </div>
                    <div className="text-2xl font-light text-[#A3B18A] font-display">{property.price?.toLocaleString() || '0'} <span className="text-base text-slate-500">EGP</span></div>
                    <div className="grid grid-cols-3 gap-2 mt-4 pt-4 border-t border-slate-200 dark:border-white/5">
                        <div className="text-center"><MaterialIcon name="bed" className="text-slate-400 text-xs mb-1" /><p className="text-xs font-semibold text-slate-600 dark:text-slate-300">{property.bedrooms} Bed</p></div>
                        <div className="text-center"><MaterialIcon name="bathtub" className="text-slate-400 text-xs mb-1" /><p className="text-xs font-semibold text-slate-600 dark:text-slate-300">{property.bathrooms} Bath</p></div>
                        <div className="text-center"><MaterialIcon name="square_foot" className="text-slate-400 text-xs mb-1" /><p className="text-xs font-semibold text-slate-600 dark:text-slate-300">{property.size_sqm}m²</p></div>
                    </div>
                </div>
                <div className="absolute top-1/2 -right-16 w-16 h-[1px] bg-gradient-to-r from-white/20 to-transparent"></div>
                <div className="absolute top-1/2 -right-[66px] w-2 h-2 rounded-full bg-white/20 blur-[1px]"></div>
            </div>
        </motion.div>
    );
};

// --- Dynamic Insights Panel ---
const InsightsPanel = ({ property, responseType }: { property: any, responseType: ResponseType }) => {
    const capRate = property?.cap_rate || 8;
    const pricePerSqm = property ? Math.round(property.price / property.size_sqm) : 110000;
    const walkScore = property?.walk_score || 85;
    const wolfScore = property?.wolf_score || 68;

    const getInsightLabel = () => {
        switch (responseType) {
            case 'comparison': return 'Comparison Insights';
            case 'market_analysis': return 'Market Analysis';
            default: return 'Listing Insights';
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, x: 80 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
            className="hidden lg:block absolute right-[5%] top-[20%] w-72 z-10"
        >
            <div className="relative glass-panel rounded-2xl p-6 hover:border-[#D4A3A3]/30 transition-colors">
                <div className="absolute -bottom-[1px] -right-[1px] w-4 h-4 border-b border-r border-[#D4A3A3]/60 rounded-br-lg"></div>
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400">{getInsightLabel()}</h3>
                    <MaterialIcon name="analytics" className="text-[#D4A3A3]/70 text-lg" />
                </div>
                <div className="space-y-6">
                    {/* Cap Rate */}
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
                        <div className="flex justify-between text-xs text-slate-500 mb-2 font-display uppercase tracking-wider">
                            <span>Cap Rate</span>
                            <span className="text-[#A3B18A]">{capRate > 7 ? 'High' : capRate > 5 ? 'Medium' : 'Low'}</span>
                        </div>
                        <div className="text-3xl font-light text-slate-800 dark:text-white font-display">{capRate}%</div>
                        <div className="w-full bg-slate-200 dark:bg-white/5 h-1.5 mt-2 rounded-full overflow-hidden">
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${capRate * 10}%` }}
                                transition={{ delay: 0.5, duration: 0.8 }}
                                className="bg-gradient-to-r from-[#D4A3A3] to-[#A3B18A] h-full rounded-full opacity-80"
                            />
                        </div>
                    </motion.div>

                    {/* Price/SQM */}
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
                        <div className="flex justify-between text-xs text-slate-500 mb-1 font-display uppercase tracking-wider"><span>Price / SQM</span></div>
                        <div className="text-2xl font-light text-slate-800 dark:text-white font-display">{pricePerSqm.toLocaleString()} <span className="text-sm text-slate-500">EGP</span></div>
                    </motion.div>

                    {/* Wolf Score (if available) or Walk Score */}
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}>
                        <div className="flex justify-between text-xs text-slate-500 mb-2 font-display uppercase tracking-wider">
                            <span>{property?.wolf_score ? 'Wolf Score' : 'Walk Score'}</span>
                            <span className="text-[#E6D5B8] font-bold">{property?.wolf_score || walkScore}/100</span>
                        </div>
                        <div className="h-16 w-full flex items-end gap-1 mt-2">
                            {[40, 60, 30, 80, 90, 50].map((h, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ height: 0 }}
                                    animate={{ height: `${h}%` }}
                                    transition={{ delay: 0.7 + (i * 0.1), duration: 0.4 }}
                                    className={`w-1/6 ${i < 3 ? 'bg-[#D4A3A3]' : 'bg-[#A3B18A]'} rounded-t-sm`}
                                    style={{ opacity: 0.2 + (i * 0.15) }}
                                />
                            ))}
                        </div>
                    </motion.div>
                </div>
                <div className="absolute top-1/2 -left-16 w-16 h-[1px] bg-gradient-to-l from-white/20 to-transparent"></div>
            </div>
        </motion.div>
    );
};

// --- ROI Panel ---
const ROIPanel = ({ roi = 12.5, property }: { roi?: number, property?: any }) => (
    <motion.div
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5, duration: 0.6 }}
        className="hidden lg:block absolute right-[15%] bottom-[15%] w-64 z-10"
    >
        <div className="relative glass-panel rounded-2xl p-5 hover:border-[#A3B18A]/40 transition-colors">
            <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-bold tracking-widest uppercase text-slate-400">Proj. Annual ROI</span>
                <MaterialIcon name="trending_up" className="text-[#A3B18A] text-sm" />
            </div>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.7 }}
                className="text-3xl font-light text-[#A3B18A] font-display"
            >
                {property?.roi || roi}%
            </motion.div>
            <p className="text-[10px] text-slate-500 mt-2 leading-tight">Based on recent market trends in {property?.location || 'New Cairo'}.</p>
            <div className="absolute -top-12 left-1/2 w-[1px] h-12 bg-gradient-to-b from-transparent to-white/20"></div>
        </div>
    </motion.div>
);

// --- Loading State Component ---
const LoadingState = () => (
    <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex flex-col items-center justify-center py-12"
    >
        <div className="relative">
            <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                className="w-16 h-16 rounded-full border-2 border-[#A3B18A]/20 border-t-[#A3B18A]"
            />
            <MaterialIcon name="auto_awesome" className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-[#A3B18A]" size="24px" />
        </div>
        <motion.p
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="mt-4 text-slate-500 font-display"
        >
            جاري تحليل البيانات...
        </motion.p>
    </motion.div>
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
    const [activePropertyIndex, setActivePropertyIndex] = useState(0);

    // Default property for initial state
    const defaultProperty = { title: 'Apartment in El Patio 7', location: 'New Cairo', price: 18150000, bedrooms: 3, bathrooms: 3, size_sqm: 165, rating: 5.0, wolf_score: 68 };

    // Smart property selection
    const currentProperty = displayProperties[activePropertyIndex] || (displayProperties.length > 0 ? displayProperties[0] : defaultProperty);
    const hasProperties = displayProperties.length > 0;

    const latestAiMessage = useMemo(() => {
        const aiMessages = messages.filter(m => m.role === 'amr');
        return aiMessages.length > 0 ? aiMessages[aiMessages.length - 1] : null;
    }, [messages]);

    // Detect response type
    const responseType = useMemo(() => {
        return detectResponseType(
            latestAiMessage?.content || '',
            displayProperties,
            visualizations
        );
    }, [latestAiMessage?.content, displayProperties, visualizations]);

    // Get contextual actions
    const contextualActions = useMemo(() => {
        return getContextualActions(responseType, hasProperties);
    }, [responseType, hasProperties]);

    const handleSelectProperty = useCallback((prop: any, index: number = 0) => {
        setActivePropertyIndex(index);
        setSelectedProperty({
            title: prop.title, address: prop.location, price: `${prop.price?.toLocaleString() || 0} EGP`,
            metrics: { bedrooms: prop.bedrooms, size: prop.size_sqm, wolfScore: prop.wolf_score || 75, capRate: `${prop.cap_rate || 8}%`, pricePerSqFt: `${Math.round((prop.price || 0) / (prop.size_sqm || 1)).toLocaleString()}` },
            aiRecommendation: prop.ai_recommendation || "Strong appreciation potential.", tags: prop.tags || ["High Growth"], agent: { name: "Amr", title: "Consultant" }
        });
    }, []);

    const handleSend = async () => {
        if (!input.trim() || isTyping) return;
        const userMsg = { role: 'user', content: input, id: Date.now().toString() };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsTyping(true);
        setActivePropertyIndex(0);

        const aiMsgId = (Date.now() + 1).toString();
        setMessages(prev => [...prev, { role: 'amr', content: '', id: aiMsgId, isTyping: true }]);

        let fullResponse = '';
        try {
            await streamChat(userMsg.content, sessionId, {
                onToken: (token) => { fullResponse += token; setMessages(prev => prev.map(m => m.id === aiMsgId ? { ...m, content: fullResponse } : m)); },
                onToolStart: () => { }, onToolEnd: () => { },
                onComplete: (data) => {
                    setMessages(prev => prev.map(m => m.id === aiMsgId ? { ...m, content: fullResponse, properties: data.properties, visualizations: data.ui_actions, isTyping: false } : m));
                    if (data.properties?.length > 0) {
                        setDisplayProperties(data.properties.slice(0, 3));
                        handleSelectProperty(data.properties[0], 0);
                    }
                    if (data.ui_actions?.length > 0) { setVisualizations(data.ui_actions); }
                    setIsTyping(false);
                },
                onError: () => { setMessages(prev => prev.map(m => m.id === aiMsgId ? { ...m, content: fullResponse + '\n\n[Error]', isTyping: false } : m)); setIsTyping(false); }
            }, language === 'ar' ? 'ar' : 'auto');
        } catch { setIsTyping(false); }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } };
    const getUserName = (): string => user?.full_name || user?.email?.split('@')[0] || 'Mustafa';
    const handleNewSession = () => { setMessages([]); setSelectedProperty(null); setDisplayProperties([]); setVisualizations([]); setInput(''); setIsTyping(false); setSessionId(`session-${Date.now()}`); setActivePropertyIndex(0); };

    const hasAiResponse = messages.some(m => m.role === 'amr');
    const displayContent = latestAiMessage?.content ? sanitizeContent(latestAiMessage.content) : null;
    const showProcessing = isTyping || latestAiMessage?.isTyping;

    // Determine which properties to show
    const propertiesToDisplay = hasProperties ? displayProperties : [defaultProperty];

    return (
        <div className="bg-[#F2F2EF] dark:bg-[#14171F] text-slate-700 dark:text-[#E8E8E3] font-sans transition-colors duration-500 overflow-hidden h-screen w-screen relative selection:bg-[#A3B18A] selection:text-white">
            {/* Grid Background */}
            <div className="absolute inset-0 z-0 pointer-events-none opacity-40 dark:opacity-100 bg-grid-light dark:bg-grid-dark grid-bg"></div>
            <div className="absolute inset-0 z-0 bg-gradient-to-b from-[#F2F2EF]/50 via-transparent to-[#F2F2EF]/80 dark:from-[#14171F]/50 dark:via-transparent dark:to-[#14171F]/90 pointer-events-none"></div>

            {/* Navigation */}
            <nav className="absolute top-0 left-0 w-full z-50 p-8 flex justify-between items-center">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full border border-[#A3B18A]/30 bg-[#A3B18A]/10 flex items-center justify-center backdrop-blur-md">
                        <MaterialIcon name="hub" className="text-[#A3B18A] text-lg" />
                    </div>
                    <Link href="/" className="text-xl font-display font-medium tracking-widest uppercase text-slate-800 dark:text-gray-200">
                        Osool<span className="text-[#A3B18A] font-bold">AI</span>
                    </Link>
                </div>
                <div className="flex gap-4">
                    <button onClick={toggleTheme} className="p-2 rounded-full border border-slate-300 dark:border-white/10 hover:bg-white/50 dark:hover:bg-white/5 transition-colors text-slate-500 dark:text-slate-400">
                        <MaterialIcon name={theme === 'dark' ? 'light_mode' : 'dark_mode'} className="text-xl" />
                    </button>
                    <Link href="/dashboard" className="px-5 py-2 rounded-full border border-slate-300 dark:border-white/10 text-sm hover:bg-slate-100 dark:hover:bg-white/5 transition text-slate-600 dark:text-slate-300 font-display tracking-wide flex items-center gap-2">
                        <History size={16} /> History
                    </Link>
                    <button onClick={handleNewSession} className="px-5 py-2 rounded-full bg-slate-800 dark:bg-white/10 text-white dark:text-[#E6D5B8] border border-transparent dark:border-[#E6D5B8]/20 text-sm font-medium tracking-wide hover:bg-slate-700 dark:hover:bg-white/20 transition shadow-lg shadow-black/10 flex items-center gap-2">
                        <PlusCircle size={16} /> New Session
                    </button>
                    {isAuthenticated && (
                        <div className="relative">
                            <button onClick={() => setUserMenuOpen(!isUserMenuOpen)} className="w-10 h-10 rounded-full border border-slate-300 dark:border-white/10 hover:bg-slate-100 dark:hover:bg-white/5 transition text-slate-500 dark:text-slate-400 flex items-center justify-center">
                                <User size={18} />
                            </button>
                            <AnimatePresence>
                                {isUserMenuOpen && (
                                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 10 }} className="absolute right-0 mt-2 w-56 rounded-xl bg-white dark:bg-[#1C212B] border border-slate-200 dark:border-white/10 shadow-xl z-[60]">
                                        <div className="p-3 border-b border-slate-200 dark:border-white/10">
                                            <p className="text-sm font-medium text-slate-800 dark:text-white">{user?.full_name || 'User'}</p>
                                            <p className="text-xs text-slate-500">{user?.email}</p>
                                        </div>
                                        <div className="p-2">
                                            <button onClick={() => setInvitationModalOpen(true)} className="flex items-center gap-2 w-full px-3 py-2 text-sm rounded-lg hover:bg-slate-100 dark:hover:bg-white/5 text-green-600"><Gift size={16} /> Invite</button>
                                            <button onClick={() => logout()} className="flex items-center gap-2 w-full px-3 py-2 text-sm rounded-lg hover:bg-red-50 dark:hover:bg-red-900/10 text-red-500"><LogOut size={16} /> Sign Out</button>
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

                {/* LEFT: Property Cards with AnimatePresence */}
                <AnimatePresence mode="wait">
                    {propertiesToDisplay.slice(0, 2).map((prop, idx) => (
                        <PropertyCard
                            key={`${prop.title}-${idx}`}
                            property={prop}
                            index={idx}
                            isActive={idx === activePropertyIndex}
                            onClick={() => handleSelectProperty(prop, idx)}
                        />
                    ))}
                </AnimatePresence>

                {/* RIGHT: Insights Panel */}
                <InsightsPanel property={currentProperty} responseType={responseType} />

                {/* BOTTOM-RIGHT: ROI Panel */}
                <ROIPanel roi={12.5} property={currentProperty} />

                {/* CENTER: Agentic Core Panel */}
                <div className="relative z-20 w-full max-w-2xl mx-4 lg:mx-0 transform transition-all duration-700">
                    <div className="absolute -inset-1 bg-gradient-to-r from-[#A3B18A]/20 via-[#E6D5B8]/10 to-[#D4A3A3]/20 rounded-3xl blur-xl opacity-30 dark:opacity-40 animate-pulse"></div>
                    <div className="relative glass-panel bg-white/80 dark:bg-[#1C212B]/40 rounded-2xl p-6 lg:p-10 shadow-soft-glow">
                        {/* Header */}
                        <div className="flex items-center gap-4 mb-8 border-b border-slate-200 dark:border-white/5 pb-6">
                            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#A3B18A]/20 to-slate-100 dark:to-[#1C212B] border border-[#A3B18A]/20 flex items-center justify-center">
                                <MaterialIcon name="auto_awesome" className="text-[#A3B18A] font-light" />
                            </div>
                            <div>
                                <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-slate-400 dark:text-slate-400 mb-1">Agentic Core</h2>
                                <motion.span
                                    key={showProcessing ? 'processing' : 'complete'}
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="text-sm text-[#A3B18A]/80 font-display flex items-center gap-2"
                                >
                                    {showProcessing ? 'Processing Market Data' : 'Analysis Complete'}
                                    {showProcessing && <span className="flex space-x-1">{[0, 0.2, 0.4].map((d, i) => <span key={i} className="w-1 h-1 bg-[#A3B18A] rounded-full animate-bounce" style={{ animationDelay: `${d}s` }}></span>)}</span>}
                                </motion.span>
                            </div>
                        </div>

                        {/* Content */}
                        <div className="text-right font-sans text-lg leading-loose text-slate-700 dark:text-[#E8E8E3] space-y-6" dir="rtl">
                            <AnimatePresence mode="wait">
                                {displayContent ? (
                                    <motion.div
                                        key="content"
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -20 }}
                                        className="prose prose-lg dark:prose-invert max-w-none prose-p:text-slate-700 dark:prose-p:text-[#E8E8E3] prose-p:leading-loose prose-strong:text-[#A3B18A] prose-a:text-[#A3B18A]"
                                    >
                                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{displayContent}</ReactMarkdown>
                                    </motion.div>
                                ) : hasAiResponse ? (
                                    <LoadingState />
                                ) : (
                                    <motion.div key="greeting" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                                        <p className="text-slate-900 dark:text-white font-medium">أهلاً بيك يا {getUserName()}! التجمع الخامس اختيار ممتاز.</p>
                                        <p className="text-slate-600 dark:text-gray-300 font-light mt-4">بص، متوسط أسعار الشقق في التجمع الخامس بيبدأ من <span className="text-[#E6D5B8] font-bold px-1">5.4</span> مليون جنيه لحد <span className="text-[#E6D5B8] font-bold px-1">18.1</span> مليون جنيه.</p>
                                        <div className="p-4 bg-[#A3B18A]/5 border border-[#A3B18A]/10 rounded-xl relative overflow-hidden mt-4">
                                            <div className="absolute top-0 right-0 w-1 h-full bg-[#A3B18A]/40"></div>
                                            <p className="text-slate-700 dark:text-gray-200">من الخيارات اللي عندي، في شقة في <span className="font-bold text-[#A3B18A]">السراي</span> بسعر 5.38 مليون جنيه. الـ AI بتاعي قيمها بـ 50/100.</p>
                                        </div>
                                        <p className="text-sm text-slate-500 mt-4 font-display">تحب نحجز معاينة يا {getUserName()}؟</p>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>

                        {/* Charts */}
                        <AnimatePresence>
                            {visualizations.length > 0 && (
                                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mt-6 space-y-4">
                                    {visualizations.map((viz: any, idx: number) => {
                                        let chartData = viz.type === 'inflation_killer' && viz.data?.projections ? viz.data.projections : viz.data;
                                        if (!Array.isArray(chartData) || chartData.length === 0) return null;
                                        return (
                                            <div key={idx} className="glass-panel rounded-xl p-4 bg-white/50 dark:bg-white/5">
                                                <ChartVisualization type={viz.type === 'inflation_killer' ? 'line' : viz.type || 'bar'} title={viz.title || 'Analysis'} data={chartData} labels={viz.labels || []} trend={viz.trend} subtitle={viz.subtitle} />
                                            </div>
                                        );
                                    })}
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* Smart Action Buttons */}
                        <motion.div
                            key={responseType}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="mt-8 flex flex-wrap gap-3 justify-end"
                            dir="rtl"
                        >
                            {contextualActions.map((action, idx) => (
                                <motion.button
                                    key={action.label}
                                    initial={{ opacity: 0, x: 20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: idx * 0.1 }}
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                    className={`px-5 py-2.5 rounded-xl text-sm transition-all flex items-center gap-2 shadow-sm ${action.primary
                                        ? 'bg-[#A3B18A]/10 border border-[#A3B18A]/30 text-[#A3B18A] hover:bg-[#A3B18A]/20'
                                        : 'bg-slate-100 dark:bg-white/5 hover:bg-slate-200 dark:hover:bg-white/10 border border-slate-200 dark:border-white/5 text-slate-600 dark:text-slate-300'
                                        }`}
                                >
                                    <MaterialIcon name={action.icon} className="text-lg" /> {action.label}
                                </motion.button>
                            ))}
                        </motion.div>
                    </div>
                </div>
            </main>

            {/* Floating Controls */}
            <div className="absolute bottom-8 left-8 flex flex-col gap-3 z-50">
                {['add', 'remove', 'my_location'].map((icon, idx) => (
                    <motion.button
                        key={icon}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.5 + (idx * 0.1) }}
                        className="w-11 h-11 rounded-xl bg-white/80 dark:bg-[#1C212B]/50 border border-slate-200 dark:border-white/10 text-slate-500 dark:text-slate-400 backdrop-blur-md flex items-center justify-center hover:bg-[#A3B18A]/20 hover:text-[#A3B18A] hover:border-[#A3B18A]/30 transition-all shadow-lg"
                    >
                        <MaterialIcon name={icon} className="text-xl" />
                    </motion.button>
                ))}
            </div>

            {/* Input */}
            <div className="absolute bottom-10 left-1/2 -translate-x-1/2 w-full max-w-2xl px-6 z-50">
                <motion.div initial={{ opacity: 0, y: 50 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="relative group">
                    <div className="absolute -inset-1 bg-gradient-to-r from-[#A3B18A]/30 via-[#E6D5B8]/20 to-[#D4A3A3]/30 rounded-full blur-xl opacity-20 group-hover:opacity-40 transition duration-700"></div>
                    <div className="relative flex items-center bg-white dark:bg-[#1C212B]/80 backdrop-blur-xl border border-slate-200 dark:border-white/10 rounded-full shadow-2xl overflow-hidden transition-colors hover:border-[#A3B18A]/20">
                        <button className="pl-5 pr-3 text-slate-400 hover:text-[#A3B18A] transition"><MaterialIcon name="add_circle" /></button>
                        <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKeyDown} className="w-full py-4 bg-transparent border-none focus:ring-0 focus:outline-none text-slate-700 dark:text-gray-200 placeholder-slate-400 font-sans text-base tracking-wide" placeholder="Ask about properties, market trends..." disabled={isTyping} />
                        <button className="p-3 text-slate-400 hover:text-[#A3B18A] transition"><MaterialIcon name="mic" /></button>
                        <button onClick={handleSend} disabled={!input.trim() || isTyping} className="mr-2 p-2.5 bg-slate-100 dark:bg-white/10 rounded-full text-slate-500 dark:text-[#E6D5B8] hover:bg-[#A3B18A] hover:text-white transition shadow-inner disabled:opacity-50">
                            <MaterialIcon name="arrow_upward" className="text-lg" />
                        </button>
                    </div>
                    <div className="text-center mt-3"><p className="text-[10px] text-slate-400 dark:text-slate-500 tracking-widest uppercase font-display opacity-70">AI insights require independent verification</p></div>
                </motion.div>
            </div>

            <ContextualPane isOpen={!!selectedProperty} onClose={() => setSelectedProperty(null)} property={selectedProperty} isRTL={language === 'ar'} />
            <InvitationModal isOpen={isInvitationModalOpen} onClose={() => setInvitationModalOpen(false)} />
        </div>
    );
}
