'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Send,
    Sparkles,
    Menu,
    Plus,
    PanelLeftClose,
    PanelLeft,
    Copy,
    Check,
    ChevronDown,
    Zap,
    Search,
    Calculator,
    TrendingUp,
    GitCompare,
    Calendar,
    MapPin,
    DollarSign,
    BarChart3,
    Home,
    Loader2
} from 'lucide-react';
import ConversationHistory from './ConversationHistory';
import VisualizationRenderer from './visualizations/VisualizationRenderer';
import ThemeToggle from './ThemeToggle';
import api from '../lib/api';

// Types
type UIAction = {
    type: string;
    priority: number;
    data: any;
    trigger_reason?: string;
    chart_reference?: string;
};

type Property = {
    id: number;
    title: string;
    price: number;
    location: string;
    size_sqm: number;
    bedrooms: number;
    wolf_score?: number;
    valuation_verdict?: string;
    la2ta_score?: number;
    [key: string]: any;
};

type Message = {
    id: string;
    role: 'user' | 'amr';
    content: string;
    visualizations?: UIAction[];
    properties?: Property[];
    psychology?: any;
    timestamp?: Date;
    copied?: boolean;
    isTyping?: boolean;
};

// Class A Developers List
const CLASS_A_DEVELOPERS = [
    'al marasem', 'المراسم', 'marakez', 'مراكز', 'sodic', 'سوديك',
    'emaar', 'إعمار', 'mountain view', 'ماونتن فيو', 'lake view', 'ليك فيو',
    'la vista', 'لافيستا', 'lavista'
];

const isClassADeveloper = (developer: string | undefined): boolean => {
    if (!developer) return false;
    const devLower = developer.toLowerCase().trim();
    return CLASS_A_DEVELOPERS.some(d => devLower.includes(d) || d.includes(devLower));
};

// Enhanced Typewriter Hook V2 - Variable speed based on character type
function useTypewriter(text: string, baseSpeed: number = 12, enabled: boolean = true) {
    const [displayedText, setDisplayedText] = useState('');
    const [isComplete, setIsComplete] = useState(false);

    useEffect(() => {
        if (!enabled) {
            setDisplayedText(text);
            setIsComplete(true);
            return;
        }

        setDisplayedText('');
        setIsComplete(false);
        let index = 0;
        let timeoutId: NodeJS.Timeout;

        const typeNext = () => {
            if (index < text.length) {
                const char = text[index];
                setDisplayedText(text.slice(0, index + 1));
                index++;

                // Variable speed based on character type
                let delay = baseSpeed;

                // Long pause on sentence endings
                if (['.', '!', '?', '،', '؟', '。'].includes(char)) {
                    delay = baseSpeed * 6;
                }
                // Medium pause on punctuation
                else if ([',', ':', ';', '؛', '-', '–'].includes(char)) {
                    delay = baseSpeed * 3;
                }
                // Slight pause on spaces
                else if (char === ' ') {
                    delay = baseSpeed * 1.3;
                }
                // Slightly faster for Arabic (flows better)
                else if (/[\u0600-\u06FF]/.test(char)) {
                    delay = baseSpeed * 0.9;
                }
                // Emojis get a pause
                else if (/[\u{1F300}-\u{1F9FF}]/u.test(char)) {
                    delay = baseSpeed * 2;
                }

                timeoutId = setTimeout(typeNext, delay);
            } else {
                setIsComplete(true);
            }
        };

        timeoutId = setTimeout(typeNext, 50);
        return () => clearTimeout(timeoutId);
    }, [text, baseSpeed, enabled]);

    return { displayedText, isComplete };
}

// Format price
const formatPrice = (price: number): string => {
    if (price >= 1_000_000) {
        return `${(price / 1_000_000).toFixed(1)}M EGP`;
    }
    return `${(price / 1_000).toFixed(0)}K EGP`;
};

