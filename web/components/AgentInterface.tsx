'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams, useRouter as useNextRouter } from 'next/navigation';
import { motion, AnimatePresence, LayoutGroup } from 'framer-motion';
import {
    Sparkles, MapPin,
    X, ChevronRight,
    BarChart2, Shield, Search, TrendingUp,
    Copy, RefreshCw, ArrowUp,
    History, Plus, MessageSquare, Check
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import api from '@/lib/api';
import { streamChat } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { useGamification } from '@/contexts/GamificationContext';
import Link from 'next/link';
import { Lock, Heart, BarChart3, Scale } from 'lucide-react';
import { toggleFavorite } from '@/lib/gamification';
import type { VisualizationRendererProps } from '@/components/visualizations/VisualizationRenderer';
import dynamic from 'next/dynamic';
import SuggestionChips from '@/components/SuggestionChips';
import FunnelIndicator from '@/components/FunnelIndicator';
import MarketPulseSidebar from '@/components/MarketPulseSidebar';

const VisualizationRenderer = dynamic(
    () => import('@/components/visualizations/VisualizationRenderer'),
    { ssr: false }
);

/* Types */
interface PropertyMetrics {
    size: number;
    bedrooms: number;
    bathrooms: number;
    wolf_score: number;
    roi: number;
    price_per_sqm: number;
    liquidity_rating: string;
}

interface Property {
    id: string;
    title: string;
    location: string;
    price: number;
    currency: string;
    metrics: PropertyMetrics;
    image: string;
    developer: string;
    tags: string[];
    status: string;
}

interface ChatPropertyPayload {
    id?: string | number;
    title?: string;
    name?: string;
    location?: string;
    address?: string;
    price?: number;
    size_sqm?: number;
    size?: number;
    bedrooms?: number;
    bathrooms?: number;
    wolf_score?: number;
    projected_roi?: number;
    roi?: number;
    price_per_sqm?: number;
    liquidity_rating?: string;
    image_url?: string;
    image?: string;
    developer?: string;
    tags?: string[];
    status?: string;
}

interface UiActionArea {
    name?: string;
    avg_price_sqm?: number;
    avg_price_per_sqm?: number;
}

interface UiActionData {
    area?: UiActionArea;
    areas?: UiActionArea[];
    projections?: unknown[];
    data_points?: unknown[];
    summary?: {
        cash_final?: number;
    };
    final_values?: {
        cash_real_value?: number;
    };
    area_context?: {
        avg_price_sqm?: number;
    };
    avg_price_sqm?: number;
    [key: string]: unknown;
}

interface UiAction {
    type: string;
    data?: UiActionData;
    [key: string]: unknown;
}

interface AnalyticsContext {
    has_analytics?: boolean;
    avg_price_sqm?: number;
    growth_rate?: number;
    rental_yield?: number;
    [key: string]: unknown;
}

interface ChatHistoryMessagePayload {
    id?: number;
    role?: string;
    content?: string;
    properties?: Property[];
}

interface ChatResponsePayload {
    properties?: ChatPropertyPayload[];
    ui_actions?: UiAction[];
    suggestions?: string[];
    lead_score?: number;
    readiness_score?: number;
    detected_language?: string;
    showing_strategy?: string;
    analytics_context?: AnalyticsContext | null;
    response?: string;
    message?: string;
}

interface Artifacts {
    property?: Property;
    chart?: { type: string; data: unknown };
}

interface Message {
    id: number;
    role: 'user' | 'agent';
    content: string;
    artifacts?: Artifacts | null;
    uiActions?: UiAction[];
    analyticsContext?: AnalyticsContext | null;
    showingStrategy?: string;
    allProperties?: Property[];
    leadScore?: number;
    readinessScore?: number;
    suggestions?: string[];
    detectedLanguage?: string;
}

interface Suggestion {
    icon: React.ComponentType<{ className?: string }>;
    label: string;
    prompt: string;
}

interface SuggestionWithSnippet extends Suggestion {
    snippet: string;
    snippetAr: string;
    trend: 'up' | 'down' | 'neutral';
}

const SUGGESTIONS_AR: SuggestionWithSnippet[] = [
    { icon: BarChart2, label: "تحليل السوق", prompt: "حلل اتجاهات السوق الحالية في القاهرة الجديدة", snippet: "+2.4% avg EGP/m² this week", snippetAr: "+٢.٤٪ متوسط سعر المتر هذا الأسبوع", trend: 'up' },
    { icon: Search, label: "فرص استثمارية", prompt: "ابحث عن عقارات عائد مرتفع تحت 5 مليون جنيه", snippet: "12 new high-ROI listings", snippetAr: "١٢ وحدة عائد مرتفع جديدة", trend: 'up' },
    { icon: Shield, label: "تدقيق المطور", prompt: "دقق في سجل تسليمات بالم هيلز", snippet: "Palm Hills: 94% on-time", snippetAr: "بالم هيلز: ٩٤٪ تسليم في الموعد", trend: 'neutral' },
    { icon: TrendingUp, label: "مقارنة الأسعار", prompt: "قارن أسعار المتر في القاهرة الجديدة والشيخ زايد والساحل", snippet: "North Coast +5.1% this week", snippetAr: "الساحل +٥.١٪ هذا الأسبوع", trend: 'up' },
];

const SUGGESTIONS_EN: SuggestionWithSnippet[] = [
    { icon: BarChart2, label: "Market Intelligence", prompt: "Analyze current market trends in New Cairo", snippet: "+2.4% avg EGP/m² this week", snippetAr: "+٢.٤٪ متوسط سعر المتر", trend: 'up' },
    { icon: Search, label: "Find Opportunities", prompt: "Find high ROI properties under 5M EGP", snippet: "12 new high-ROI listings", snippetAr: "١٢ وحدة عائد عالي", trend: 'up' },
    { icon: Shield, label: "Developer Audit", prompt: "Audit the delivery history of Palm Hills", snippet: "Palm Hills: 94% on-time", snippetAr: "بالم هيلز: ٩٤٪ ملتزمين", trend: 'neutral' },
    { icon: TrendingUp, label: "Price Comparison", prompt: "Compare price per sqm across New Cairo, Sheikh Zayed, and North Coast", snippet: "North Coast +5.1% this week", snippetAr: "الساحل +٥.١٪ هذا الأسبوع", trend: 'up' },
];

/* Agent Avatar — Clean professional AI mark, no background, animated */
const AgentAvatar = ({ thinking = false }: { thinking?: boolean }) => (
    <div className="relative flex items-center justify-center w-8 h-8 flex-shrink-0 bg-transparent">
        {/* Glow effect when thinking */}
        {thinking && (
            <div className="absolute inset-0 bg-emerald-500/10 rounded-full blur-md animate-pulse" />
        )}
        <svg 
            className={`w-6 h-6 text-emerald-600 dark:text-emerald-500 ${thinking ? 'animate-[spin_3s_linear_infinite]' : ''}`} 
            viewBox="0 0 24 24" 
            fill="none" 
            xmlns="http://www.w3.org/2000/svg"
        >
            <path 
                d="M12 1.5C12 7.3 16.7 12 22.5 12C16.7 12 12 16.7 12 22.5C12 16.7 7.3 12 1.5 12C7.3 12 12 7.3 12 1.5Z" 
                fill="currentColor" 
            />
        </svg>
    </div>
);

/* RTL Detection */
const isArabic = (text: string): boolean => {
    if (!text) return false;
    const arabicChars = text.match(/[\u0600-\u06FF]/g);
    return !!arabicChars && arabicChars.length > text.length * 0.3;
};

/* Fix malformed markdown tables so remark-gfm can parse them */
function fixMarkdownTables(text: string): string {
    const lines = text.split('\n');
    const result: string[] = [];
    let i = 0;

    while (i < lines.length) {
        const line = lines[i];
        if (/^\s*\|/.test(line)) {
            const tableLines: string[] = [];
            while (i < lines.length && /^\s*\|/.test(lines[i])) {
                tableLines.push(lines[i]);
                i++;
            }

            if (tableLines.length >= 2) {
                const headerCols = (tableLines[0].match(/\|/g) || []).length - 1;
                const isSeparator = (l: string) => /^\s*\|[\s\-:|]+\|\s*$/.test(l);

                if (isSeparator(tableLines[1])) {
                    // Separator exists — rebuild it with correct column count
                    const sepCols = (tableLines[1].match(/\|/g) || []).length - 1;
                    if (sepCols !== headerCols) {
                        tableLines[1] = '| ' + Array(headerCols).fill('---').join(' | ') + ' |';
                    }
                } else if (headerCols >= 2) {
                    // No separator row — insert one after the header
                    tableLines.splice(1, 0, '| ' + Array(headerCols).fill('---').join(' | ') + ' |');
                }

                // Pad data rows that have fewer columns
                for (let r = 2; r < tableLines.length; r++) {
                    if (isSeparator(tableLines[r])) continue;
                    const rowCols = (tableLines[r].match(/\|/g) || []).length - 1;
                    if (rowCols < headerCols) {
                        tableLines[r] = tableLines[r].trimEnd().replace(/\|$/, '') + '| '.repeat(headerCols - rowCols) + '|';
                    }
                }

                result.push(...tableLines);
            } else {
                result.push(...tableLines);
            }
        } else {
            result.push(line);
            i++;
        }
    }
    return result.join('\n');
}

/* Markdown Renderer */
const MarkdownMessage = ({ content }: { content: string }) => {
    const msgIsArabic = isArabic(content);
    const normalized = fixMarkdownTables(
        content
            .replace(/\r\n/g, '\n')
            .replace(/\n{3,}/g, '\n\n')
            .replace(/(?<!\n)\n(?!\n)/gm, (match, offset, str) => {
                // Don't double-space lines inside markdown tables
                const before = str.lastIndexOf('\n', offset - 1);
                const after = str.indexOf('\n', offset + 1);
                const prevLine = str.slice(before + 1, offset);
                const nextLine = str.slice(offset + 1, after === -1 ? undefined : after);
                if (/^\s*\|/.test(prevLine) || /^\s*\|/.test(nextLine)) return match;
                return '\n\n';
            })
    );

    return (
        <div dir={msgIsArabic ? 'rtl' : 'ltr'} className={msgIsArabic ? 'text-right' : 'text-left'}>
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    p: ({ node, ...props }) => (
                        <p className={`mb-1.5 md:mb-3 last:mb-0 leading-[1.6] md:leading-relaxed ${msgIsArabic ? 'text-right' : 'text-left'}`} {...props} />
                    ),
                    ul: ({ node, ...props }) => (
                        <ul className={`list-disc mb-2 md:mb-3 space-y-0.5 md:space-y-1 ${msgIsArabic ? 'pr-5' : 'pl-5'}`} {...props} />
                    ),
                    ol: ({ node, ...props }) => (
                        <ol className={`list-decimal mb-2 md:mb-3 space-y-0.5 md:space-y-1 ${msgIsArabic ? 'pr-5' : 'pl-5'}`} {...props} />
                    ),
                    li: ({ node, ...props }) => <li className="mb-0.5 md:mb-1" {...props} />,
                    strong: ({ node, ...props }) => (
                        <strong className="font-semibold text-[var(--color-text-primary)]" {...props} />
                    ),
                    em: ({ node, ...props }) => (
                        <em className="italic text-[var(--color-text-secondary)]" {...props} />
                    ),
                    h1: ({ node, ...props }) => <h1 className="text-xl font-semibold mb-2 md:mb-3 mt-3 md:mt-4" {...props} />,
                    h2: ({ node, ...props }) => <h2 className="text-lg font-semibold mb-1.5 md:mb-2 mt-2 md:mt-3" {...props} />,
                    h3: ({ node, ...props }) => <h3 className="text-base font-medium mb-1.5 md:mb-2 mt-1.5 md:mt-2" {...props} />,
                    blockquote: ({ node, ...props }) => (
                        <blockquote
                            className={`${msgIsArabic ? 'border-r-2 pr-4' : 'border-l-2 pl-4'} border-emerald-500/40 py-1 my-2 text-[var(--color-text-secondary)]`}
                            {...props}
                        />
                    ),
                    a: ({ node, ...props }) => (
                        <a className="text-emerald-600 dark:text-emerald-400 hover:underline underline-offset-2" target="_blank" rel="noopener noreferrer" {...props} />
                    ),
                    code: ({ node, className, children, ...props }) => {
                        const isInline = !className;
                        return isInline ? (
                            <code className="bg-[var(--color-surface-elevated)] text-[var(--color-text-primary)] px-1.5 py-0.5 rounded text-[13px] font-mono" {...props}>{children}</code>
                        ) : (
                            <pre className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4 my-3 overflow-x-auto">
                                <code className="text-sm text-[var(--color-text-secondary)] font-mono" {...props}>{children}</code>
                            </pre>
                        );
                    },
                    hr: ({ node, ...props }) => <hr className="border-[var(--color-border)] my-4" {...props} />,
                    table: ({ node, ...props }) => (
                        <div className="overflow-x-auto my-3 rounded-lg border border-[var(--color-border)]">
                            <table className="w-full border-collapse text-sm" {...props} />
                        </div>
                    ),
                    th: ({ node, ...props }) => (
                        <th className="border-b border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-left text-[var(--color-text-primary)] font-medium text-xs uppercase tracking-wider" {...props} />
                    ),
                    td: ({ node, ...props }) => (
                        <td className="border-b border-[var(--color-border)] px-3 py-2.5 text-[var(--color-text-secondary)]" {...props} />
                    ),
                }}
            >
                {normalized}
            </ReactMarkdown>
        </div>
    );
};

