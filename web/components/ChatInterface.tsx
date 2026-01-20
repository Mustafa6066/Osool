'use client';

import { useState, useMemo } from 'react';
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

// --- SVG Synapse Lines (exact from reference) ---
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

    // Default property
    const defaultProperty = { title: 'Apartment in El Patio 7', location: 'New Cairo', price: 18150000, bedrooms: 3, bathrooms: 3, size_sqm: 165, rating: 5.0 };
    const currentProperty = displayProperties[0] || defaultProperty;

    const latestAiMessage = useMemo(() => {
        const aiMessages = messages.filter(m => m.role === 'amr');
        return aiMessages.length > 0 ? aiMessages[aiMessages.length - 1] : null;
    }, [messages]);

    const handleSelectProperty = (prop: any) => {
        setSelectedProperty({
            title: prop.title, address: prop.location, price: `${prop.price.toLocaleString()} EGP`,
            metrics: { bedrooms: prop.bedrooms, size: prop.size_sqm, wolfScore: prop.wolf_score || 75, capRate: "8%", pricePerSqFt: `${Math.round(prop.price / prop.size_sqm).toLocaleString()}` },
            aiRecommendation: "Strong appreciation potential.", tags: ["High Growth"], agent: { name: "Amr", title: "Consultant" }
        });
    };

    const handleSend = async () => {
        if (!input.trim() || isTyping) return;
        const userMsg = { role: 'user', content: input, id: Date.now().toString() };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsTyping(true);

        const aiMsgId = (Date.now() + 1).toString();
        setMessages(prev => [...prev, { role: 'amr', content: '', id: aiMsgId, isTyping: true }]);

        let fullResponse = '';
        try {
            await streamChat(userMsg.content, sessionId, {
                onToken: (token) => { fullResponse += token; setMessages(prev => prev.map(m => m.id === aiMsgId ? { ...m, content: fullResponse } : m)); },
                onToolStart: () => { }, onToolEnd: () => { },
                onComplete: (data) => {
                    setMessages(prev => prev.map(m => m.id === aiMsgId ? { ...m, content: fullResponse, properties: data.properties, visualizations: data.ui_actions, isTyping: false } : m));
                    if (data.properties?.length > 0) { setDisplayProperties(data.properties.slice(0, 3)); handleSelectProperty(data.properties[0]); }
                    if (data.ui_actions?.length > 0) { setVisualizations(data.ui_actions); }
                    setIsTyping(false);
                },
                onError: () => { setMessages(prev => prev.map(m => m.id === aiMsgId ? { ...m, content: fullResponse + '\n\n[Error]', isTyping: false } : m)); setIsTyping(false); }
            }, language === 'ar' ? 'ar' : 'auto');
        } catch { setIsTyping(false); }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } };
    const getUserName = (): string => user?.full_name || user?.email?.split('@')[0] || 'Mustafa';
    const handleNewSession = () => { setMessages([]); setSelectedProperty(null); setDisplayProperties([]); setVisualizations([]); setInput(''); setIsTyping(false); setSessionId(`session-${Date.now()}`); };

    const displayContent = latestAiMessage ? sanitizeContent(latestAiMessage.content || '') : null;
    const showProcessing = isTyping || latestAiMessage?.isTyping;

    // Calculate insights from property
    const capRate = currentProperty?.cap_rate || 8;
    const pricePerSqm = currentProperty ? Math.round(currentProperty.price / currentProperty.size_sqm) : 110000;
    const walkScore = currentProperty?.walk_score || 85;

    return (
        <div className="bg-[#F2F2EF] dark:bg-[#14171F] text-slate-700 dark:text-[#E8E8E3] font-sans transition-colors duration-500 overflow-hidden h-screen w-screen relative selection:bg-[#A3B18A] selection:text-white">
            {/* Grid Background */}
            <div className="absolute inset-0 z-0 pointer-events-none opacity-40 dark:opacity-100 bg-grid-light dark:bg-grid-dark grid-bg"></div>
            <div className="absolute inset-0 z-0 bg-gradient-to-b from-[#F2F2EF]/50 via-transparent to-[#F2F2EF]/80 dark:from-[#14171F]/50 dark:via-transparent dark:to-[#14171F]/90 pointer-events-none"></div>

            {/* Navigation - exact from reference */}
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
                    <button onClick={toggleTheme} className="p-2 rounded-full border border-slate-300 dark:border-white/10 hover:bg-white/5 transition-colors text-slate-500 dark:text-slate-400">
                        <MaterialIcon name={theme === 'dark' ? 'light_mode' : 'dark_mode'} className="text-xl" />
                    </button>
                    <Link href="/dashboard" className="px-5 py-2 rounded-full border border-slate-300 dark:border-white/10 text-sm hover:bg-white/5 transition text-slate-600 dark:text-slate-300 font-display tracking-wide flex items-center gap-2">
                        <History size={16} /> History
                    </Link>
                    <button onClick={handleNewSession} className="px-5 py-2 rounded-full bg-slate-800 dark:bg-white/10 text-white dark:text-[#E6D5B8] border border-transparent dark:border-[#E6D5B8]/20 text-sm font-medium tracking-wide hover:bg-slate-700 dark:hover:bg-white/20 transition shadow-lg shadow-black/10 flex items-center gap-2">
                        <PlusCircle size={16} /> New Session
                    </button>
                    {isAuthenticated && (
                        <div className="relative">
                            <button onClick={() => setUserMenuOpen(!isUserMenuOpen)} className="w-10 h-10 rounded-full border border-slate-300 dark:border-white/10 hover:bg-white/5 transition text-slate-500 dark:text-slate-400 flex items-center justify-center">
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

                {/* LEFT: Property Card - exact positioning from reference */}
                <div className="hidden lg:block absolute left-[10%] top-[25%] w-80 transform transition-transform hover:scale-105 duration-700">
                    <div className="relative glass-panel rounded-2xl p-5 group hover:border-[#A3B18A]/30 transition-colors">
                        <div className="absolute -top-[1px] -left-[1px] w-4 h-4 border-t border-l border-[#A3B18A]/60 rounded-tl-lg"></div>
                        <div className="relative overflow-hidden rounded-xl mb-4 h-44 bg-[#1C212B]/50">
                            {currentProperty.image_url ? (
                                <img alt="Property" className="w-full h-full object-cover opacity-90 group-hover:opacity-100 hologram-img" src={currentProperty.image_url} />
                            ) : (
                                <div className="w-full h-full bg-slate-300 dark:bg-slate-800 flex items-center justify-center">
                                    <MaterialIcon name="apartment" className="text-slate-400 dark:text-white/20" size="48px" />
                                </div>
                            )}
                            <div className="absolute top-3 left-3 px-3 py-1 bg-[#1C212B]/40 border border-white/20 text-[#E8E8E3] text-[10px] font-bold uppercase rounded-md backdrop-blur-md tracking-wider">Top Pick</div>
                        </div>
                        <div className="space-y-3">
                            <div className="flex justify-between items-start">
                                <div>
                                    <h3 className="text-lg font-medium leading-tight text-slate-800 dark:text-slate-100 font-sans">{currentProperty.title}</h3>
                                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-display uppercase tracking-wide">{currentProperty.location}</p>
                                </div>
                                <div className="flex items-center gap-1 text-[#E6D5B8]">
                                    <MaterialIcon name="star" className="text-sm" />
                                    <span className="text-sm font-bold">{currentProperty.rating || 5.0}</span>
                                </div>
                            </div>
                            <div className="text-2xl font-light text-[#A3B18A] font-display">{currentProperty.price.toLocaleString()} <span className="text-base text-slate-500">EGP</span></div>
                            <div className="grid grid-cols-3 gap-2 mt-4 pt-4 border-t border-slate-200 dark:border-white/5">
                                <div className="text-center"><MaterialIcon name="bed" className="text-slate-400 text-xs mb-1" /><p className="text-xs font-semibold text-slate-600 dark:text-slate-300">{currentProperty.bedrooms} Bed</p></div>
                                <div className="text-center"><MaterialIcon name="bathtub" className="text-slate-400 text-xs mb-1" /><p className="text-xs font-semibold text-slate-600 dark:text-slate-300">{currentProperty.bathrooms} Bath</p></div>
                                <div className="text-center"><MaterialIcon name="square_foot" className="text-slate-400 text-xs mb-1" /><p className="text-xs font-semibold text-slate-600 dark:text-slate-300">{currentProperty.size_sqm}m²</p></div>
                            </div>
                        </div>
                        <div className="absolute top-1/2 -right-16 w-16 h-[1px] bg-gradient-to-r from-white/20 to-transparent"></div>
                        <div className="absolute top-1/2 -right-[66px] w-2 h-2 rounded-full bg-white/20 blur-[1px]"></div>
                    </div>
                </div>

                {/* CENTER: Agentic Core Panel */}
                <div className="relative z-20 w-full max-w-2xl mx-4 lg:mx-0 transform transition-all duration-700">
                    <div className="absolute -inset-1 bg-gradient-to-r from-[#A3B18A]/20 via-[#E6D5B8]/10 to-[#D4A3A3]/20 rounded-3xl blur-xl opacity-30 dark:opacity-40 animate-pulse"></div>
                    <div className="relative glass-panel bg-white/80 dark:bg-[#1C212B]/40 rounded-2xl p-6 lg:p-10 shadow-soft-glow">
                        {/* Header */}
                        <div className="flex items-center gap-4 mb-8 border-b border-slate-200 dark:border-white/5 pb-6">
                            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#A3B18A]/20 to-[#1C212B] border border-[#A3B18A]/20 flex items-center justify-center">
                                <MaterialIcon name="auto_awesome" className="text-[#A3B18A] font-light" />
                            </div>
                            <div>
                                <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-slate-400 dark:text-slate-400 mb-1">Agentic Core</h2>
                                <span className="text-sm text-[#A3B18A]/80 font-display flex items-center gap-2">
                                    {showProcessing ? 'Processing Market Data' : 'Analysis Complete'}
                                    {showProcessing && <span className="flex space-x-1">{[0, 0.2, 0.4].map((d, i) => <span key={i} className="w-1 h-1 bg-[#A3B18A] rounded-full animate-bounce" style={{ animationDelay: `${d}s` }}></span>)}</span>}
                                </span>
                            </div>
                        </div>

                        {/* Content */}
                        <div className="text-right font-sans text-lg leading-loose text-slate-700 dark:text-[#E8E8E3] space-y-6" dir="rtl">
                            {displayContent ? (
                                <div className="prose prose-lg dark:prose-invert max-w-none prose-p:text-slate-700 dark:prose-p:text-[#E8E8E3] prose-p:leading-loose prose-strong:text-[#A3B18A] prose-a:text-[#A3B18A]">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{displayContent}</ReactMarkdown>
                                </div>
                            ) : (
                                <>
                                    <p className="text-slate-900 dark:text-white font-medium">أهلاً بيك يا {getUserName()}! التجمع الخامس اختيار ممتاز.</p>
                                    <p className="text-slate-600 dark:text-gray-300 font-light">بص، متوسط أسعار الشقق في التجمع الخامس بيبدأ من <span className="text-[#E6D5B8] font-bold px-1">5.4</span> مليون جنيه لحد <span className="text-[#E6D5B8] font-bold px-1">18.1</span> مليون جنيه. الفرق ده بيكون حسب المطور والموقع.</p>
                                    <div className="p-4 bg-[#A3B18A]/5 border border-[#A3B18A]/10 rounded-xl relative overflow-hidden group">
                                        <div className="absolute top-0 right-0 w-1 h-full bg-[#A3B18A]/40"></div>
                                        <p className="text-slate-700 dark:text-gray-200">من الخيارات اللي عندي دلوقتي، في شقة في مشروع <span className="font-bold text-[#A3B18A]">السراي</span> بسعر 5.38 مليون جنيه، مساحتها 81 متر مربع، 1 نوم و2 حمام. الشقة دي الـ AI بتاعي قيمها بـ 50 على 100، يعني لقطة.</p>
                                    </div>
                                    <p className="text-sm text-slate-500 dark:text-slate-500 mt-6 font-display tracking-wide">تحب نحجز ميعاد معاينة للشقة دي يا {getUserName()}؟ عشان تشوفها على الطبيعة وأقدر أجبلك تفاصيل القسط الشهري.</p>
                                </>
                            )}
                        </div>

                        {/* Charts */}
                        {visualizations.length > 0 && (
                            <div className="mt-6 space-y-4">
                                {visualizations.map((viz: any, idx: number) => {
                                    let chartData = viz.type === 'inflation_killer' && viz.data?.projections ? viz.data.projections : viz.data;
                                    if (!Array.isArray(chartData) || chartData.length === 0) return null;
                                    return (
                                        <div key={idx} className="glass-panel rounded-xl p-4 bg-white/50 dark:bg-white/5">
                                            <ChartVisualization type={viz.type === 'inflation_killer' ? 'line' : viz.type || 'bar'} title={viz.title || 'Analysis'} data={chartData} labels={viz.labels || []} trend={viz.trend} subtitle={viz.subtitle} />
                                        </div>
                                    );
                                })}
                            </div>
                        )}

                        {/* Buttons */}
                        <div className="mt-8 flex flex-wrap gap-4 justify-end" dir="rtl">
                            <button className="px-5 py-2.5 bg-slate-100 dark:bg-white/5 hover:bg-slate-200 dark:hover:bg-white/10 border border-transparent dark:border-white/5 rounded-xl text-sm text-slate-600 dark:text-slate-300 transition-all flex items-center gap-2 shadow-sm">
                                <MaterialIcon name="calendar_today" className="text-lg" /> حجز معاينة
                            </button>
                            <button className="px-5 py-2.5 bg-[#A3B18A]/10 border border-[#A3B18A]/30 text-[#A3B18A] hover:bg-[#A3B18A]/20 rounded-xl text-sm transition-all flex items-center gap-2 shadow-sm">
                                <MaterialIcon name="visibility" className="text-lg" /> عرض التفاصيل
                            </button>
                        </div>
                    </div>
                </div>

                {/* RIGHT: Listing Insights - exact positioning from reference */}
                <div className="hidden lg:block absolute right-[5%] top-[20%] w-72 transform transition-transform hover:scale-105 duration-700">
                    <div className="relative glass-panel rounded-2xl p-6 hover:border-[#D4A3A3]/30 transition-colors group">
                        <div className="absolute -bottom-[1px] -right-[1px] w-4 h-4 border-b border-r border-[#D4A3A3]/60 rounded-br-lg"></div>
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400">Listing Insights</h3>
                            <MaterialIcon name="analytics" className="text-[#D4A3A3]/70 text-lg" />
                        </div>
                        <div className="space-y-6">
                            <div>
                                <div className="flex justify-between text-xs text-slate-500 mb-2 font-display uppercase tracking-wider"><span>Cap Rate</span><span className="text-[#A3B18A]">High</span></div>
                                <div className="text-3xl font-light text-slate-800 dark:text-white font-display">{capRate}%</div>
                                <div className="w-full bg-slate-200 dark:bg-white/5 h-1.5 mt-2 rounded-full overflow-hidden"><div className="bg-gradient-to-r from-[#D4A3A3] to-[#A3B18A] w-[80%] h-full rounded-full opacity-80"></div></div>
                            </div>
                            <div>
                                <div className="flex justify-between text-xs text-slate-500 mb-1 font-display uppercase tracking-wider"><span>Price / SQM</span></div>
                                <div className="text-2xl font-light text-slate-800 dark:text-white font-display">{pricePerSqm.toLocaleString()} <span className="text-sm text-slate-500">EGP</span></div>
                            </div>
                            <div>
                                <div className="flex justify-between text-xs text-slate-500 mb-2 font-display uppercase tracking-wider"><span>Walk Score</span><span className="text-[#E6D5B8] font-bold">{walkScore}/100</span></div>
                                <div className="h-16 w-full flex items-end gap-1 mt-2">
                                    <div className="w-1/6 bg-[#D4A3A3] h-[40%] rounded-t-sm opacity-20"></div>
                                    <div className="w-1/6 bg-[#D4A3A3] h-[60%] rounded-t-sm opacity-30"></div>
                                    <div className="w-1/6 bg-[#D4A3A3] h-[30%] rounded-t-sm opacity-40"></div>
                                    <div className="w-1/6 bg-[#A3B18A] h-[80%] rounded-t-sm opacity-50"></div>
                                    <div className="w-1/6 bg-[#A3B18A] h-[90%] rounded-t-sm opacity-70"></div>
                                    <div className="w-1/6 bg-[#A3B18A] h-[50%] rounded-t-sm opacity-90"></div>
                                </div>
                            </div>
                        </div>
                        <div className="absolute top-1/2 -left-16 w-16 h-[1px] bg-gradient-to-l from-white/20 to-transparent"></div>
                    </div>
                </div>

                {/* BOTTOM-RIGHT: ROI Panel - exact positioning from reference */}
                <div className="hidden lg:block absolute right-[15%] bottom-[15%] w-64 transform transition-transform hover:scale-105 duration-700">
                    <div className="relative glass-panel rounded-2xl p-5 hover:border-[#A3B18A]/40 transition-colors">
                        <div className="flex items-center justify-between mb-3">
                            <span className="text-[10px] font-bold tracking-widest uppercase text-slate-400">Proj. Annual ROI</span>
                            <MaterialIcon name="trending_up" className="text-[#A3B18A] text-sm" />
                        </div>
                        <div className="text-3xl font-light text-[#A3B18A] font-display">12.5%</div>
                        <p className="text-[10px] text-slate-500 mt-2 leading-tight">Based on recent market trends in New Cairo.</p>
                        <div className="absolute -top-12 left-1/2 w-[1px] h-12 bg-gradient-to-b from-transparent to-white/20"></div>
                    </div>
                </div>
            </main>

            {/* BOTTOM-LEFT: Floating Controls - exact positioning from reference */}
            <div className="absolute bottom-8 left-8 flex flex-col gap-3 z-50">
                {['add', 'remove', 'my_location'].map(icon => (
                    <button key={icon} className="w-11 h-11 rounded-xl bg-white/5 dark:bg-[#1C212B]/50 border border-slate-200 dark:border-white/10 text-slate-500 dark:text-slate-400 backdrop-blur-md flex items-center justify-center hover:bg-[#A3B18A]/20 hover:text-[#A3B18A] hover:border-[#A3B18A]/30 transition-all shadow-lg">
                        <MaterialIcon name={icon} className="text-xl" />
                    </button>
                ))}
            </div>

            {/* BOTTOM: Input - exact positioning from reference */}
            <div className="absolute bottom-10 left-1/2 -translate-x-1/2 w-full max-w-2xl px-6 z-50">
                <div className="relative group">
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
                </div>
            </div>

            <ContextualPane isOpen={!!selectedProperty} onClose={() => setSelectedProperty(null)} property={selectedProperty} isRTL={language === 'ar'} />
            <InvitationModal isOpen={isInvitationModalOpen} onClose={() => setInvitationModalOpen(false)} />
        </div>
    );
}