// Property Card
function PropertyCard({ property, delay = 0 }: { property: Property; delay?: number }) {
    const isClassA = isClassADeveloper(property.developer);

    return (
        <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ delay, type: "spring", stiffness: 400, damping: 25 }}
            whileHover={{ y: -4, transition: { duration: 0.2 } }}
            className={`group relative bg-[var(--color-surface)] rounded-2xl p-5
                       border hover:border-[var(--color-primary)]
                       shadow-sm hover:shadow-xl transition-all duration-300 cursor-pointer
                       ${isClassA ? 'border-amber-500/30 ring-1 ring-amber-500/10' : 'border-[var(--color-border)]'}`}
        >
            {/* Glow effect on hover */}
            <div className={`absolute inset-0 rounded-2xl transition-all duration-500
                          ${isClassA
                            ? 'bg-gradient-to-br from-amber-500/5 to-orange-500/5 group-hover:from-amber-500/10 group-hover:to-orange-500/10'
                            : 'bg-gradient-to-br from-emerald-500/0 to-teal-500/0 group-hover:from-emerald-500/5 group-hover:to-teal-500/5'}`} />

            <div className="relative">
                {/* Class A Badge */}
                {isClassA && (
                    <motion.div
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: delay + 0.1 }}
                        className="absolute -top-2 -right-2 z-10"
                    >
                        <span className="text-xs bg-gradient-to-r from-amber-500 to-orange-500
                                       text-white px-2.5 py-1 rounded-full font-bold shadow-lg shadow-amber-500/30
                                       flex items-center gap-1">
                            🏆 Class A
                        </span>
                    </motion.div>
                )}

                <div className="flex justify-between items-start mb-3">
                    <h4 className="font-semibold text-[var(--color-text-primary)] text-sm line-clamp-1 flex-1 pr-2">
                        {property.title}
                    </h4>
                    {property.wolf_score && (
                        <motion.span
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            transition={{ delay: delay + 0.2, type: "spring" }}
                            className={`text-xs font-bold px-2.5 py-1 rounded-full flex-shrink-0 ${property.wolf_score >= 80
                                    ? 'bg-emerald-500/15 text-emerald-500 ring-1 ring-emerald-500/30'
                                    : property.wolf_score >= 60
                                        ? 'bg-amber-500/15 text-amber-500 ring-1 ring-amber-500/30'
                                        : 'bg-[var(--color-surface-elevated)] text-[var(--color-text-muted)]'
                                }`}
                        >
                            {property.wolf_score}/100
                        </motion.span>
                    )}
                </div>

                <p className="text-xs text-[var(--color-text-muted)] mb-4 flex items-center gap-2 flex-wrap">
                    <span className="flex items-center gap-1">📍 {property.location}</span>
                    <span className="w-1 h-1 rounded-full bg-[var(--color-border)]" />
                    <span>{property.size_sqm} sqm</span>
                    <span className="w-1 h-1 rounded-full bg-[var(--color-border)]" />
                    <span>{property.bedrooms} bed</span>
                </p>

                {/* Developer name with Class A indicator */}
                {property.developer && (
                    <p className={`text-xs mb-3 font-medium ${isClassA ? 'text-amber-500' : 'text-[var(--color-text-muted)]'}`}>
                        {isClassA && '⭐ '}{property.developer}
                    </p>
                )}

                <div className="flex justify-between items-center">
                    <span className="text-[var(--color-primary)] font-bold text-lg">
                        {formatPrice(property.price)}
                    </span>
                    {property.valuation_verdict === 'BARGAIN' && (
                        <motion.span
                            initial={{ scale: 0, rotate: -10 }}
                            animate={{ scale: 1, rotate: 0 }}
                            transition={{ delay: delay + 0.3, type: "spring" }}
                            className="text-xs bg-gradient-to-r from-emerald-500 to-teal-500
                                     text-white px-3 py-1.5 rounded-full font-medium shadow-lg shadow-emerald-500/25"
                        >
                            🐺 La2ta!
                        </motion.span>
                    )}
                </div>
            </div>
        </motion.div>
    );
}