/* ─── SessionStorage helpers ─── */
const STORAGE_KEYS = {
    MESSAGES: 'osool_chat_messages',
    SESSION_ID: 'osool_chat_session_id',
    SESSIONS_LIST: 'osool_chat_sessions',
} as const;

function loadFromStorage<T>(key: string, fallback: T): T {
    if (typeof window === 'undefined') return fallback;
    try {
        const raw = sessionStorage.getItem(key);
        return raw ? JSON.parse(raw) : fallback;
    } catch { return fallback; }
}

function saveToStorage(key: string, value: unknown) {
    if (typeof window === 'undefined') return;
    try { sessionStorage.setItem(key, JSON.stringify(value)); } catch {}
}

function getOrCreateSessionId(): string {
    if (typeof window === 'undefined') return `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    const existing = sessionStorage.getItem(STORAGE_KEYS.SESSION_ID);
    if (existing) return existing;
    const id = `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    sessionStorage.setItem(STORAGE_KEYS.SESSION_ID, id);
    return id;
}

function sanitizeAgentContent(text: string): string {
    if (!text) return text;
    return text
        .replace(/^\s*\[[^\n\]]+\]\s*$/gm, '')
        .replace(/\n{3,}/g, '\n\n')
        .trim();
}

/* ─── Typewriter hook ─── */
function useTypewriter(text: string, enabled: boolean, speed = 16) {
    const [displayed, setDisplayed] = useState(text);
    const [done, setDone] = useState(!enabled);
    const idx = useRef(0);

    useEffect(() => {
        let interval: ReturnType<typeof setInterval> | null = null;
        const timer = window.setTimeout(() => {
            if (!enabled) {
                setDisplayed(text);
                setDone(true);
                return;
            }

            idx.current = 0;
            setDisplayed('');
            setDone(false);
            const step = text.length > 800 ? 4 : text.length > 400 ? 3 : 2;
            interval = setInterval(() => {
                idx.current = Math.min(text.length, idx.current + step);
                if (idx.current >= text.length) {
                    setDisplayed(text);
                    setDone(true);
                    if (interval) clearInterval(interval);
                } else {
                    setDisplayed(text.slice(0, idx.current));
                }
            }, speed);
        }, 0);

        return () => {
            window.clearTimeout(timer);
            if (interval) clearInterval(interval);
        };
    }, [text, enabled, speed]);

    return { displayed, done };
}

/* ─── Typewriter wrapper for agent messages ─── */
const TypewriterMarkdown = ({ content, animate }: { content: string; animate: boolean }) => {
    const sanitized = sanitizeAgentContent(content);
    const { displayed, done } = useTypewriter(sanitized, animate, 16);
    const msgIsArabic = isArabic(displayed || sanitized);
    if (done) {
        return <MarkdownMessage content={sanitized} />;
    }
    return (
        <div dir={msgIsArabic ? 'rtl' : 'ltr'} className={msgIsArabic ? 'text-right' : 'text-left'}>
            <div className="whitespace-pre-wrap leading-relaxed text-[15px] text-[var(--color-text-secondary)]">
                {displayed}
            </div>
            <span className="inline-block w-[2px] h-[1.1em] bg-emerald-500 animate-pulse align-text-bottom ml-0.5" />
        </div>
    );
};

/* ─── Past-sessions sidebar item type ─── */
interface PastSession {
    session_id: string;
    preview: string | null;
    message_count: number;
    last_message_at: string | null;
}

interface ThinkingStep {
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    duration: number;
}

function getErrorMessage(error: unknown, fallback: string): string {
    if (error instanceof Error && error.message) {
        return error.message;
    }

    return fallback;
}

/** Relative time helper — avoids heavy date-fns dependency */
function getTimeAgo(dateStr: string, lang: string): string {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return lang === 'ar' ? 'الآن' : 'just now';
    if (mins < 60) return lang === 'ar' ? `منذ ${mins} د` : `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return lang === 'ar' ? `منذ ${hrs} س` : `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    if (days < 7) return lang === 'ar' ? `منذ ${days} ي` : `${days}d ago`;
    return lang === 'ar' ? `منذ ${Math.floor(days / 7)} أسبوع` : `${Math.floor(days / 7)}w ago`;
}

/** Guess a category tag from the conversation preview text */
function guessConversationTag(preview: string | null): { label: string; color: string } | null {
    if (!preview) return null;
    const lower = preview.toLowerCase();
    if (lower.includes('market') || lower.includes('trend') || lower.includes('سوق') || lower.includes('اتجاه'))
        return { label: 'Market', color: 'bg-blue-500/15 text-blue-400' };
    if (lower.includes('invest') || lower.includes('roi') || lower.includes('استثمار') || lower.includes('عائد'))
        return { label: 'Investment', color: 'bg-emerald-500/15 text-emerald-400' };
    if (lower.includes('developer') || lower.includes('delivery') || lower.includes('audit') || lower.includes('مطور') || lower.includes('تسليم'))
        return { label: 'Developer', color: 'bg-purple-500/15 text-purple-400' };
    if (lower.includes('compare') || lower.includes('price') || lower.includes('قارن') || lower.includes('سعر'))
        return { label: 'Pricing', color: 'bg-amber-500/15 text-amber-400' };
    return null;
}

function mapChatPropertyToProperty(prop: ChatPropertyPayload): Property {
    return {
        id: prop.id?.toString() || `prop_${Date.now()}_${Math.random()}`,
        title: prop.title || prop.name || 'Property',
        location: prop.location || prop.address || 'Location',
        price: prop.price || 0,
        currency: 'EGP',
        metrics: {
            size: prop.size_sqm || prop.size || 0,
            bedrooms: prop.bedrooms || 0,
            bathrooms: prop.bathrooms || 0,
            wolf_score: prop.wolf_score || 0,
            roi: prop.projected_roi || prop.roi || 0,
            price_per_sqm: prop.price_per_sqm || 0,
            liquidity_rating: prop.liquidity_rating || 'Medium',
        },
        image: prop.image_url || prop.image || 'https://images.unsplash.com/photo-1613977257363-707ba9348227?auto=format&fit=crop&q=80&w=800',
        developer: prop.developer || 'Developer',
        tags: Array.isArray(prop.tags) ? prop.tags.filter((tag): tag is string => typeof tag === 'string') : [],
        status: prop.status || 'Available',
    };
}

function shouldRenderUiAction(action: UiAction): boolean {
    if (action.type === 'property_cards') return false;
    if (!action.data) return false;

    const data = action.data;
    if (action.type === 'area_analysis') {
        const area = data.area || data.areas?.[0];
        if (!area?.name || (area.avg_price_sqm || area.avg_price_per_sqm || 0) === 0) return false;
    }

    if (action.type === 'inflation_killer') {
        const hasProjections = (data.projections?.length || 0) > 0 || (data.data_points?.length || 0) > 0;
        const hasSummary = (data.summary?.cash_final || 0) > 0 || (data.final_values?.cash_real_value || 0) > 0;
        if (!hasProjections && !hasSummary) return false;
    }

    if (action.type === 'market_benchmark' && !data.avg_price_sqm && !data.area_context?.avg_price_sqm) {
        return false;
    }

    if (action.type === 'price_growth_chart' && (!data.data_points?.length || data.data_points.length < 2)) {
        return false;
    }

    return true;
}

/* ─── Thinking Steps — shows AI processing stages while waiting ─── */
const ThinkingSteps = ({ lastUserMessage }: { lastUserMessage: string }) => {
    const [visibleSteps, setVisibleSteps] = useState(0);
    const msgIsArabic = isArabic(lastUserMessage);
    
    // Generate dynamic steps based on the user's message
    const steps = React.useMemo(() => {
        const content = (lastUserMessage || '').toLowerCase();
        const baseSteps: ThinkingStep[] = [];
        
        if (msgIsArabic) {
            baseSteps.push({ label: 'تحليل الطلب...', icon: Search, duration: 1200 });
            if (content.includes('عقار') || content.includes('شقة') || content.includes('فيلا') || content.includes('سعر')) {
                 baseSteps.push({ label: 'البحث في قاعدة العقارات...', icon: MapPin, duration: 3000 });
                 baseSteps.push({ label: 'تصفية أفضل الخيارات...', icon: Sparkles, duration: 5000 });
            } else if (content.includes('استثمار') || content.includes('عائد') || content.includes('roi') || content.includes('تضخم') || content.includes('فلوس')) {
                 baseSteps.push({ label: 'تحليل بيانات الاستثمار...', icon: BarChart2, duration: 3000 });
                 baseSteps.push({ label: 'حساب العوائد المتوقعة...', icon: BarChart2, duration: 5000 });
            } else if (content.includes('مطور') || content.includes('شركة') || content.includes('تسليم')) {
                 baseSteps.push({ label: 'فحص سجل المطورين...', icon: Shield, duration: 3000 });
                 baseSteps.push({ label: 'تقييم المخاطر...', icon: BarChart2, duration: 5000 });
            } else {
                 baseSteps.push({ label: 'فحص بيانات السوق...', icon: BarChart2, duration: 3000 });
                 baseSteps.push({ label: 'استخراج الأفكار والتوصيات...', icon: Sparkles, duration: 5000 });
            }
            baseSteps.push({ label: 'صياغة الرد...', icon: MessageSquare, duration: 7500 });
        } else {
            baseSteps.push({ label: 'Understanding request...', icon: Search, duration: 1200 });
            if (content.includes('property') || content.includes('apartment') || content.includes('villa') || content.includes('price')) {
                 baseSteps.push({ label: 'Scanning properties inventory...', icon: MapPin, duration: 3000 });
                 baseSteps.push({ label: 'Filtering best matches...', icon: Sparkles, duration: 5000 });
            } else if (content.includes('invest') || content.includes('roi') || content.includes('yield') || content.includes('inflation') || content.includes('money')) {
                 baseSteps.push({ label: 'Analyzing investment data...', icon: BarChart2, duration: 3000 });
                 baseSteps.push({ label: 'Calculating projected returns...', icon: BarChart2, duration: 5000 });
            } else if (content.includes('developer') || content.includes('company') || content.includes('delivery')) {
                 baseSteps.push({ label: 'Auditing developer record...', icon: Shield, duration: 3000 });
                 baseSteps.push({ label: 'Evaluating risk factors...', icon: BarChart2, duration: 5000 });
            } else {
                 baseSteps.push({ label: 'Scanning market trends...', icon: BarChart2, duration: 3000 });
                 baseSteps.push({ label: 'Extracting insights...', icon: Sparkles, duration: 5000 });
            }
            baseSteps.push({ label: 'Drafting response...', icon: MessageSquare, duration: 7500 });
        }
        return baseSteps;
    }, [lastUserMessage, msgIsArabic]);

    useEffect(() => {
        const resetTimer = window.setTimeout(() => setVisibleSteps(0), 0);
        const timers = steps.map((step, i) =>
            window.setTimeout(() => setVisibleSteps(i + 1), step.duration)
        );
        return () => {
            window.clearTimeout(resetTimer);
            timers.forEach(window.clearTimeout);
        };
    }, [steps]);

    return (
        <div className="flex gap-4 mb-6 animate-fade-in" dir={msgIsArabic ? 'rtl' : 'ltr'}>
            <AgentAvatar thinking={true} />
            <div className="flex-1 flex flex-col gap-2 pt-1">
                {steps.map((step, i) => {
                    const Icon = step.icon;
                    const isVisible = i < visibleSteps;
                    const isCurrent = i === visibleSteps - 1;
                    const isPending = i >= visibleSteps;

                    if (isPending && i > visibleSteps) return null; // only show next pending

                    return (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 8 }}
                            animate={{ opacity: isVisible ? 1 : 0.4, y: 0 }}
                            transition={{ duration: 0.3 }}
                            className={`flex items-center gap-2.5 text-[13px] ${
                                isCurrent
                                    ? 'text-emerald-600 dark:text-emerald-400 font-medium'
                                    : isVisible
                                        ? 'text-[var(--color-text-muted)]'
                                        : 'text-[var(--color-text-muted)]/40'
                            }`}
                        >
                            {isCurrent ? (
                                <div className="w-4 h-4 rounded-full border-2 border-emerald-500/30 border-t-emerald-500 animate-spin flex-shrink-0" />
                            ) : isVisible ? (
                                <Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                            ) : (
                                <Icon className="w-4 h-4 flex-shrink-0 opacity-40" />
                            )}
                            <span>{step.label}</span>
                        </motion.div>
                    );
                })}

                {/* Show pending dot when no steps revealed yet */}
                {visibleSteps === 0 && (
                    <div className="flex items-center gap-1.5 pt-1">
                        <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-text-muted)] animate-pulse" style={{ animationDelay: '0ms' }} />
                        <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-text-muted)] animate-pulse" style={{ animationDelay: '150ms' }} />
                        <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-text-muted)] animate-pulse" style={{ animationDelay: '300ms' }} />
                    </div>
                )}
            </div>
        </div>
    );
};

const FREE_MESSAGE_LIMIT = 3;

/* Anonymous Gate — shown after free messages are used up */
const AnonymousChatGate = ({ language }: { language: string }) => {
    const isAr = language === 'ar';
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mx-auto max-w-lg text-center py-10 px-6"
            dir={isAr ? 'rtl' : 'ltr'}
        >
            <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10 border border-emerald-500/20">
                <Lock className="h-6 w-6 text-emerald-500" />
            </div>
            <h3 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
                {isAr ? 'عجبك اللي شوفته؟' : "Liked what you've seen?"}
            </h3>
            <p className="text-sm text-[var(--color-text-secondary)] mb-6 leading-relaxed">
                {isAr
                    ? 'سجّل دلوقتي عشان تكمّل المحادثة وتحفظ تحليلاتك — وده مجاني تماماً.'
                    : 'Sign up to continue the conversation, save your analyses, and unlock full access — completely free.'}
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
                <Link
                    href="/signup"
                    className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-full text-sm font-semibold transition-colors shadow-lg shadow-emerald-500/20"
                >
                    {isAr ? 'إنشاء حساب' : 'Create Account'}
                </Link>
                <Link
                    href="/login"
                    className="px-6 py-3 border border-[var(--color-border)] hover:border-emerald-500/40 rounded-full text-sm font-medium text-[var(--color-text-primary)] transition-colors"
                >
                    {isAr ? 'تسجيل الدخول' : 'Sign In'}
                </Link>
            </div>
        </motion.div>
    );
};