// Typewriter Message Component
function TypewriterMessage({
    content,
    isNew,
    onComplete
}: {
    content: string;
    isNew: boolean;
    onComplete?: () => void;
}) {
    const { displayedText, isComplete } = useTypewriter(content, 12, isNew);

    useEffect(() => {
        if (isComplete && onComplete) {
            onComplete();
        }
    }, [isComplete, onComplete]);

    return (
        <div className="text-sm leading-relaxed whitespace-pre-wrap" dir="auto">
            {displayedText}
            {!isComplete && (
                <motion.span
                    animate={{ opacity: [1, 0] }}
                    transition={{ duration: 0.5, repeat: Infinity }}
                    className="inline-block w-0.5 h-4 bg-[var(--color-primary)] ml-0.5 align-middle"
                />
            )}
        </div>
    );
}

// Message Component
function ChatMessage({
    message,
    onCopy,
    isLatest,
    onQuickAction
}: {
    message: Message;
    onCopy: (id: string) => void;
    isLatest: boolean;
    onQuickAction?: (prompt: string) => void;
}) {
    const isUser = message.role === 'user';
    const [showExtras, setShowExtras] = useState(!isLatest || isUser);

    // Determine quick action context based on message content
    const getQuickActionContext = () => {
        if (message.properties && message.properties.length > 0) return 'property_shown';
        if (message.visualizations && message.visualizations.length > 0) return 'search_complete';
        return 'default';
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ type: "spring", stiffness: 400, damping: 25 }}
            className={`group flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
        >
            {/* AMR Avatar */}
            {!isUser && (
                <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: "spring", stiffness: 500, damping: 25 }}
                    className="flex-shrink-0 mt-1"
                >
                    <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 
                                  flex items-center justify-center text-white text-sm font-bold 
                                  shadow-lg shadow-emerald-500/30 ring-2 ring-emerald-500/20">
                        A
                    </div>
                </motion.div>
            )}

            <div className={`flex flex-col max-w-[85%] md:max-w-[75%] space-y-3`}>
                {/* Message Bubble */}
                <motion.div
                    layout
                    className={`relative rounded-2xl px-5 py-4 ${isUser
                            ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-br-md shadow-lg shadow-emerald-500/20'
                            : 'glass border border-[var(--color-border)] text-[var(--color-text-primary)] rounded-bl-md shadow-md'
                        }`}
                >
                    {isUser ? (
                        <div className="text-sm leading-relaxed whitespace-pre-wrap" dir="auto">
                            {message.content}
                        </div>
                    ) : (
                        <TypewriterMessage
                            content={message.content}
                            isNew={isLatest}
                            onComplete={() => setShowExtras(true)}
                        />
                    )}

                    {/* Copy Button */}
                    {!isUser && (
                        <motion.button
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            onClick={() => onCopy(message.id)}
                            className="absolute -bottom-2 right-3 opacity-0 group-hover:opacity-100 
                                     transition-all duration-200 bg-[var(--color-surface)] rounded-full p-2 
                                     shadow-lg border border-[var(--color-border)] hover:border-[var(--color-primary)]
                                     hover:scale-110 active:scale-95"
                        >
                            {message.copied ? (
                                <Check size={12} className="text-emerald-500" />
                            ) : (
                                <Copy size={12} className="text-[var(--color-text-muted)]" />
                            )}
                        </motion.button>
                    )}
                </motion.div>

                {/* Visualizations */}
                <AnimatePresence>
                    {showExtras && message.visualizations && message.visualizations.length > 0 && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="space-y-3"
                        >
                            {message.visualizations.map((viz, idx) => (
                                <motion.div
                                    key={`${message.id}-viz-${idx}`}
                                    initial={{ opacity: 0, y: 15, scale: 0.95 }}
                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                    transition={{ delay: idx * 0.15, type: "spring" }}
                                    className="rounded-2xl overflow-hidden border border-[var(--color-border)] 
                                              bg-[var(--color-surface)] shadow-xl"
                                >
                                    <VisualizationRenderer type={viz.type} data={viz.data} />
                                </motion.div>
                            ))}
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Property Cards */}
                <AnimatePresence>
                    {showExtras && message.properties && message.properties.length > 0 && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="mt-3 grid gap-4 grid-cols-1 lg:grid-cols-2"
                        >
                            {message.properties.slice(0, 4).map((prop, idx) => (
                                <PropertyCard key={prop.id} property={prop} delay={idx * 0.1} />
                            ))}
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Quick Actions - Show after AMR response with content */}
                {!isUser && showExtras && isLatest && onQuickAction && (
                    <QuickActions
                        context={getQuickActionContext()}
                        onAction={onQuickAction}
                    />
                )}
            </div>

            {isUser && <div className="w-10 flex-shrink-0" />}
        </motion.div>
    );
}

// Tool metadata for execution indicators
const TOOL_METADATA: Record<string, { icon: React.ElementType; label_ar: string; label_en: string }> = {
    'search_properties': { icon: Search, label_ar: 'جاري البحث عن العقارات...', label_en: 'Searching properties...' },
    'run_valuation_ai': { icon: Calculator, label_ar: 'جاري التقييم...', label_en: 'Running valuation...' },
    'calculate_mortgage': { icon: DollarSign, label_ar: 'حساب القسط الشهري...', label_en: 'Calculating mortgage...' },
    'check_market_trends': { icon: TrendingUp, label_ar: 'تحليل اتجاهات السوق...', label_en: 'Analyzing market trends...' },
    'compare_units': { icon: GitCompare, label_ar: 'مقارنة العقارات...', label_en: 'Comparing properties...' },
    'schedule_viewing': { icon: Calendar, label_ar: 'حجز موعد المعاينة...', label_en: 'Scheduling viewing...' },
    'check_area': { icon: MapPin, label_ar: 'تحليل المنطقة...', label_en: 'Analyzing area...' },
    'investment_analysis': { icon: BarChart3, label_ar: 'تحليل الاستثمار...', label_en: 'Analyzing investment...' },
    'default': { icon: Loader2, label_ar: 'جاري التحليل...', label_en: 'Processing...' },
};

// Tool Execution Indicator Component
function ToolExecutionIndicator({ tool, status = 'running' }: { tool: string; status?: 'running' | 'complete' }) {
    const metadata = TOOL_METADATA[tool] || TOOL_METADATA['default'];
    const Icon = metadata.icon;

    return (
        <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -5, scale: 0.95 }}
            className="flex items-center gap-3 px-4 py-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20"
        >
            <motion.div
                animate={status === 'running' ? { rotate: 360 } : {}}
                transition={{ duration: 1, repeat: status === 'running' ? Infinity : 0, ease: 'linear' }}
            >
                <Icon className="w-5 h-5 text-emerald-500" />
            </motion.div>
            <span className="text-sm text-emerald-400">{metadata.label_ar}</span>
            {status === 'complete' && <Check className="w-4 h-4 text-emerald-500 ml-auto" />}
        </motion.div>
    );
}

// Quick Actions Component
type QuickAction = {
    id: string;
    label_ar: string;
    label_en: string;
    icon: React.ElementType;
    prompt: string;
    variant: 'primary' | 'secondary' | 'ghost';
};

const QUICK_ACTIONS: Record<string, QuickAction[]> = {
    'property_shown': [
        { id: 'schedule', label_ar: 'حجز معاينة', label_en: 'Schedule Viewing', icon: Calendar, prompt: 'عايز أحجز معاينة للعقار ده', variant: 'primary' },
        { id: 'compare', label_ar: 'قارن مع عقارات تانية', label_en: 'Compare', icon: GitCompare, prompt: 'قارنلي العقار ده مع عقارات تانية مشابهة', variant: 'secondary' },
        { id: 'mortgage', label_ar: 'احسب القسط', label_en: 'Calculate Mortgage', icon: Calculator, prompt: 'احسبلي القسط الشهري للعقار ده', variant: 'ghost' },
    ],
    'search_complete': [
        { id: 'filter_price', label_ar: 'غير الميزانية', label_en: 'Adjust Budget', icon: DollarSign, prompt: 'عايز أشوف في ميزانية تانية', variant: 'secondary' },
        { id: 'filter_location', label_ar: 'منطقة تانية', label_en: 'Different Area', icon: MapPin, prompt: 'ورني في منطقة تانية', variant: 'secondary' },
        { id: 'class_a', label_ar: 'مطورين الفئة الأولى', label_en: 'Class A Developers', icon: Home, prompt: 'ورني من مطورين الفئة الأولى بس', variant: 'ghost' },
    ],
    'default': [
        { id: 'search', label_ar: 'ابحث عن عقار', label_en: 'Search Properties', icon: Search, prompt: 'عايز أدور على شقة في التجمع', variant: 'primary' },
        { id: 'valuation', label_ar: 'قيم عقار', label_en: 'Valuation', icon: BarChart3, prompt: 'عايز تقييم لعقار', variant: 'secondary' },
        { id: 'market', label_ar: 'تحليل السوق', label_en: 'Market Analysis', icon: TrendingUp, prompt: 'إيه أحسن منطقة للاستثمار دلوقتي؟', variant: 'ghost' },
    ]
};

function QuickActions({ context, onAction }: { context: string; onAction: (prompt: string) => void }) {
    const actions = QUICK_ACTIONS[context] || QUICK_ACTIONS['default'];

    return (
        <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="flex flex-wrap gap-2 mt-4"
        >
            {actions.map((action, idx) => {
                const Icon = action.icon;
                return (
                    <motion.button
                        key={action.id}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.4 + idx * 0.1 }}
                        whileHover={{ scale: 1.02, y: -1 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => onAction(action.prompt)}
                        className={`px-4 py-2.5 rounded-xl flex items-center gap-2 text-sm font-medium transition-all duration-200
                            ${action.variant === 'primary'
                                ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/40'
                                : action.variant === 'secondary'
                                    ? 'bg-[var(--color-surface-elevated)] border border-[var(--color-border)] text-[var(--color-text-primary)] hover:border-[var(--color-primary)]'
                                    : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-elevated)] hover:text-[var(--color-text-primary)]'}`}
                    >
                        <Icon size={16} />
                        {action.label_ar}
                    </motion.button>
                );
            })}
        </motion.div>
    );
}