/* Main Component */
export default function AgentInterface() {
    const { user } = useAuth();
    const { profile, triggerXP } = useGamification();
    const searchParams = useSearchParams();
    const nextRouter = useNextRouter();
    const [messages, setMessages] = useState<Message[]>(() => loadFromStorage(STORAGE_KEYS.MESSAGES, []));
    const [inputValue, setInputValue] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [contextPaneOpen, setContextPaneOpen] = useState(false);
    const [activeContext, setActiveContext] = useState<Artifacts | null>(null);
    const [recentQueries, setRecentQueries] = useState<string[]>([]);
    const [conversationLeadScore, setConversationLeadScore] = useState(0);
    const [conversationReadiness, setConversationReadiness] = useState(0);
    const [conversationLanguage, setConversationLanguage] = useState('ar');
    const [lastAiMsgId, setLastAiMsgId] = useState<number | null>(null);
    const [pastSessions, setPastSessions] = useState<PastSession[]>([]);
    const [historyOpen, setHistoryOpen] = useState(false);
    const [anonGateShown, setAnonGateShown] = useState(false);
    const [savedPropertyIds, setSavedPropertyIds] = useState<Set<string>>(new Set());

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);
    const sessionIdRef = useRef<string>(getOrCreateSessionId());
    const hasFetchedHistory = useRef(false);
    const seededPromptRef = useRef<string | null>(null);

    const userName = user?.full_name || user?.email?.split('@')[0] || (conversationLanguage === 'ar' ? 'مستثمر' : 'there');

    /* Persist messages to sessionStorage whenever they change */
    useEffect(() => {
        if (messages.length > 0) saveToStorage(STORAGE_KEYS.MESSAGES, messages);
    }, [messages]);

    /* Fetch past sessions from backend on first mount */
    useEffect(() => {
        if (hasFetchedHistory.current) return;
        hasFetchedHistory.current = true;
        api.get('/api/chat/history').then(res => {
            const sessions: PastSession[] = (res.data?.sessions || []).filter(
                (s: PastSession) => s.session_id !== sessionIdRef.current
            );
            setPastSessions(sessions);
        }).catch(() => {});
    }, []);

    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.style.height = 'auto';
            inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 150)}px`;
        }
    }, [inputValue]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isTyping]);

    const hasStarted = messages.length > 0;

    /* Re-focus input after layout transition */
    useEffect(() => {
        const timer = setTimeout(() => {
            if (inputRef.current) inputRef.current.focus();
        }, 500);
        return () => clearTimeout(timer);
    }, [hasStarted]);

    // Count user messages for anonymous gate
    const userMessageCount = messages.filter(m => m.role === 'user').length;
    const isAnonymous = !user;
    const isGated = isAnonymous && userMessageCount >= FREE_MESSAGE_LIMIT;

    const handleSendMessage = useCallback(async (text?: string) => {
        const content = text || inputValue;
        if (!content.trim() || isTyping) return;

        // Anonymous gate: block after FREE_MESSAGE_LIMIT messages
        if (!user) {
            const currentUserMsgCount = messages.filter(m => m.role === 'user').length;
            if (currentUserMsgCount >= FREE_MESSAGE_LIMIT) {
                setAnonGateShown(true);
                return;
            }
        }

        setRecentQueries(prev => {
            const updated = [content.slice(0, 40), ...prev.filter(q => q !== content.slice(0, 40))];
            return updated.slice(0, 5);
        });

        const userMsg: Message = { id: Date.now(), role: 'user', content };
        setMessages(prev => [...prev, userMsg]);
        setInputValue('');
        setIsTyping(true);

        // ── SSE STREAMING MODE ──
        // Uses Server-Sent Events to keep connection alive during long Wolf Brain processing.
        // Prevents mobile carrier NAT from dropping idle TCP connections.
        const aiMsgId = Date.now() + 1;
        let accumulatedText = '';
        let streamingStarted = false;

        try {
            await streamChat(
                content,
                sessionIdRef.current,
                {
                    onToken: (token) => {
                        accumulatedText += (typeof token === 'string' ? token : '');
                        if (!streamingStarted) {
                            streamingStarted = true;
                            setIsTyping(false); // Hide ThinkingSteps, start showing text
                            setMessages(prev => [...prev, {
                                id: aiMsgId,
                                role: 'agent',
                                content: accumulatedText,
                            }]);
                        } else {
                            const currentText = accumulatedText;
                            setMessages(prev => prev.map(m =>
                                m.id === aiMsgId ? { ...m, content: currentText } : m
                            ));
                        }
                    },
                    onToolStart: (tool) => {
                        console.log('[CoInvestor] Stream tool start:', tool);
                    },
                    onToolEnd: (tool) => {
                        console.log('[CoInvestor] Stream tool end:', tool);
                    },
                    onComplete: (data) => {
                        const allProps = Array.isArray(data.properties) ? data.properties.map(mapChatPropertyToProperty) : [];
                        const uiActions = Array.isArray(data.ui_actions) ? (data.ui_actions as UiAction[]) : [];
                        const artifacts: Artifacts | null = allProps.length > 0 ? { property: allProps[0] } : null;

                        const finalContent = accumulatedText || (conversationLanguage === 'ar'
                            ? 'أنا CoInvestor، وكيل الذكاء العقاري الخاص بك. كيف أقدر أساعدك النهارده؟'
                            : "I'm CoInvestor, your real estate intelligence agent. How can I assist you today?");

                        // Finalize the streaming message with all metadata
                        setMessages(prev => {
                            // If streaming never started (no tokens received), add the AI message now
                            const hasMsg = prev.some(m => m.id === aiMsgId);
                            if (!hasMsg) {
                                return [...prev, {
                                    id: aiMsgId,
                                    role: 'agent' as const,
                                    content: finalContent,
                                    artifacts,
                                    uiActions,
                                    allProperties: allProps,
                                    suggestions: data.suggestions || [],
                                    leadScore: data.lead_score || 0,
                                    readinessScore: data.readiness_score || 0,
                                    detectedLanguage: data.detected_language || 'ar',
                                    showingStrategy: data.showing_strategy || 'NONE',
                                }];
                            }
                            return prev.map(m =>
                                m.id === aiMsgId ? {
                                    ...m,
                                    content: finalContent,
                                    artifacts,
                                    uiActions,
                                    allProperties: allProps,
                                    suggestions: data.suggestions || [],
                                    leadScore: data.lead_score || 0,
                                    readinessScore: data.readiness_score || 0,
                                    detectedLanguage: data.detected_language || 'ar',
                                    showingStrategy: data.showing_strategy || 'NONE',
                                } : m
                            );
                        });

                        // Update conversation-level tracking
                        setConversationLeadScore(data.lead_score || 0);
                        setConversationReadiness(data.readiness_score || 0);
                        if (data.detected_language) setConversationLanguage(data.detected_language);

                        // Don't set lastAiMsgId — streaming already provided incremental display.
                        // Setting it would re-trigger the typewriter on already-displayed text.
                        setIsTyping(false);
                        triggerXP(5, 'Asked a question');

                        if (data.ui_actions && data.ui_actions.length > 0) {
                            triggerXP(15, 'Used analysis tool');
                        }
                        if (artifacts) {
                            setActiveContext(artifacts);
                        }
                    },
                    onError: (error) => {
                        console.error('[CoInvestor] Stream Error:', error);
                        const isArabic = conversationLanguage === 'ar';
                        const errorContent = isArabic
                            ? 'حصل مشكلة بسيطة في التحليل. ممكن تعيد السؤال تاني؟ أنا CoInvestor وجاهز أساعدك في أي استفسار عقاري.'
                            : "A brief analysis issue occurred. Could you try again? I'm CoInvestor, ready to help with any real estate question.";

                        setMessages(prev => {
                            const hasMsg = prev.some(m => m.id === aiMsgId);
                            if (!hasMsg) {
                                return [...prev, { id: aiMsgId, role: 'agent' as const, content: errorContent, artifacts: null }];
                            }
                            return prev.map(m =>
                                m.id === aiMsgId ? { ...m, content: errorContent } : m
                            );
                        });
                        setIsTyping(false);
                    },
                },
                'auto'
            );
        } catch (error: unknown) {
            // Streaming setup failed entirely — fallback to non-streaming
            console.warn('[CoInvestor] SSE streaming failed, falling back to POST:', getErrorMessage(error, 'Unknown streaming error'));
            try {
                const response = await api.post('/api/chat', {
                    message: content,
                    session_id: sessionIdRef.current,
                    language: 'auto'
                }, { timeout: 120000 });
                const data = response.data as ChatResponsePayload;

                const allProps = Array.isArray(data.properties) ? data.properties.map(mapChatPropertyToProperty) : [];
                const uiActions = Array.isArray(data.ui_actions) ? data.ui_actions : [];

                const aiMsg: Message = {
                    id: aiMsgId,
                    role: 'agent',
                    content: data.response || data.message || (conversationLanguage === 'ar' ? 'أنا CoInvestor، وكيل الذكاء العقاري الخاص بك.' : "I'm CoInvestor, your real estate intelligence agent."),
                    artifacts: allProps.length > 0 ? { property: allProps[0] } : null,
                    uiActions,
                    allProperties: allProps,
                    suggestions: data.suggestions || [],
                    leadScore: data.lead_score || 0,
                    readinessScore: data.readiness_score || 0,
                    detectedLanguage: data.detected_language || 'ar',
                    showingStrategy: data.showing_strategy || 'NONE',
                    analyticsContext: data.analytics_context || null,
                };
                setMessages(prev => [...prev, aiMsg]);
                setLastAiMsgId(aiMsgId);
                setConversationLeadScore(data.lead_score || 0);
                setConversationReadiness(data.readiness_score || 0);
                if (data.detected_language) setConversationLanguage(data.detected_language);
                triggerXP(5, 'Asked a question');
                if (aiMsg.uiActions && aiMsg.uiActions.length > 0) triggerXP(15, 'Used analysis tool');
                if (allProps.length > 0) setActiveContext({ property: allProps[0] });
            } catch (fallbackErr: unknown) {
                console.error('[CoInvestor] Fallback POST also failed:', fallbackErr);
                const isArabic = conversationLanguage === 'ar';
                const errorMsg = isArabic
                    ? 'حصل مشكلة بسيطة في التحليل. ممكن تعيد السؤال تاني؟ أنا CoInvestor وجاهز أساعدك في أي استفسار عقاري.'
                    : "A brief analysis issue occurred. Could you try again? I'm CoInvestor, ready to help with any real estate question.";
                setMessages(prev => [...prev, { id: aiMsgId, role: 'agent' as const, content: errorMsg, artifacts: null }]);
            }
        } finally {
            setIsTyping(false);
        }
    }, [inputValue, isTyping, user, messages]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const handleNewChat = useCallback(() => {
        setMessages([]);
        setContextPaneOpen(false);
        setActiveContext(null);
        setInputValue('');
        setConversationLeadScore(0);
        setConversationReadiness(0);
        setConversationLanguage('ar');
        setLastAiMsgId(null);
        seededPromptRef.current = null; // reset so same chip can fire again
        const newId = `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
        sessionIdRef.current = newId;
        sessionStorage.setItem(STORAGE_KEYS.SESSION_ID, newId);
        sessionStorage.removeItem(STORAGE_KEYS.MESSAGES);
    }, []);

    useEffect(() => {
        const prompt = searchParams.get('prompt');
        if (!prompt || isTyping || seededPromptRef.current === prompt) {
            return;
        }

        const autostart = searchParams.get('autostart') === '1';
        seededPromptRef.current = prompt;

        // Clear the URL params so re-clicking the same chip always works
        nextRouter.replace('/chat', { scroll: false });

        if (messages.length > 0) {
            handleNewChat();
        }

        if (autostart) {
            const timer = window.setTimeout(() => {
                void handleSendMessage(prompt);
            }, 80);

            return () => window.clearTimeout(timer);
        }

        setInputValue(prompt);
        const focusTimer = window.setTimeout(() => {
            inputRef.current?.focus();
        }, 60);

        return () => window.clearTimeout(focusTimer);
    }, [searchParams, messages.length, isTyping, handleNewChat, handleSendMessage]);

    /* Load a past session's messages from the backend */
    const loadSession = useCallback(async (sessionId: string) => {
        try {
            const res = await api.get(`/api/chat/history/${sessionId}`);
            const msgs: Message[] = ((res.data?.messages || []) as ChatHistoryMessagePayload[]).map((m, i: number) => ({
                id: m.id || Date.now() + i,
                role: m.role === 'user' ? 'user' : 'agent',
                content: m.content || '',
                artifacts: null,
                allProperties: m.properties || [],
            }));
            setMessages(msgs);
            sessionIdRef.current = sessionId;
            sessionStorage.setItem(STORAGE_KEYS.SESSION_ID, sessionId);
            saveToStorage(STORAGE_KEYS.MESSAGES, msgs);
            setLastAiMsgId(null); // don't animate old messages
            setHistoryOpen(false);
        } catch (err) {
            console.error('[History] Failed to load session', err);
        }
    }, []);

    const [copiedMsgId, setCopiedMsgId] = useState<number | null>(null);

    const copyToClipboard = (text: string, msgId: number) => {
        navigator.clipboard.writeText(text).then(() => {
            setCopiedMsgId(msgId);
            setTimeout(() => setCopiedMsgId(null), 2000);
        });
    };

    const handleRetry = useCallback(async (msgIndex: number) => {
        // Find the last user message before this AI message
        const prevUserMsg = messages.slice(0, msgIndex).reverse().find(m => m.role === 'user');
        if (!prevUserMsg) return;
        // Remove the AI message being retried
        setMessages(prev => prev.filter((_, i) => i !== msgIndex));
        // Re-send the user message
        await handleSendMessage(prevUserMsg.content);
    }, [messages, handleSendMessage]);

    /* ─── Chat-native property actions ─── */
    const handleSaveProperty = useCallback(async (prop: Property, e: React.MouseEvent) => {
        e.stopPropagation();
        if (!user) return;
        const propId = parseInt(String(prop.id), 10);
        if (isNaN(propId)) return;
        try {
            await toggleFavorite(propId);
            setSavedPropertyIds(prev => {
                const next = new Set(prev);
                if (next.has(String(prop.id))) {
                    next.delete(String(prop.id));
                } else {
                    next.add(String(prop.id));
                    triggerXP(10, 'Saved a property');
                }
                return next;
            });
        } catch (err) {
            console.warn('[Chat] Failed to toggle favorite:', err);
        }
    }, [user, triggerXP]);

    const handleInlineValuation = useCallback((prop: Property, e: React.MouseEvent) => {
        e.stopPropagation();
        const prompt = conversationLanguage === 'ar'
            ? `شغّل تقييم AI على "${prop.title}" في ${prop.location} - سعره ${(prop.price / 1000000).toFixed(1)} مليون جنيه`
            : `Run AI valuation on "${prop.title}" in ${prop.location} - listed at ${(prop.price / 1000000).toFixed(1)}M EGP`;
        void handleSendMessage(prompt);
    }, [conversationLanguage, handleSendMessage]);

    const handleInlineCompare = useCallback((prop: Property, e: React.MouseEvent) => {
        e.stopPropagation();
        const prompt = conversationLanguage === 'ar'
            ? `قارن "${prop.title}" مع وحدات مشابهة في ${prop.location} في نفس النطاق السعري`
            : `Compare "${prop.title}" with similar units in ${prop.location} in the same price range`;
        void handleSendMessage(prompt);
    }, [conversationLanguage, handleSendMessage]);

    /* ─── Shared Input Bar ─── */
    const inputBar = (
        <motion.div layoutId="input-bar" className="w-full" transition={{ type: 'spring', damping: 30, stiffness: 300 }}>
            <div className={`bg-[var(--color-surface)]/95 backdrop-blur-2xl rounded-[24px] flex flex-col transition-all duration-300 ${isTyping ? 'opacity-70 scale-[0.99]' : ''} shadow-[0_8px_30px_rgba(0,0,0,0.04)] border border-[var(--color-border)]/40`}>

                <div className="flex items-end gap-2">
                    <textarea
                        dir="auto"
                        ref={inputRef}
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={conversationLanguage === 'ar' ? 'اسأل عن العقارات، بيانات السوق، أو الاستثمار...' : 'Ask about properties, market data, or investments...'}
                        className="flex-1 bg-transparent border-none text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:ring-0 resize-none py-2.5 md:py-4 px-4 md:px-6 text-[14px] md:text-[15px] max-h-[120px] md:max-h-[180px] outline-none ring-0 leading-normal font-medium"
                        rows={1}
                        disabled={isTyping}
                    />

                    <div className="flex-shrink-0 pb-2 md:pb-3 pr-2 md:pr-3">
                        <button
                            onClick={() => handleSendMessage()}
                            disabled={isTyping || !inputValue.trim()}
                            aria-label={conversationLanguage === 'ar' ? 'إرسال الرسالة' : 'Send message'}
                            title="Send message"
                            className="p-2 md:p-2.5 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-xl hover:scale-105 active:scale-95 shadow-sm transition-all duration-200 disabled:opacity-20 disabled:pointer-events-none"
                        >
                            <ArrowUp className="w-4 h-4" strokeWidth={2.5} />
                        </button>
                    </div>
                </div>
            </div>
        </motion.div>
    );

    const generateSuggestions = (msg: Message): string[] => {
        const content = msg.content.toLowerCase();
        const hasProperties = msg.allProperties && msg.allProperties.length > 0;
        const hasAnalytics = msg.analyticsContext?.has_analytics;
        const lang = msg.detectedLanguage || conversationLanguage || 'ar';
        const isAr = lang === 'ar';

        // Use a simple hash of content to rotate through options deterministically
        const hash = content.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);

        // Content-based triggers for variety
        if (content.includes('تضخم') || content.includes('inflation') || content.includes('فلوس')) {
            return isAr
                ? ['إزاي أحمي فلوسي؟', 'عقار ولا شهادات بنك؟', 'حلل العائد بعد التضخم']
                : ['How to protect my money?', 'Property vs bank CDs?', 'Real return after inflation'];
        }
        if (content.includes('مطور') || content.includes('developer') || content.includes('تسليم') || content.includes('delivery')) {
            const opts = isAr
                ? ['سجل التسليم بتاعهم', 'هل فيه مطور أضمن؟', 'ورّيني التقييمات', 'مواعيد التسليم', 'المشاريع المتأخرة']
                : ['Their delivery track record', 'More reliable developer?', 'Show me ratings', 'Delivery timeline', 'Delayed projects'];
            return [opts[hash % opts.length], opts[(hash + 2) % opts.length], opts[(hash + 4) % opts.length]];
        }
        if (content.includes('ساحل') || content.includes('coast') || content.includes('سوخنة') || content.includes('sokhna')) {
            return isAr
                ? ['ساحل ولا سوخنة أحسن؟', 'العائد الإيجاري كام؟', 'أحسن كمبوند هناك؟']
                : ['Coast vs Sokhna?', 'Rental yield there?', 'Best compound there?'];
        }
        if (content.includes('أقساط') || content.includes('سداد') || content.includes('installment') || content.includes('payment')) {
            return isAr
                ? ['أطول خطة سداد؟', 'سداد بدون فوايد؟', 'قارن خطط السداد']
                : ['Longest payment plan?', 'Interest-free options?', 'Compare payment plans'];
        }

        if (hasProperties) {
            const opts = isAr
                ? ['قارن العقارات دي', 'تحليل العائد', 'خطة السداد؟', 'تفاصيل أكتر عن الوحدة', 'وحدات مشابهة أرخص', 'مخاطر القرار']
                : ['Compare these properties', 'Show ROI analysis', 'Payment plan options?', 'More details on this unit', 'Similar but cheaper?', 'Decision risks'];
            return [opts[hash % opts.length], opts[(hash + 2) % opts.length], opts[(hash + 4) % opts.length]];
        } else if (hasAnalytics) {
            const opts = isAr
                ? ['اتجاهات الأسعار', 'أفضل مناطق النمو', 'قارن البدائل', 'تحليل ضد التضخم', 'هل ده وقت مناسب؟']
                : ['Show price trends', 'Best growth areas?', 'Compare alternatives', 'Inflation analysis', 'Is this a good time?'];
            return [opts[hash % opts.length], opts[(hash + 2) % opts.length], opts[(hash + 4) % opts.length]];
        } else {
            // General pool — rotate based on content hash for variety
            const opts = isAr
                ? ['أفضل العقارات', 'نظرة على السوق', 'حدد ميزانيتي', 'أفضل منطقة للاستثمار', 'إيه المطورين الموثوقين؟', 'فيه عروض حالياً؟', 'عايز أفهم العائد']
                : ['Top properties', 'Market overview', 'Set my budget', 'Best area for investment', 'Reliable developers?', 'Any current deals?', 'Explain ROI to me'];
            return [opts[hash % opts.length], opts[(hash + 2) % opts.length], opts[(hash + 4) % opts.length]];
        }
    };

    return (
        <LayoutGroup>
        <div className="flex h-full min-h-0 w-full bg-[var(--color-background)] text-[var(--color-text-primary)] overflow-hidden selection:bg-emerald-500/15 relative">

            {/* Main Chat */}
            <main className="flex-1 flex flex-col relative min-w-0 h-full w-full min-h-0 z-0">

                {/* Top bar — sticky header with session controls + funnel */}
                {hasStarted && (
                    <div className="sticky top-0 left-0 right-0 z-30 bg-[var(--color-background)]/80 backdrop-blur-xl border-b border-[var(--color-border)]/30">
                        <div className="max-w-[980px] mx-auto px-4 md:px-6">
                            <div className="flex items-center justify-between py-1.5 md:py-2.5">
                                <span className="text-[12px] md:text-[13px] font-semibold text-[var(--color-text-primary)] tracking-tight">
                                    Osool AI <span className="text-[var(--color-text-muted)] font-medium mx-1.5">/</span> <span className="text-[var(--color-text-secondary)] font-medium">{conversationLanguage === 'ar' ? 'جلسة' : 'Session'}</span>
                                </span>
                                <div className="flex items-center gap-1 md:gap-2">
                                    <button
                                        onClick={() => setHistoryOpen(true)}
                                        aria-label={conversationLanguage === 'ar' ? 'المحادثات السابقة' : 'Past conversations'}
                                        className="p-1.5 md:p-2 hover:bg-[var(--color-surface)] rounded-full text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-all hover:scale-105 active:scale-95"
                                        title={conversationLanguage === 'ar' ? 'المحادثات السابقة' : 'Past Conversations'}
                                    >
                                        <History className="w-4 h-4 md:w-4 md:h-4" strokeWidth={2} />
                                    </button>
                                    <button
                                        onClick={handleNewChat}
                                        aria-label={conversationLanguage === 'ar' ? 'محادثة جديدة' : 'New chat'}
                                        className="p-1.5 md:p-2 hover:bg-[var(--color-surface)] rounded-full text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-all hover:scale-105 active:scale-95"
                                        title={conversationLanguage === 'ar' ? 'محادثة جديدة' : 'New Chat'}
                                    >
                                        <Plus className="w-4 h-4 md:w-4 md:h-4" strokeWidth={2} />
                                    </button>
                                </div>
                            </div>
                            <div className="max-w-[800px] mx-auto -mt-1 pb-1 md:pb-2">
                                <FunnelIndicator
                                    leadScore={conversationLeadScore}
                                    readinessScore={conversationReadiness}
                                    language={conversationLanguage}
                                />
                            </div>
                        </div>
                    </div>
                )}

                {/* Scrollable Content */}
                <div className="flex-1 overflow-y-auto scroll-smooth">
                    <div className="max-w-[980px] mx-auto h-full w-full">

                        {/* Greeting */}
                        {!hasStarted && (
                            <div className="flex flex-col min-h-[calc(100vh-8rem)] justify-center px-4 py-6 relative">
                                {/* Decorative background elements */}
                                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-emerald-500/5 dark:bg-emerald-500/10 blur-[100px] rounded-full pointer-events-none -z-10" />

                                <div className="text-center w-full max-w-3xl mx-auto">
                                    <div className="flex items-center justify-center gap-3 mb-4">
                                        <AgentAvatar />
                                        <span className="text-[13px] font-semibold text-[var(--color-text-muted)] uppercase tracking-widest">Osool AI</span>
                                    </div>
                                    <h1 className="text-[2rem] md:text-[3rem] font-semibold tracking-tight leading-[1.15] mb-3 md:mb-4 text-[var(--color-text-primary)]" dir="auto">
                                        {conversationLanguage === 'ar' ? `أهلاً، ${userName}` : `Hello, ${userName}`}
                                    </h1>
                                    <p className="text-[1rem] md:text-[1.15rem] text-[var(--color-text-secondary)] font-normal max-w-xl mx-auto leading-relaxed px-4 md:px-0" dir="auto">
                                        {conversationLanguage === 'ar' ? 'وكيلك الذكي للعقارات — تحليل السوق، فرص الاستثمار، وتدقيق المطورين' : 'Your AI real estate agent — market analysis, investment opportunities, and developer audits'}<span className="text-emerald-500 font-bold ml-0.5">.</span>
                                    </p>
                                </div>

                                    {/* Centered Input Bar */}
                                    <div className="w-full max-w-[800px] mx-auto mt-6 px-4">
                                        {inputBar}
                                    </div>

                                    {/* Quick Action Cards — enhanced with data snippets  */}
                                    <div className="w-full max-w-3xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-3 mt-5 md:mt-6 px-4">
                                        {(conversationLanguage === 'ar' ? SUGGESTIONS_AR : SUGGESTIONS_EN).map((s, i) => (
                                            <button
                                                key={i}
                                                onMouseDown={(e) => e.preventDefault()}
                                                onClick={() => { handleSendMessage(s.prompt); setTimeout(() => inputRef.current?.focus(), 100); }}
                                                className="p-4 md:p-5 bg-[var(--color-surface)]/60 hover:bg-[var(--color-surface)] backdrop-blur-md rounded-2xl text-left transition-all duration-300 flex flex-col justify-between group border border-[var(--color-border)]/40 hover:border-emerald-500/30 hover:shadow-[0_8px_30px_rgba(16,185,129,0.06)] hover:-translate-y-1"
                                            >
                                                <div className="p-2.5 bg-emerald-500/10 rounded-xl text-emerald-600 dark:text-emerald-400 group-hover:bg-emerald-500/20 transition-colors w-fit mb-3">
                                                    <s.icon className="w-4 h-4" />
                                                </div>
                                                <span className="text-[13px] font-semibold text-[var(--color-text-primary)] leading-snug group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors" dir="auto">{s.label}</span>
                                                {/* Dynamic data snippet */}
                                                <span className={`mt-1.5 text-[10px] font-medium flex items-center gap-1 ${
                                                    s.trend === 'up' ? 'text-emerald-500' : s.trend === 'down' ? 'text-red-400' : 'text-[var(--color-text-muted)]'
                                                }`}>
                                                    {s.trend === 'up' && <TrendingUp className="w-3 h-3" />}
                                                    {conversationLanguage === 'ar' ? s.snippetAr : s.snippet}
                                                </span>
                                            </button>
                                        ))}
                                    </div>

                                    {/* Recent conversations — enhanced with timestamps & category tags */}
                                    {pastSessions.length > 0 && (
                                        <div className="w-full max-w-2xl mx-auto mt-8 px-4">
                                            <button
                                                onClick={() => setHistoryOpen(true)}
                                                className="flex items-center gap-2 text-[13px] font-medium text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] mx-auto mb-3 transition-colors"
                                            >
                                                <History className="w-3.5 h-3.5" />
                                                {conversationLanguage === 'ar' ? 'المحادثات السابقة' : 'Recent conversations'}
                                            </button>
                                            <div className="space-y-1.5">
                                                {pastSessions.slice(0, 3).map(s => {
                                                    const timeAgo = s.last_message_at ? getTimeAgo(s.last_message_at, conversationLanguage) : null;
                                                    const tag = guessConversationTag(s.preview);
                                                    return (
                                                        <button
                                                            key={s.session_id}
                                                            onClick={() => loadSession(s.session_id)}
                                                            className="w-full flex items-center gap-3 p-3 rounded-2xl bg-[var(--color-surface)]/50 hover:bg-[var(--color-surface)] border border-[var(--color-border)]/50 hover:border-[var(--color-border)] transition-all text-left group"
                                                        >
                                                            <div className="w-8 h-8 rounded-full bg-[var(--color-surface-elevated)] flex items-center justify-center flex-shrink-0">
                                                                <MessageSquare className="w-3.5 h-3.5 text-[var(--color-text-secondary)]" />
                                                            </div>
                                                            <div className="flex-1 min-w-0">
                                                                <div className="flex items-center gap-2">
                                                                    <p className="text-[13px] font-medium text-[var(--color-text-primary)] truncate" dir="auto">{s.preview || 'Conversation'}</p>
                                                                    {tag && (
                                                                        <span className={`flex-shrink-0 text-[9px] font-bold px-1.5 py-0.5 rounded-full ${tag.color}`}>{tag.label}</span>
                                                                    )}
                                                                </div>
                                                                <div className="flex items-center gap-2 mt-0.5">
                                                                    <span className="text-[11px] text-[var(--color-text-secondary)]">{s.message_count} {conversationLanguage === 'ar' ? 'رسالة' : 'messages'}</span>
                                                                    {timeAgo && <span className="text-[10px] text-[var(--color-text-muted)]">· {timeAgo}</span>}
                                                                </div>
                                                            </div>
                                                            <ChevronRight className="w-4 h-4 text-[var(--color-text-muted)] group-hover:text-[var(--color-text-secondary)] flex-shrink-0 transition-colors" />
                                                        </button>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    )}
                            </div>
                        )}

                        {/* Messages */}
                        {hasStarted && (
                            <div className="px-4 pt-6 pb-8">
                                {messages.map((msg, index) => (
                                    <div key={msg.id} className="mb-6 animate-fade-in">
                                        <div className="flex gap-4">
                                            <div className="flex-shrink-0 mt-1">
                                                {msg.role === 'user' ? null : <AgentAvatar />}
                                            </div>

                                            <div className={`flex-1 min-w-0 ${msg.role === 'user' ? 'flex justify-end' : ''}`}>
                                                {msg.role === 'user' ? (
                                                    <div
                                                        className="bg-gray-100 dark:bg-gray-800/80 text-[var(--color-text-primary)] px-4 py-3 md:px-5 md:py-3.5 rounded-3xl rounded-br-[8px] max-w-[95%] md:max-w-[85%] text-[14px] md:text-[15px] leading-[1.6] md:leading-relaxed shadow-sm font-medium"
                                                        dir="auto"
                                                    >
                                                        {msg.content}
                                                    </div>
                                                ) : (
                                                    <div className="text-[14px] md:text-[15px] leading-[1.6] md:leading-relaxed text-[var(--color-text-secondary)] tracking-wide pt-1" dir="auto">
                                                        <TypewriterMarkdown content={msg.content} animate={msg.id === lastAiMsgId} />

                                                        {/* Visualizations */}
                                                        {msg.uiActions && msg.uiActions.length > 0 && (
                                                            <div className="mt-5 space-y-3" dir="ltr">
                                                                    <AnimatePresence>
                                                                        {msg.uiActions
                                                                            .filter(shouldRenderUiAction)
                                                                            .map((action: UiAction, idx: number) => (
                                                                                <motion.div 
                                                                                    key={idx}
                                                                                    initial={{ opacity: 0, height: 0, scale: 0.95, filter: 'blur(4px)' }}
                                                                                    animate={{ opacity: 1, height: 'auto', scale: 1, filter: 'blur(0px)' }}
                                                                                    transition={{ 
                                                                                        duration: 0.6, 
                                                                                        ease: [0.16, 1, 0.3, 1], // easeOutExpo
                                                                                        delay: idx * 0.15 
                                                                                    }}
                                                                                    className="ai-visualization w-full max-w-full"
                                                                                >
                                                                                    <VisualizationRenderer
                                                                                        type={action.type}
                                                                                        data={(action.data || action) as VisualizationRendererProps['data']}
                                                                                        isRTL={isArabic(msg.content)}
                                                                                    />
                                                                                </motion.div>
                                                                            ))}
                                                                </AnimatePresence>
                                                            </div>
                                                        )}

                                                        {/* Analytics Panel */}
                                                        {msg.analyticsContext?.has_analytics && (!msg.allProperties || msg.allProperties.length === 0) && (
                                                                <motion.div 
                                                                    initial={{ opacity: 0, y: 15 }}
                                                                    animate={{ opacity: 1, y: 0 }}
                                                                    transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
                                                                    className="mt-5 p-6 rounded-[20px] border border-[var(--color-border)]/50 bg-[var(--color-surface)] shadow-[0_4px_24px_rgba(0,0,0,0.03)]" 
                                                                    dir="ltr"
                                                                >
                                                                <div className="flex items-center gap-2 mb-5">
                                                                    <div className="p-1.5 bg-emerald-50 dark:bg-emerald-500/10 rounded-lg">
                                                                        <BarChart2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" strokeWidth={2.5} />
                                                                    </div>
                                                                    <span className="text-[11px] font-bold text-[var(--color-text-primary)] uppercase tracking-widest pl-1">Market Intelligence</span>
                                                                </div>
                                                                <div className="grid grid-cols-1 xs:grid-cols-2 md:grid-cols-3 gap-y-6 gap-x-4">
                                                                    {(msg.analyticsContext.avg_price_sqm ?? 0) > 0 && (
                                                                        <div>
                                                                            <div className="text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">Avg Price/m²</div>
                                                                            <div className="text-xl font-bold text-[var(--color-text-primary)] tracking-tight">
                                                                                {msg.analyticsContext.avg_price_sqm?.toLocaleString()} <span className="text-[13px] font-medium text-[var(--color-text-muted)] tracking-normal">EGP</span>
                                                                            </div>
                                                                        </div>
                                                                    )}
                                                                    {(msg.analyticsContext.growth_rate ?? 0) > 0 && (
                                                                        <div>
                                                                            <div className="text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">Growth Rate</div>
                                                                            <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400 tracking-tight">
                                                                                +{((msg.analyticsContext.growth_rate ?? 0) * 100).toFixed(0)}% <span className="text-[13px] font-medium text-[var(--color-text-muted)] tracking-normal">YoY</span>
                                                                            </div>
                                                                        </div>
                                                                    )}
                                                                    {(msg.analyticsContext.rental_yield ?? 0) > 0 && (
                                                                        <div>
                                                                            <div className="text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">Rental Yield</div>
                                                                            <div className="text-xl font-bold text-[var(--color-text-primary)] tracking-tight">
                                                                                {((msg.analyticsContext.rental_yield ?? 0) * 100).toFixed(1)}%
                                                                            </div>
                                                                        </div>
                                                                    )}
                                                                </div>
                                                                </motion.div>
                                                        )}

                                                        {/* Property Cards */}
                                                        {msg.allProperties && msg.allProperties.length > 0 && (
                                                            <div className="mt-5 space-y-2" dir="ltr">
                                                                {msg.allProperties.map((prop, idx) => (
                                                                    <div
                                                                        key={prop.id}
                                                                        onClick={() => { setActiveContext({ property: prop }); setContextPaneOpen(true); }}
                                                                        className="group relative flex gap-3 md:gap-4 p-3 md:p-4 border border-[var(--color-border)]/60 hover:border-emerald-500/40 bg-[var(--color-surface)]/60 backdrop-blur-sm rounded-2xl cursor-pointer transition-all duration-300 hover:shadow-[0_8px_30px_rgb(0,0,0,0.04)] hover:-translate-y-0.5"
                                                                        style={{ animationDelay: `${idx * 80}ms` }}
                                                                    >
                                                                        {/* Image */}
                                                                        <div className="w-[72px] h-[72px] sm:w-[84px] sm:h-[84px] md:w-24 md:h-24 bg-[var(--color-surface-hover)] rounded-[14px] flex-shrink-0 overflow-hidden shadow-[inset_0_0_0_1px_rgba(0,0,0,0.05)]">
                                                                            <img src={prop.image} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700 ease-out" alt={prop.title} />
                                                                        </div>

                                                                        {/* Info */}
                                                                        <div className="flex-1 min-w-0 flex flex-col justify-center">
                                                                            <h3 className="font-semibold text-[var(--color-text-primary)] truncate text-[15px]" dir="auto">{prop.title}</h3>
                                                                            <p className="text-[13px] text-[var(--color-text-muted)] truncate mt-0.5" dir="auto">
                                                                                {prop.location} {prop.developer && <span className="mx-1.5 opacity-50">·</span>} {prop.developer}
                                                                            </p>
                                                                            <div className="flex flex-wrap items-center gap-1.5 md:gap-2.5 mt-2.5">
                                                                                <span className="text-[14px] md:text-[15px] font-bold text-[var(--color-text-primary)] tracking-tight">
                                                                                    {(prop.price / 1000000).toFixed(1)}M <span className="text-[11px] font-medium text-[var(--color-text-muted)]">EGP</span>
                                                                                </span>
                                                                                {prop.metrics.price_per_sqm > 0 && (
                                                                                    <span className="text-[11px] font-medium text-[var(--color-text-muted)] bg-[var(--color-surface-elevated)] px-2 py-0.5 rounded-md">
                                                                                        {prop.metrics.price_per_sqm.toLocaleString()}/m²
                                                                                    </span>
                                                                                )}
                                                                                {prop.metrics.roi > 0 && (
                                                                                    <span className="text-[11px] font-semibold text-emerald-700 dark:text-emerald-300 bg-emerald-500/10 px-2 py-0.5 rounded-md">
                                                                                        +{prop.metrics.roi}% ROI
                                                                                    </span>
                                                                                )}
                                                                            </div>
                                                                            {prop.metrics.wolf_score > 0 && (
                                                                                <div className="mt-2.5 flex items-center gap-2">
                                                                                    <div className="flex-1 h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden max-w-[120px]">
                                                                                        <div
                                                                                            className="h-full rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.4)] transition-all duration-1000 ease-out"
                                                                                            style={{ width: `${Math.min(prop.metrics.wolf_score, 100)}%` }}
                                                                                        />
                                                                                    </div>
                                                                                    <span className="text-[10px] text-[var(--color-text-secondary)] font-semibold">{prop.metrics.wolf_score}<span className="text-[8px] text-[var(--color-text-muted)] font-medium">/100</span></span>
                                                                                </div>
                                                                            )}
                                                                        </div>

                                                                        {/* Inline Action Buttons */}
                                                                        <div className="flex flex-col items-center gap-1.5 self-center flex-shrink-0">
                                                                            {user && (
                                                                                <button
                                                                                    onClick={(e) => handleSaveProperty(prop, e)}
                                                                                    className={`p-1.5 rounded-lg transition-colors ${
                                                                                        savedPropertyIds.has(String(prop.id))
                                                                                            ? 'text-red-500 bg-red-500/10'
                                                                                            : 'text-[var(--color-text-muted)] hover:text-red-500 hover:bg-red-500/10'
                                                                                    }`}
                                                                                    title={savedPropertyIds.has(String(prop.id)) ? 'Saved' : 'Save'}
                                                                                >
                                                                                    <Heart className="w-3.5 h-3.5" fill={savedPropertyIds.has(String(prop.id)) ? 'currentColor' : 'none'} />
                                                                                </button>
                                                                            )}
                                                                            <button
                                                                                onClick={(e) => handleInlineValuation(prop, e)}
                                                                                className="p-1.5 rounded-lg text-[var(--color-text-muted)] hover:text-emerald-500 hover:bg-emerald-500/10 transition-colors"
                                                                                title="Run Valuation"
                                                                            >
                                                                                <BarChart3 className="w-3.5 h-3.5" />
                                                                            </button>
                                                                            <button
                                                                                onClick={(e) => handleInlineCompare(prop, e)}
                                                                                className="p-1.5 rounded-lg text-[var(--color-text-muted)] hover:text-blue-500 hover:bg-blue-500/10 transition-colors"
                                                                                title="Compare"
                                                                            >
                                                                                <Scale className="w-3.5 h-3.5" />
                                                                            </button>
                                                                        </div>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        )}

                                                        {/* Actions + Suggestions */}
                                                        {!isTyping && (
                                                            <>
                                                                <div className="flex gap-1 mt-4" dir="ltr">
                                                                    <button
                                                                        onClick={() => copyToClipboard(msg.content, msg.id)}
                                                                        className="p-1.5 hover:bg-[var(--color-surface)] rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
                                                                        title={copiedMsgId === msg.id ? 'Copied!' : 'Copy'}
                                                                    >
                                                                        {copiedMsgId === msg.id ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                                                                    </button>
                                                                    <button
                                                                        onClick={() => handleRetry(index)}
                                                                        className="p-1.5 hover:bg-[var(--color-surface)] rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
                                                                        title="Retry"
                                                                    >
                                                                        <RefreshCw className="w-3.5 h-3.5" />
                                                                    </button>
                                                                </div>

                                                                {index === messages.length - 1 && (
                                                                    <SuggestionChips
                                                                        suggestions={msg.suggestions && msg.suggestions.length > 0 ? msg.suggestions : generateSuggestions(msg)}
                                                                        onSelect={(suggestion) => handleSendMessage(suggestion)}
                                                                        isRTL={msg.detectedLanguage === 'ar' || isArabic(msg.content)}
                                                                    />
                                                                )}
                                                            </>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}

                                {/* Thinking steps indicator */}
                                {isTyping && (
                                    <ThinkingSteps lastUserMessage={messages.length > 0 ? messages[messages.length - 1].content : ''} />
                                )}

                                {/* Anonymous gate — shown after free messages exhausted */}
                                {(isGated || anonGateShown) && (
                                    <AnonymousChatGate language={conversationLanguage} />
                                )}

                                <div ref={messagesEndRef} />
                            </div>
                        )}
                    </div>
                </div>

                {/* Input Bar - Floating Figma Style (only shown after conversation starts, hidden when gated) */}
                {hasStarted && !isGated && !anonGateShown && (
                    <div className="sticky bottom-0 left-0 right-0 z-40 px-3 md:px-6 pb-2 md:pb-6 pt-2 md:pt-12 bg-gradient-to-t from-[var(--color-background)] via-[var(--color-background)]/95 to-transparent pointer-events-none">
                        <div className="max-w-[800px] mx-auto relative pointer-events-auto">
                            {inputBar}

                            <div className="text-center mt-1.5 md:mt-3">
                                <p className="text-[10px] md:text-[11px] font-medium text-[var(--color-text-muted)]/60" dir="auto">{conversationLanguage === 'ar' ? 'CoInvestor وكيل ذكاء اصطناعي. يرجى التحقق من بيانات الاستثمار المهمة بشكل مستقل.' : 'CoInvestor is an AI agent. Please verify critical investment data independently.'}</p>
                            </div>
                        </div>
                    </div>
                )}

            </main>

            {/* Context Pane - Floating Style */}
            {contextPaneOpen && activeContext?.property && (
                <aside className="w-full lg:w-[400px] bg-[var(--color-surface)]/95 backdrop-blur-2xl lg:border-l border-[var(--color-border)]/50 flex flex-col z-50 fixed inset-0 lg:static lg:flex lg:shadow-[-10px_0_40px_rgba(0,0,0,0.04)] lg:m-4 lg:ml-0 lg:rounded-[24px] overflow-hidden">
                    {/* Header */}
                    <div className="h-14 border-b border-[var(--color-border)]/50 flex items-center justify-between px-6 flex-shrink-0 bg-white/50 dark:bg-gray-800/50">
                        <div className="flex items-center gap-2.5">
                            <span className="text-[15px] font-semibold text-[var(--color-text-primary)]">Details</span>
                            <span className="text-[10px] text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full font-bold uppercase tracking-widest shadow-sm">Live Context</span>
                        </div>
                        <button
                            onClick={() => setContextPaneOpen(false)}
                            aria-label={conversationLanguage === 'ar' ? 'إغلاق التفاصيل' : 'Close details pane'}
                            title="Close details pane"
                            className="w-8 h-8 flex items-center justify-center text-[var(--color-text-muted)] hover:text-gray-900 dark:hover:text-white bg-gray-100/50 dark:bg-gray-800/50 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full transition-all"
                        >
                            <X className="w-4 h-4" strokeWidth={2} />
                        </button>
                    </div>

                    <div className="flex-1 overflow-y-auto p-6 space-y-7 custom-scrollbar">

                        {/* Image */}
                        <div className="space-y-4">
                            <div className="aspect-video bg-[var(--color-surface-hover)] rounded-2xl overflow-hidden relative shadow-[inset_0_0_0_1px_rgba(0,0,0,0.05)] shadow-md">
                                <img
                                    src={activeContext.property.image}
                                    className="w-full h-full object-cover hover:scale-105 transition-transform duration-700 ease-out"
                                    alt="Property"
                                />
                                <div className="absolute top-3 right-3 bg-white/90 dark:bg-gray-900/90 backdrop-blur-md text-[var(--color-text-primary)] px-3 py-1.5 rounded-full text-[11px] font-semibold shadow-sm border border-black/5 dark:border-white/10">
                                    {activeContext.property.status}
                                </div>
                            </div>
                            <div>
                                <h2 className="text-[22px] font-semibold text-[var(--color-text-primary)] leading-tight mb-1.5 tracking-tight" dir="auto">
                                    {activeContext.property.title}
                                </h2>
                                <p className="text-[var(--color-text-muted)] flex items-center gap-1.5 text-[14px] font-medium" dir="auto">
                                    <MapPin className="w-4 h-4 text-emerald-500" strokeWidth={2} />
                                    {activeContext.property.location}
                                </p>
                            </div>
                        </div>

                        {/* Score */}
                        <div className="bg-gradient-to-br from-emerald-500/5 to-transparent rounded-[20px] p-5 border border-emerald-500/10 relative overflow-hidden">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 blur-[40px] rounded-full" />
                            <div className="flex items-center gap-2 mb-5 relative z-10">
                                <Sparkles className="w-5 h-5 text-emerald-500" strokeWidth={2} />
                                <h3 className="text-[15px] font-semibold text-[var(--color-text-primary)]">Osool Intelligence Score</h3>
                            </div>
                            <div className="flex gap-4 sm:gap-8 relative z-10">
                                <div>
                                    <div className="text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Index</div>
                                    <div className="text-3xl font-bold text-emerald-500 tracking-tighter">
                                        {activeContext.property.metrics.wolf_score}
                                        <span className="text-lg font-medium text-[var(--color-text-muted)] tracking-normal">/100</span>
                                    </div>
                                </div>
                                <div className="w-px bg-emerald-500/20" />
                                <div>
                                    <div className="text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Liquidity</div>
                                    <div className="text-3xl font-bold text-[var(--color-text-primary)] tracking-tighter">
                                        {activeContext.property.metrics.liquidity_rating}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Specs Grid */}
                        <div>
                            <h3 className="text-[11px] font-bold text-[var(--color-text-muted)] mb-3.5 uppercase tracking-widest pl-1">Specifications</h3>
                            <div className="grid grid-cols-2 gap-2">
                                <div className="bg-gray-50/50 dark:bg-gray-800/40 p-4 rounded-2xl border border-[var(--color-border)]/50">
                                    <div className="text-[11px] font-medium text-[var(--color-text-muted)] mb-1">Total Built Area</div>
                                    <div className="text-[var(--color-text-primary)] font-semibold text-[15px]">
                                        {activeContext.property.metrics.size} <span className="text-[12px] font-medium text-[var(--color-text-muted)]">m²</span>
                                    </div>
                                </div>
                                <div className="bg-gray-50/50 dark:bg-gray-800/40 p-4 rounded-2xl border border-[var(--color-border)]/50">
                                    <div className="text-[11px] font-medium text-[var(--color-text-muted)] mb-1">Bedrooms</div>
                                    <div className="text-[var(--color-text-primary)] font-semibold text-[15px]">
                                        {activeContext.property.metrics.bedrooms}
                                    </div>
                                </div>
                                <div className="bg-gray-50/50 dark:bg-gray-800/40 p-4 rounded-2xl border border-[var(--color-border)]/50">
                                    <div className="text-[11px] font-medium text-[var(--color-text-muted)] mb-1">Price per m²</div>
                                    <div className="text-[var(--color-text-primary)] font-semibold text-[15px]">
                                        {activeContext.property.metrics.price_per_sqm > 0
                                            ? `${(activeContext.property.metrics.price_per_sqm / 1000).toFixed(1)}k`
                                            : 'N/A'
                                        }
                                    </div>
                                </div>
                                <div className="bg-emerald-50/50 dark:bg-emerald-500/5 p-4 rounded-2xl border border-emerald-500/20">
                                    <div className="text-[11px] font-medium text-emerald-600/80 dark:text-emerald-400/80 mb-1">Total Valuation</div>
                                    <div className="text-emerald-600 dark:text-emerald-400 font-bold text-[15px]">
                                        {(activeContext.property.price / 1000000).toFixed(2)}M
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Tags */}
                        {activeContext.property.tags?.length > 0 && (
                            <div className="flex flex-wrap gap-2 pt-2">
                                {activeContext.property.tags.map((tag, i) => (
                                    <span key={i} className="text-[12px] font-medium bg-gray-100 dark:bg-gray-800 text-[var(--color-text-primary)] px-3.5 py-1.5 rounded-full border border-gray-200 dark:border-gray-700">
                                        {tag}
                                    </span>
                                ))}
                            </div>
                        )}

                        <div className="pt-4 pb-2">
                            <button className="w-full py-4 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-[16px] font-semibold text-[15px] transition-all hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-black/10 dark:shadow-white/10 flex items-center justify-center gap-2">
                                Request Private Viewing
                                <ChevronRight className="w-4 h-4 opacity-70" strokeWidth={2.5} />
                            </button>
                        </div>
                    </div>
                </aside>
            )}

            {/* ── Market Pulse Sidebar ── */}
            <MarketPulseSidebar language={conversationLanguage} onPrompt={handleSendMessage} />

            {/* ── Conversation History Overlay ── */}
            <AnimatePresence>
                {historyOpen && (
                    <>
                        {/* Backdrop */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50"
                            onClick={() => setHistoryOpen(false)}
                        />
                        {/* Slide-in panel */}
                        <motion.aside
                            initial={{ x: -320, opacity: 0 }}
                            animate={{ x: 0, opacity: 1 }}
                            exit={{ x: -320, opacity: 0 }}
                            transition={{ type: 'spring', damping: 28, stiffness: 350 }}
                            className="fixed left-0 top-0 bottom-0 w-[320px] bg-[var(--color-surface)] border-r border-[var(--color-border)] z-50 flex flex-col shadow-2xl"
                        >
                            <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--color-border)]">
                                <span className="text-[15px] font-semibold text-[var(--color-text-primary)]">{conversationLanguage === 'ar' ? 'المحادثات السابقة' : 'Past Conversations'}</span>
                                <button
                                    onClick={() => setHistoryOpen(false)}
                                    aria-label={conversationLanguage === 'ar' ? 'إغلاق' : 'Close'}
                                    title="Close"
                                    className="p-1.5 hover:bg-[var(--color-surface-elevated)] rounded-lg transition-colors"
                                >
                                    <X className="w-4 h-4 text-[var(--color-text-muted)]" />
                                </button>
                            </div>
                            <div className="flex-1 overflow-y-auto p-3 space-y-1">
                                {pastSessions.length === 0 ? (
                                    <div className="text-center py-12 text-[var(--color-text-muted)]">
                                        <History className="w-10 h-10 mx-auto mb-3 opacity-30" />
                                        <p className="text-sm">{conversationLanguage === 'ar' ? 'لا توجد محادثات سابقة بعد' : 'No past conversations yet'}</p>
                                    </div>
                                ) : (
                                    pastSessions.map(s => (
                                        <button
                                            key={s.session_id}
                                            onClick={() => loadSession(s.session_id)}
                                            className={`w-full text-left p-3 rounded-xl hover:bg-[var(--color-surface-elevated)] transition-colors group ${s.session_id === sessionIdRef.current ? 'bg-emerald-500/10 border border-emerald-500/20' : ''}`}
                                        >
                                            <p className="text-[13px] font-medium text-[var(--color-text-primary)] truncate" dir="auto">
                                                {s.preview || 'Conversation'}
                                            </p>
                                            <div className="flex items-center gap-2 mt-1">
                                                <span className="text-[11px] text-[var(--color-text-muted)]">
                                                    {s.message_count} {conversationLanguage === 'ar' ? 'رسالة' : 'messages'}
                                                </span>
                                                {s.last_message_at && (
                                                    <span className="text-[11px] text-[var(--color-text-muted)]">
                                                        · {new Date(s.last_message_at).toLocaleDateString()}
                                                    </span>
                                                )}
                                            </div>
                                        </button>
                                    ))
                                )}
                            </div>
                            <div className="p-3 border-t border-[var(--color-border)]">
                                <button
                                    onClick={() => { handleNewChat(); setHistoryOpen(false); }}
                                    className="w-full py-2.5 bg-[var(--color-text-primary)] text-[var(--color-background)] rounded-xl text-[13px] font-semibold hover:opacity-90 transition-all flex items-center justify-center gap-2"
                                >
                                    <Plus className="w-4 h-4" />
                                    {conversationLanguage === 'ar' ? 'محادثة جديدة' : 'New Conversation'}
                                </button>
                            </div>
                        </motion.aside>
                    </>
                )}
            </AnimatePresence>
        </div>
        </LayoutGroup>
    );
}