// Typing Indicator
function TypingIndicator({ currentTool }: { currentTool?: string }) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="flex flex-col gap-3"
        >
            <div className="flex items-center gap-3">
                <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="w-10 h-10 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500
                              flex items-center justify-center text-white text-sm font-bold
                              shadow-lg shadow-emerald-500/30 ring-2 ring-emerald-500/20"
                >
                    A
                </motion.div>
                <div className="flex items-center gap-2 glass px-5 py-4 rounded-2xl rounded-bl-md
                              border border-[var(--color-border)] shadow-md">
                    <Zap size={14} className="text-emerald-500" />
                    <span className="text-sm text-[var(--color-text-secondary)]">Thinking</span>
                    <motion.div className="flex gap-1">
                        {[0, 1, 2].map((i) => (
                            <motion.span
                                key={i}
                                animate={{ scale: [1, 1.3, 1], opacity: [0.5, 1, 0.5] }}
                                transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.15 }}
                                className="w-2 h-2 bg-emerald-500 rounded-full"
                            />
                        ))}
                    </motion.div>
                </div>
            </div>
            {/* Show current tool execution */}
            <AnimatePresence>
                {currentTool && (
                    <div className="ml-13 pl-13">
                        <ToolExecutionIndicator tool={currentTool} />
                    </div>
                )}
            </AnimatePresence>
        </motion.div>
    );
}

// Empty State
function EmptyState({ onSuggestionClick }: { onSuggestionClick: (text: string) => void }) {
    const suggestions = [
        { text: "عايز شقة في التجمع تحت 5 مليون", icon: "🏠", color: "from-blue-500 to-cyan-500" },
        { text: "قارنلي بين زايد والتجمع للاستثمار", icon: "📊", color: "from-purple-500 to-pink-500" },
        { text: "إيه أحسن منطقة للعائد الإيجاري؟", icon: "💰", color: "from-amber-500 to-orange-500" },
        { text: "Show me properties in New Cairo", icon: "🔍", color: "from-emerald-500 to-teal-500" }
    ];

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center h-full text-center px-4 py-8"
        >
            {/* Animated Logo */}
            <motion.div
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ type: "spring", stiffness: 200, damping: 15 }}
                className="relative mb-8"
            >
                <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-emerald-500 to-teal-500 
                              flex items-center justify-center shadow-2xl shadow-emerald-500/40
                              ring-4 ring-emerald-500/20">
                    <span className="text-5xl font-bold text-white">A</span>
                </div>
                <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="absolute -bottom-1 -right-1 w-6 h-6 bg-emerald-400 rounded-full 
                              border-4 border-[var(--color-background)]"
                />
            </motion.div>

            <motion.h2
                initial={{ y: 30, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="text-4xl font-bold text-[var(--color-text-primary)] mb-3"
            >
                Ahlan! Ana Amr 👋
            </motion.h2>

            <motion.p
                initial={{ y: 30, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="text-[var(--color-text-secondary)] mb-10 max-w-lg text-lg leading-relaxed"
            >
                Your AI Real Estate Consultant. I help you find verified properties
                and protect your investment in Egypt.
            </motion.p>

            <motion.div
                initial={{ y: 30, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="grid gap-3 w-full max-w-xl"
            >
                <p className="text-xs text-[var(--color-text-muted)] uppercase tracking-widest mb-2 font-semibold">
                    ✨ Try asking
                </p>
                {suggestions.map((suggestion, idx) => (
                    <motion.button
                        key={idx}
                        initial={{ x: idx % 2 === 0 ? -30 : 30, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ delay: 0.5 + idx * 0.1, type: "spring" }}
                        whileHover={{ scale: 1.02, x: 5 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => onSuggestionClick(suggestion.text)}
                        className="group text-left px-5 py-4 rounded-2xl border border-[var(--color-border)] 
                                 bg-[var(--color-surface)] text-[var(--color-text-secondary)] text-sm 
                                 hover:border-[var(--color-primary)] hover:shadow-lg
                                 transition-all duration-300 flex items-center gap-4"
                    >
                        <span className={`w-10 h-10 rounded-xl bg-gradient-to-br ${suggestion.color} 
                                       flex items-center justify-center text-lg shadow-md`}>
                            {suggestion.icon}
                        </span>
                        <span className="group-hover:text-[var(--color-text-primary)] transition-colors flex-1">
                            {suggestion.text}
                        </span>
                        <motion.span
                            initial={{ x: 0, opacity: 0 }}
                            whileHover={{ x: 5, opacity: 1 }}
                            className="text-[var(--color-primary)]"
                        >
                            →
                        </motion.span>
                    </motion.button>
                ))}
            </motion.div>
        </motion.div>
    );
}

// Main Chat Interface
export default function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
    const [showScrollButton, setShowScrollButton] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
        }
    }, [messages, isTyping]);

    const handleScroll = useCallback(() => {
        if (scrollRef.current) {
            const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
            setShowScrollButton(scrollHeight - scrollTop - clientHeight > 100);
        }
    }, []);

    const scrollToBottom = () => {
        scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    };

    const handleCopy = (messageId: string) => {
        const message = messages.find(m => m.id === messageId);
        if (message) {
            navigator.clipboard.writeText(message.content);
            setMessages(prev => prev.map(m =>
                m.id === messageId ? { ...m, copied: true } : m
            ));
            setTimeout(() => {
                setMessages(prev => prev.map(m =>
                    m.id === messageId ? { ...m, copied: false } : m
                ));
            }, 2000);
        }
    };

    const handleSend = async (text?: string) => {
        const messageText = text || input.trim();
        if (!messageText || isTyping) return;

        const userMessage: Message = {
            id: `user-${Date.now()}`,
            role: 'user',
            content: messageText,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsTyping(true);

        if (inputRef.current) {
            inputRef.current.style.height = 'auto';
        }

        try {
            const { data } = await api.post('/api/chat', { message: messageText });

            const amrMessage: Message = {
                id: `amr-${Date.now()}`,
                role: 'amr',
                content: data.response || data.message || "عذراً، حصل مشكلة. جرب تاني يا باشا.",
                visualizations: data.ui_actions || [],
                properties: data.properties || [],
                psychology: data.psychology,
                timestamp: new Date()
            };

            setMessages(prev => [...prev, amrMessage]);
        } catch (error) {
            console.error("Chat error:", error);
            const errorMessage: Message = {
                id: `error-${Date.now()}`,
                role: 'amr',
                content: "عذراً، فيه مشكلة في الاتصال. جرب تاني بعد شوية يا باشا.",
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsTyping(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setInput(e.target.value);
        e.target.style.height = 'auto';
        e.target.style.height = Math.min(e.target.scrollHeight, 150) + 'px';
    };

    const handleNewConversation = () => {
        setMessages([]);
        setInput('');
    };

    return (
        <div className="flex h-screen bg-[var(--color-background)] overflow-hidden">
            {/* Desktop Sidebar */}
            <motion.div
                initial={false}
                animate={{ width: isSidebarCollapsed ? 0 : 300 }}
                transition={{ type: "spring", stiffness: 300, damping: 30 }}
                className="hidden md:flex flex-col bg-[var(--color-surface)] border-r border-[var(--color-border)] overflow-hidden"
            >
                <div className="p-5 border-b border-[var(--color-border)]">
                    <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={handleNewConversation}
                        className="w-full flex items-center justify-center gap-2 px-5 py-3.5 
                                 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-xl 
                                 font-semibold shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/40
                                 transition-all duration-300"
                    >
                        <Plus size={18} />
                        New Chat
                    </motion.button>
                </div>

                <div className="flex-1 overflow-y-auto p-3 custom-scrollbar">
                    <ConversationHistory
                        isOpen={true}
                        onClose={() => { }}
                        onSelectConversation={(id) => console.log("Selected:", id)}
                        onNewConversation={handleNewConversation}
                        isDesktopSidebar={true}
                    />
                </div>

                <div className="p-5 border-t border-[var(--color-border)] bg-[var(--color-surface-elevated)]">
                    <div className="flex items-center gap-3 text-[var(--color-text-muted)] text-xs">
                        <Sparkles size={14} className="text-emerald-500" />
                        <span>Powered by Wolf Brain V5</span>
                    </div>
                </div>
            </motion.div>

            {/* Sidebar Toggle */}
            <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
                className="hidden md:flex absolute top-1/2 -translate-y-1/2 z-20 
                         bg-[var(--color-surface)] border border-[var(--color-border)] 
                         hover:border-[var(--color-primary)] text-[var(--color-text-secondary)] 
                         p-2.5 rounded-r-xl transition-all duration-300 shadow-lg"
                style={{ left: isSidebarCollapsed ? 0 : 300 }}
            >
                {isSidebarCollapsed ? <PanelLeft size={16} /> : <PanelLeftClose size={16} />}
            </motion.button>

            {/* Mobile Sidebar */}
            <ConversationHistory
                isOpen={isSidebarOpen}
                onClose={() => setIsSidebarOpen(false)}
                onSelectConversation={(id) => {
                    console.log("Selected:", id);
                    setIsSidebarOpen(false);
                }}
                onNewConversation={() => {
                    handleNewConversation();
                    setIsSidebarOpen(false);
                }}
            />

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col h-full">
                {/* Header */}
                <header className="flex items-center justify-between px-4 md:px-6 py-4 
                               border-b border-[var(--color-border)] bg-[var(--color-surface)]/80 
                               backdrop-blur-2xl sticky top-0 z-10">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => setIsSidebarOpen(true)}
                            className="md:hidden p-2.5 text-[var(--color-text-secondary)] 
                                     hover:bg-[var(--color-surface-elevated)] rounded-xl transition-colors"
                        >
                            <Menu size={20} />
                        </button>
                        <div className="flex items-center gap-3">
                            <div className="relative">
                                <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 
                                              flex items-center justify-center text-white font-bold text-lg
                                              shadow-lg shadow-emerald-500/25 ring-2 ring-emerald-500/20">
                                    A
                                </div>
                                <motion.div
                                    animate={{ scale: [1, 1.2, 1] }}
                                    transition={{ duration: 2, repeat: Infinity }}
                                    className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-emerald-400 
                                              border-2 border-[var(--color-surface)] rounded-full"
                                />
                            </div>
                            <div>
                                <h3 className="font-semibold text-[var(--color-text-primary)] flex items-center gap-2 text-lg">
                                    Amr
                                    <span className="text-xs px-2 py-1 rounded-full bg-emerald-500/15 text-emerald-500 font-medium">
                                        Online
                                    </span>
                                </h3>
                                <p className="text-xs text-[var(--color-text-muted)]">
                                    Wolf of Osool • AI Real Estate Consultant
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <ThemeToggle />
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={handleNewConversation}
                            className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium 
                                     text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]
                                     hover:bg-[var(--color-surface-elevated)] rounded-xl transition-all"
                        >
                            <Plus size={16} />
                            <span className="hidden sm:inline">New Chat</span>
                        </motion.button>
                    </div>
                </header>

                {/* Messages Area */}
                <div
                    ref={scrollRef}
                    onScroll={handleScroll}
                    className="flex-1 overflow-y-auto px-4 md:px-8 py-8 space-y-6 custom-scrollbar"
                >
                    {messages.length === 0 ? (
                        <EmptyState onSuggestionClick={(text) => handleSend(text)} />
                    ) : (
                        <AnimatePresence mode="popLayout">
                            {messages.map((msg, idx) => (
                                <ChatMessage
                                    key={msg.id}
                                    message={msg}
                                    onCopy={handleCopy}
                                    isLatest={idx === messages.length - 1}
                                    onQuickAction={(prompt) => handleSend(prompt)}
                                />
                            ))}
                            {isTyping && <TypingIndicator currentTool="search_properties" />}
                        </AnimatePresence>
                    )}
                </div>

                {/* Scroll Button */}
                <AnimatePresence>
                    {showScrollButton && (
                        <motion.button
                            initial={{ opacity: 0, scale: 0.8, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.8, y: 20 }}
                            whileHover={{ scale: 1.1 }}
                            onClick={scrollToBottom}
                            className="absolute bottom-32 left-1/2 -translate-x-1/2 
                                     bg-[var(--color-surface)] border border-[var(--color-border)]
                                     text-[var(--color-text-secondary)] p-3 rounded-full shadow-xl 
                                     hover:border-[var(--color-primary)] transition-all"
                        >
                            <ChevronDown size={20} />
                        </motion.button>
                    )}
                </AnimatePresence>

                {/* Input Area */}
                <div className="border-t border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-2xl p-4 md:p-6">
                    <div className="max-w-4xl mx-auto">
                        <motion.div
                            className="relative flex items-end bg-[var(--color-surface-elevated)] 
                                      rounded-2xl border border-[var(--color-border)]
                                      shadow-lg hover:shadow-xl focus-within:border-[var(--color-primary)]
                                      focus-within:ring-4 focus-within:ring-[var(--color-primary-light)]
                                      transition-all duration-300"
                        >
                            <textarea
                                ref={inputRef}
                                value={input}
                                onChange={handleInputChange}
                                onKeyDown={handleKeyDown}
                                placeholder="اسأل عمرو عن أي حاجة في العقارات..."
                                rows={1}
                                className="flex-1 bg-transparent text-[var(--color-text-primary)] py-4 px-6 
                                         text-sm resize-none focus:outline-none max-h-[150px] 
                                         placeholder:text-[var(--color-text-muted)]"
                                dir="auto"
                            />
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={() => handleSend()}
                                disabled={!input.trim() || isTyping}
                                className="m-2.5 w-12 h-12 bg-gradient-to-r from-emerald-500 to-teal-500
                                         disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed 
                                         text-white rounded-xl flex items-center justify-center 
                                         transition-all duration-300 shadow-lg shadow-emerald-500/25 
                                         disabled:shadow-none hover:shadow-emerald-500/50"
                            >
                                <Send size={18} />
                            </motion.button>
                        </motion.div>

                        <p className="text-center mt-4 text-xs text-[var(--color-text-muted)] 
                                    flex items-center justify-center gap-2">
                            <Sparkles size={12} className="text-amber-500" />
                            <span>Powered by Osool Hybrid Brain V5 • Claude + GPT-4o + XGBoost</span>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
