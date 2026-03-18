'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams, useRouter as useNextRouter } from 'next/navigation';
import { motion, AnimatePresence, LayoutGroup } from 'framer-motion';
import {
    Sparkles, MapPin,
    X, ChevronRight,
    BarChart2, Shield, Search, TrendingUp,
    Copy, RefreshCw, ArrowUp,
    History, Plus, MessageSquare, Check,
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
import type { SuggestionChipItem } from '@/components/SuggestionChips';
import MarketPulseSidebar from '@/components/MarketPulseSidebar';
import OnboardingFlow from '@/components/chat/OnboardingFlow';
import { getSmartEmptyStateSuggestions } from '@/lib/suggestions';
import ChatInsightsShell from '@/components/chat/ChatInsightsShell';
import { GlossaryAnnotated } from '@/components/GlossaryTooltip';
import { useVoiceRecording } from '@/hooks/useVoiceRecording';
import { useVoicePlayback } from '@/hooks/useVoicePlayback';
import VoiceOrb from '@/components/VoiceOrb';
import SpeakerButton from '@/components/SpeakerButton';
import BentoResultGrid from '@/components/chat/BentoResultGrid';
import MessageSkeleton from '@/components/chat/MessageSkeleton';

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
        <div dir={msgIsArabic ? 'rtl' : 'ltr'} className={msgIsArabic ? 'text-end' : 'text-start'}>
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    p: ({ node, children, ...props }) => {
                        if (!msgIsArabic) {
                            const annotated = React.Children.map(children, (child, i) =>
                                typeof child === 'string'
                                    ? <GlossaryAnnotated key={i} text={child} />
                                    : child
                            );
                            return <p className="mb-1.5 md:mb-3 last:mb-0 leading-[1.6] md:leading-relaxed text-start" {...props}>{annotated}</p>;
                        }
                        return <p className="mb-1.5 md:mb-3 last:mb-0 leading-[1.6] md:leading-relaxed text-end" {...props}>{children}</p>;
                    },
                    ul: ({ node, ...props }) => (
                        <ul className={`list-disc mb-2 md:mb-3 space-y-0.5 md:space-y-1 ${msgIsArabic ? 'pe-5' : 'ps-5'}`} {...props} />
                    ),
                    ol: ({ node, ...props }) => (
                        <ol className={`list-decimal mb-2 md:mb-3 space-y-0.5 md:space-y-1 ${msgIsArabic ? 'pe-5' : 'ps-5'}`} {...props} />
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
                            className={`${msgIsArabic ? 'border-e-2 pe-4' : 'border-s-2 ps-4'} border-emerald-500/40 py-1 my-2 text-[var(--color-text-secondary)]`}
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
                        <th className="border-b border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-start text-[var(--color-text-primary)] font-medium text-xs uppercase tracking-wider" {...props} />
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
        <div dir={msgIsArabic ? 'rtl' : 'ltr'} className={msgIsArabic ? 'text-end' : 'text-start'}>
            <div className="whitespace-pre-wrap leading-relaxed text-[15px] text-[var(--color-text-secondary)]">
                {displayed}
            </div>
            <span className="inline-block w-[2px] h-[1.1em] bg-emerald-500 animate-pulse align-text-bottom ms-0.5" />
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
    const [transcriptHighlight, setTranscriptHighlight] = useState(false);
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
    const [isPinnedToBottom, setIsPinnedToBottom] = useState(true);
    const [showNewMessagesCue, setShowNewMessagesCue] = useState(false);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const scrollViewportRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);
    const sessionIdRef = useRef<string>(getOrCreateSessionId());
    const hasFetchedHistory = useRef(false);
    const seededPromptRef = useRef<string | null>(null);

    const userName = user?.full_name || user?.email?.split('@')[0] || (conversationLanguage === 'ar' ? 'مستثمر' : 'there');

    // ── Whisper-powered voice recording ──
    const { status: voiceStatus, isListening, amplitude, startRecording, stopRecording } = useVoiceRecording({
        language: conversationLanguage === 'ar' ? 'ar-EG' : 'auto',
        silenceThresholdMs: 2000,
        onTranscript: (text) => {
            setInputValue(text);
            inputRef.current?.focus();
            setTranscriptHighlight(true);
            setTimeout(() => setTranscriptHighlight(false), 600);
        },
        onError: (msg) => console.warn('[Voice]', msg),
    });
    // ── OpenAI TTS playback ──
    const { playbackStatus, speak: speakTTS, pause: pauseTTS, resume: resumeTTS, stop: stopTTS } = useVoicePlayback();
    const handleVoiceToggle = useCallback(() => {
        if (isListening || voiceStatus === 'processing') {
            stopRecording();
        } else {
            stopTTS(); // stop any playing TTS before recording
            startRecording();
        }
    }, [isListening, voiceStatus, startRecording, stopRecording, stopTTS]);
    const handleSpeakerClick = useCallback((text: string, lang: string) => {
        if (playbackStatus === 'playing') {
            pauseTTS();
        } else if (playbackStatus === 'paused') {
            resumeTTS();
        } else {
            speakTTS(text, lang);
        }
    }, [playbackStatus, speakTTS, pauseTTS, resumeTTS]);

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

    // Voice transcript syncs via onTranscript callback in useVoiceRecording

    const hasStarted = messages.length > 0;

    const scrollToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
        const viewport = scrollViewportRef.current;
        if (!viewport) return;
        viewport.scrollTo({ top: viewport.scrollHeight, behavior });
        setIsPinnedToBottom(true);
        setShowNewMessagesCue(false);
    }, []);

    const handleScroll = useCallback(() => {
        const viewport = scrollViewportRef.current;
        if (!viewport) return;
        const distanceFromBottom = viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight;
        const nearBottom = distanceFromBottom < 120;
        setIsPinnedToBottom(nearBottom);
        if (nearBottom) {
            setShowNewMessagesCue(false);
        }
    }, []);

    useEffect(() => {
        if (!hasStarted) return;
        if (isPinnedToBottom) {
            const frame = window.requestAnimationFrame(() => {
                scrollToBottom(isTyping ? 'auto' : 'smooth');
            });
            return () => window.cancelAnimationFrame(frame);
        }

        setShowNewMessagesCue(true);
    }, [messages, isTyping, hasStarted, isPinnedToBottom, scrollToBottom]);

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
    const emptyStateSuggestions = React.useMemo(
        () => getSmartEmptyStateSuggestions(
            conversationLanguage,
            typeof profile?.level === 'string' ? profile.level : 'curious',
            savedPropertyIds.size
        ),
        [conversationLanguage, profile?.level, savedPropertyIds.size]
    );

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
        setIsPinnedToBottom(true);
        setShowNewMessagesCue(false);
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
            setIsPinnedToBottom(true);
            setShowNewMessagesCue(false);
            setLastAiMsgId(null); // don't animate old messages
            setHistoryOpen(false);
        } catch (err) {
            console.error('[History] Failed to load session', err);
        }
    }, []);

    const [copiedMsgId, setCopiedMsgId] = useState<number | null>(null);

    const [showOnboarding, setShowOnboarding] = useState(false);
    useEffect(() => {
        if (profile?.properties_analyzed === 0 && !localStorage.getItem('onboarding_skipped') && messages.length === 0) {
            setShowOnboarding(true);
        }
    }, [profile, messages.length]);

    const handleOnboardingComplete = (data: any) => {
        localStorage.setItem('onboarding_skipped', 'true');
        setShowOnboarding(false);
        const prompt = `I am looking for ${data.goal} properties. ` + 
            (data.regions.length > 0 ? `I prefer these regions: ${data.regions.join(', ')}. ` : '') + 
            `My budget is ${data.budget}. Please recommend some options.`;
        handleSendMessage(prompt);
    };

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
            <div className={`bg-[var(--color-surface)]/95 backdrop-blur-2xl rounded-[24px] flex flex-col transition-all duration-300 ${isTyping ? 'opacity-70 scale-[0.99]' : ''} shadow-[0_8px_30px_rgba(0,0,0,0.04)] border ${isListening ? 'border-emerald-500/40 shadow-[0_0_0_3px_rgba(16,185,129,0.06)]' : 'border-[var(--color-border)]/40'}${transcriptHighlight ? ' ring-2 ring-emerald-500/40' : ''}`}>

                {/* Voice status bar — shown while recording or processing */}
                <AnimatePresence>
                    {(voiceStatus === 'recording' || voiceStatus === 'processing') && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.25 }}
                            className="px-5 pt-3 pb-0 flex items-center gap-2.5 overflow-hidden"
                        >
                            <VoiceOrb status={voiceStatus} amplitude={amplitude} onClick={handleVoiceToggle} isRTL={conversationLanguage === 'ar'} size="sm" />
                            <span className="ms-auto text-[11px] text-emerald-600 dark:text-emerald-400 font-semibold animate-pulse flex-shrink-0">
                                {voiceStatus === 'processing'
                                    ? (conversationLanguage === 'ar' ? 'يعالج...' : 'Transcribing...')
                                    : (conversationLanguage === 'ar' ? 'يستمع...' : 'Listening...')}
                            </span>
                        </motion.div>
                    )}
                </AnimatePresence>

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

                    <div className="flex-shrink-0 pb-2 md:pb-3 pe-2 md:pe-3 flex items-center gap-1.5">
                        {/* Voice orb — Whisper-powered via MediaRecorder */}
                        <VoiceOrb
                            status={voiceStatus}
                            amplitude={amplitude}
                            onClick={handleVoiceToggle}
                            isRTL={conversationLanguage === 'ar'}
                            size="sm"
                        />
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

    const enrichSuggestion = useCallback((prompt: string, lang: string): SuggestionChipItem => {
        const lower = prompt.toLowerCase();
        const isAr = lang === 'ar' || isArabic(prompt);

        if (lower.includes('roi') || lower.includes('عائد') || lower.includes('invest') || lower.includes('استثمار')) {
            return {
                icon: BarChart2,
                label: prompt,
                prompt,
                snippet: 'Returns, downside, and market fit',
                snippetAr: 'العائد والمخاطر وملاءمة السوق',
                trend: 'up',
            };
        }

        if (lower.includes('developer') || lower.includes('مطور') || lower.includes('delivery') || lower.includes('تسليم')) {
            return {
                icon: Shield,
                label: prompt,
                prompt,
                snippet: 'Track record, delays, and risk flags',
                snippetAr: 'سجل التنفيذ والتأخير وعلامات المخاطر',
                trend: 'neutral',
            };
        }

        if (lower.includes('payment') || lower.includes('installment') || lower.includes('أقساط') || lower.includes('سداد')) {
            return {
                icon: Sparkles,
                label: prompt,
                prompt,
                snippet: 'Down payment, tenure, and flexibility',
                snippetAr: 'المقدم ومدة السداد والمرونة',
                trend: 'neutral',
            };
        }

        if (lower.includes('compare') || lower.includes('قارن') || lower.includes('similar') || lower.includes('مشابه')) {
            return {
                icon: TrendingUp,
                label: prompt,
                prompt,
                snippet: 'Side-by-side shortlist with trade-offs',
                snippetAr: 'مقارنة سريعة مع إبراز الفروقات',
                trend: 'up',
            };
        }

        return {
            icon: Search,
            label: prompt,
            prompt,
            snippet: isAr ? undefined : 'Fast follow-up from the current context',
            snippetAr: isAr ? 'متابعة سريعة من نفس سياق الحوار' : undefined,
            trend: 'neutral',
        };
    }, []);

    const generateSuggestions = (msg: Message): SuggestionChipItem[] => {
        const content = msg.content.toLowerCase();
        const hasProperties = msg.allProperties && msg.allProperties.length > 0;
        const hasAnalytics = msg.analyticsContext?.has_analytics;
        const lang = msg.detectedLanguage || conversationLanguage || 'ar';
        const isAr = lang === 'ar';

        // Use a simple hash of content to rotate through options deterministically
        const hash = content.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);

        // Content-based triggers for variety
        if (content.includes('تضخم') || content.includes('inflation') || content.includes('فلوس')) {
            return (isAr
                ? ['إزاي أحمي فلوسي؟', 'عقار ولا شهادات بنك؟', 'حلل العائد بعد التضخم']
                : ['How to protect my money?', 'Property vs bank CDs?', 'Real return after inflation'])
                .map((prompt) => enrichSuggestion(prompt, lang));
        }
        if (content.includes('مطور') || content.includes('developer') || content.includes('تسليم') || content.includes('delivery')) {
            const opts = isAr
                ? ['سجل التسليم بتاعهم', 'هل فيه مطور أضمن؟', 'ورّيني التقييمات', 'مواعيد التسليم', 'المشاريع المتأخرة']
                : ['Their delivery track record', 'More reliable developer?', 'Show me ratings', 'Delivery timeline', 'Delayed projects'];
            return [opts[hash % opts.length], opts[(hash + 2) % opts.length], opts[(hash + 4) % opts.length]].map((prompt) => enrichSuggestion(prompt, lang));
        }
        if (content.includes('ساحل') || content.includes('coast') || content.includes('سوخنة') || content.includes('sokhna')) {
            return (isAr
                ? ['ساحل ولا سوخنة أحسن؟', 'العائد الإيجاري كام؟', 'أحسن كمبوند هناك؟']
                : ['Coast vs Sokhna?', 'Rental yield there?', 'Best compound there?'])
                .map((prompt) => enrichSuggestion(prompt, lang));
        }
        if (content.includes('أقساط') || content.includes('سداد') || content.includes('installment') || content.includes('payment')) {
            return (isAr
                ? ['أطول خطة سداد؟', 'سداد بدون فوايد؟', 'قارن خطط السداد']
                : ['Longest payment plan?', 'Interest-free options?', 'Compare payment plans'])
                .map((prompt) => enrichSuggestion(prompt, lang));
        }

        if (hasProperties) {
            const opts = isAr
                ? ['قارن العقارات دي', 'تحليل العائد', 'خطة السداد؟', 'تفاصيل أكتر عن الوحدة', 'وحدات مشابهة أرخص', 'مخاطر القرار']
                : ['Compare these properties', 'Show ROI analysis', 'Payment plan options?', 'More details on this unit', 'Similar but cheaper?', 'Decision risks'];
            return [opts[hash % opts.length], opts[(hash + 2) % opts.length], opts[(hash + 4) % opts.length]].map((prompt) => enrichSuggestion(prompt, lang));
        } else if (hasAnalytics) {
            const opts = isAr
                ? ['اتجاهات الأسعار', 'أفضل مناطق النمو', 'قارن البدائل', 'تحليل ضد التضخم', 'هل ده وقت مناسب؟']
                : ['Show price trends', 'Best growth areas?', 'Compare alternatives', 'Inflation analysis', 'Is this a good time?'];
            return [opts[hash % opts.length], opts[(hash + 2) % opts.length], opts[(hash + 4) % opts.length]].map((prompt) => enrichSuggestion(prompt, lang));
        } else {
            // General pool — rotate based on content hash for variety
            const opts = isAr
                ? ['أفضل العقارات', 'نظرة على السوق', 'حدد ميزانيتي', 'أفضل منطقة للاستثمار', 'إيه المطورين الموثوقين؟', 'فيه عروض حالياً؟', 'عايز أفهم العائد']
                : ['Top properties', 'Market overview', 'Set my budget', 'Best area for investment', 'Reliable developers?', 'Any current deals?', 'Explain ROI to me'];
            return [opts[hash % opts.length], opts[(hash + 2) % opts.length], opts[(hash + 4) % opts.length]].map((prompt) => enrichSuggestion(prompt, lang));
        }
    };

    return (
        <LayoutGroup>
        <div className="flex h-full min-h-0 w-full bg-[var(--color-background)] text-[var(--color-text-primary)] overflow-hidden selection:bg-emerald-500/15 relative">

            {/* Main Chat */}
            <main className="flex-1 flex flex-col relative min-w-0 h-full w-full min-h-0 z-0">
                {/* Ambient AI state — teal glow pulses while AI is thinking */}
                <AnimatePresence>
                    {isTyping && (
                        <motion.div
                            key="ambient"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 1.2 }}
                            className="pointer-events-none absolute inset-x-0 top-0 h-[400px] z-0"
                            aria-hidden="true"
                        >
                            <div className="absolute top-[-100px] left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-emerald-500/[0.04] dark:bg-emerald-400/[0.06] rounded-full blur-[90px] animate-ambient-pulse" />
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Top bar — sticky header with session controls */}
                {hasStarted && (
                    <div className="sticky top-0 start-0 end-0 z-30 bg-[var(--color-background)]/80 backdrop-blur-xl border-b border-[var(--color-border)]/30">
                        <div className="max-w-full lg:max-w-[980px] mx-auto px-3 sm:px-4 md:px-6">
                            <div className="flex items-center justify-between py-2 md:py-2.5">
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
                        </div>
                    </div>
                )}

                {/* Scrollable Content */}
                <div ref={scrollViewportRef} onScroll={handleScroll} className="flex-1 overflow-y-auto scroll-smooth">
                    <div className="max-w-full lg:max-w-[980px] mx-auto h-full w-full">

                        {/* Greeting */}
                        {!hasStarted && (
                            <div className="flex flex-col min-h-[calc(100dvh-6.5rem)] sm:min-h-[calc(100vh-8rem)] justify-start sm:justify-center px-3 sm:px-4 pt-6 sm:py-6 pb-4 sm:pb-6 relative">
                                {/* Decorative background elements */}
                                <div className="absolute top-[42%] sm:top-1/2 start-1/2 rtl:translate-x-1/2 ltr:-translate-x-1/2 -translate-y-1/2 w-[420px] h-[420px] sm:w-[600px] sm:h-[600px] bg-emerald-500/5 dark:bg-emerald-500/10 blur-[90px] sm:blur-[100px] rounded-full pointer-events-none -z-10" />

                                <div className="text-center w-full max-w-3xl mx-auto">
                                    <div className="flex items-center justify-center gap-3 mb-3 sm:mb-4">
                                        <AgentAvatar />
                                        <span className="text-[13px] font-semibold text-[var(--color-text-muted)] uppercase tracking-widest">Osool AI</span>
                                    </div>
                                    <h1 className="text-[1.75rem] sm:text-[2.2rem] md:text-[3rem] font-semibold tracking-tight leading-[1.15] mb-2.5 sm:mb-4 text-[var(--color-text-primary)]" dir="auto">
                                        {conversationLanguage === 'ar' ? `أهلاً، ${userName}` : `Hello, ${userName}`}
                                    </h1>
                                    <p className="text-[0.95rem] sm:text-[1.02rem] md:text-[1.15rem] text-[var(--color-text-secondary)] font-normal max-w-xl mx-auto leading-relaxed px-2 sm:px-4 md:px-0" dir="auto">
                                        {conversationLanguage === 'ar' ? 'وكيلك الذكي للعقارات — تحليل السوق، فرص الاستثمار، وتدقيق المطورين' : 'Your AI real estate agent — market analysis, investment opportunities, and developer audits'}<span className="text-emerald-500 font-bold ms-0.5">.</span>
                                    </p>
                                </div>

                                    {/* Centered Input Bar */}
                                    <div className="w-full max-w-[800px] mx-auto mt-4 sm:mt-6 px-1 sm:px-4">
                                        {inputBar}
                                    </div>

                                    {/* Quick Action Cards — enhanced with data snippets  */}
                                    <div className="md:hidden w-full max-w-[800px] mx-auto mt-3.5 px-1">
                                        <div className="space-y-2.5">
                                            {emptyStateSuggestions.slice(0, 3).map((s, i) => (
                                                <button
                                                    key={`mobile-${i}`}
                                                    onMouseDown={(e) => e.preventDefault()}
                                                    onClick={() => { handleSendMessage(s.prompt); setTimeout(() => inputRef.current?.focus(), 100); }}
                                                    className="w-full text-start p-3 rounded-xl border border-[var(--color-border)]/40 bg-[var(--color-surface)]/75 hover:border-emerald-500/35 transition-colors"
                                                >
                                                    <div className="flex items-start gap-2.5">
                                                        <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-500 mt-0.5">
                                                            <s.icon className="w-3.5 h-3.5" />
                                                        </div>
                                                        <div className="min-w-0 flex-1">
                                                            <div dir="auto" className="text-[13px] font-semibold text-[var(--color-text-primary)] leading-snug">{s.label}</div>
                                                            <div className="mt-1 text-[11px] text-[var(--color-text-secondary)]" dir="auto">
                                                                {conversationLanguage === 'ar' ? s.snippetAr : s.snippet}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </button>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="hidden md:grid w-full max-w-3xl mx-auto md:grid-cols-2 xl:grid-cols-4 gap-3 mt-5 md:mt-6 px-4">
                                        {emptyStateSuggestions.map((s, i) => (
                                            <button
                                                key={i}
                                                onMouseDown={(e) => e.preventDefault()}
                                                onClick={() => { handleSendMessage(s.prompt); setTimeout(() => inputRef.current?.focus(), 100); }}
                                                className="p-4 md:p-5 bg-[var(--color-surface)]/60 hover:bg-[var(--color-surface)] backdrop-blur-md rounded-2xl text-start transition-all duration-300 flex flex-col justify-between group border border-[var(--color-border)]/40 hover:border-emerald-500/30 hover:shadow-[0_8px_30px_rgba(16,185,129,0.06)] hover:-translate-y-1"
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
                                        <div className="hidden md:block w-full max-w-2xl mx-auto mt-8 px-4">
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
                                                            className="w-full flex items-center gap-3 p-3 rounded-2xl bg-[var(--color-surface)]/50 hover:bg-[var(--color-surface)] border border-[var(--color-border)]/50 hover:border-[var(--color-border)] transition-all text-start group"
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
                            <div className="px-2.5 sm:px-4 pt-4 sm:pt-6 pb-28 sm:pb-10">
                                {messages.map((msg, index) => (
                                    <div key={msg.id} className="mb-5 sm:mb-6 animate-fade-in">
                                        <div className="flex gap-3 sm:gap-4">
                                            <div className="flex flex-shrink-0 mt-1">
                                                {msg.role === 'user' ? null : <div className="scale-[0.85] sm:scale-100 origin-top"><AgentAvatar /></div>}
                                            </div>

                                            <div className={`flex-1 min-w-0 ${msg.role === 'user' ? 'flex justify-end' : ''}`}>
                                                {msg.role === 'user' ? (
                                                    <div
                                                        className="bg-[var(--color-surface)] border border-[var(--color-border)]/40 text-[var(--color-text-primary)] px-3.5 py-2.5 sm:px-5 sm:py-3.5 rounded-2xl sm:rounded-3xl sm:rounded-br-md max-w-[90%] sm:max-w-[82%] text-[14px] sm:text-[15px] leading-[1.55] sm:leading-relaxed shadow-sm font-medium"
                                                        dir="auto"
                                                    >
                                                        {msg.content}
                                                    </div>
                                                ) : (
                                                    <div className="text-[14px] sm:text-[15px] leading-[1.65] sm:leading-relaxed text-[var(--color-text-secondary)] pt-0.5 sm:pt-1" dir="auto">
                                                        <TypewriterMarkdown content={msg.content} animate={msg.id === lastAiMsgId} />

                                                        {/* Visualizations */}
                                                        {msg.uiActions && msg.uiActions.length > 0 && (
                                                            <div className="mt-4 sm:mt-5 space-y-2.5 sm:space-y-3" dir="ltr">
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
                                                                                    className="w-full max-w-full"
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
                                                                    className="mt-4 sm:mt-5 p-4 sm:p-6 rounded-[18px] sm:rounded-[20px] border border-[var(--color-border)]/50 bg-[var(--color-surface)] shadow-[0_4px_24px_rgba(0,0,0,0.03)]" 
                                                                    dir="ltr"
                                                                >
                                                                <div className="flex items-center gap-2 mb-5">
                                                                    <div className="p-1.5 bg-emerald-50 dark:bg-emerald-500/10 rounded-lg">
                                                                        <BarChart2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" strokeWidth={2.5} />
                                                                    </div>
                                                                    <span className="text-[11px] font-bold text-[var(--color-text-primary)] uppercase tracking-widest ps-1">Market Intelligence</span>
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

                                                        {/* Bento Results Grid — hero card + compact list + analytics tiles */}
                                                        <BentoResultGrid
                                                            properties={msg.allProperties ?? []}
                                                            analyticsContext={msg.analyticsContext ?? null}
                                                            language={msg.detectedLanguage || conversationLanguage}
                                                            savedIds={savedPropertyIds}
                                                            onOpenDetails={(prop) => { setActiveContext({ property: prop }); setContextPaneOpen(true); }}
                                                            onSave={handleSaveProperty}
                                                            onValuation={handleInlineValuation}
                                                            onCompare={handleInlineCompare}
                                                        />

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
                                                                    {msg.content.trim().length > 0 && (
                                                                        <SpeakerButton
                                                                            status={playbackStatus}
                                                                            onClick={() => handleSpeakerClick(msg.content, msg.detectedLanguage || conversationLanguage)}
                                                                            isRTL={conversationLanguage === 'ar'}
                                                                        />
                                                                    )}
                                                                </div>

                                                                {index === messages.length - 1 && (
                                                                    <SuggestionChips
                                                                        suggestions={msg.suggestions && msg.suggestions.length > 0 ? msg.suggestions.map((suggestion) => enrichSuggestion(suggestion, msg.detectedLanguage || conversationLanguage)) : generateSuggestions(msg)}
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

                                {/* Reserved-height skeleton while AI is responding */}
                                {isTyping && (() => {
                                    const lastUserMsg = [...messages].reverse().find(m => m.role === 'user');
                                    if (!lastUserMsg) return null;
                                    const c = lastUserMsg.content.toLowerCase();
                                    const hasPropertyKeyword = /property|عقار|شقة|villa|فيلا|show|find|compare|unit|فرصة|شراء|apartment/.test(c);
                                    const hasAnalyticsKeyword = /market|سوق|price|سعر|roi|trend|yield|growth|analytics/.test(c);
                                    if (hasPropertyKeyword) return <MessageSkeleton key="skel-prop" variant="property" />;
                                    if (hasAnalyticsKeyword) return <MessageSkeleton key="skel-ana" variant="analytics" />;
                                    return null;
                                })()}

                                {/* Anonymous gate — shown after free messages exhausted */}
                                {(isGated || anonGateShown) && (
                                    <AnonymousChatGate language={conversationLanguage} />
                                )}

                                <div ref={messagesEndRef} />
                            </div>
                        )}
                    </div>
                </div>

                {showNewMessagesCue && hasStarted && (
                    <div className="pointer-events-none absolute inset-x-0 bottom-24 md:bottom-32 z-30 flex justify-center px-4">
                        <motion.button
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: 10 }}
                            onClick={() => scrollToBottom('smooth')}
                            className="pointer-events-auto rounded-full border border-emerald-500/20 bg-[var(--color-surface)]/95 px-4 py-2 text-[12px] font-semibold text-[var(--color-text-primary)] shadow-[0_12px_30px_rgba(0,0,0,0.08)] backdrop-blur-xl transition-colors hover:border-emerald-500/40 hover:text-emerald-600 dark:hover:text-emerald-400"
                        >
                            {conversationLanguage === 'ar' ? 'رسائل جديدة' : 'New messages'}
                        </motion.button>
                    </div>
                )}

                {/* Input Bar - Floating Figma Style (only shown after conversation starts, hidden when gated) */}
                {hasStarted && !isGated && !anonGateShown && (
                    <div className="sticky bottom-0 start-0 end-0 z-40 px-2 sm:px-6 pb-[calc(0.5rem+env(safe-area-inset-bottom))] sm:pb-6 pt-1 sm:pt-10 bg-gradient-to-t from-[var(--color-background)] via-[var(--color-background)]/95 to-transparent pointer-events-none">
                        <div className="max-w-[800px] mx-auto relative pointer-events-auto">
                            {inputBar}

                            <div className="text-center mt-1.5 md:mt-3">
                                <p className="text-[10px] md:text-[11px] font-medium text-[var(--color-text-muted)]/60" dir="auto">{conversationLanguage === 'ar' ? 'CoInvestor وكيل ذكاء اصطناعي. يرجى التحقق من بيانات الاستثمار المهمة بشكل مستقل.' : 'CoInvestor is an AI agent. Please verify critical investment data independently.'}</p>
                            </div>
                        </div>
                    </div>
                )}

            </main>

            {/* Context Pane — Premium Insights Shell */}
            <ChatInsightsShell
                property={activeContext?.property ?? null}
                isOpen={contextPaneOpen}
                onClose={() => setContextPaneOpen(false)}
                language={conversationLanguage}
                onPrompt={handleSendMessage}
            />

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
                            className="fixed start-0 top-0 bottom-0 w-[320px] bg-[var(--color-surface)] border-e border-[var(--color-border)] z-50 flex flex-col shadow-2xl"
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
                                            className={`w-full text-start p-3 rounded-xl hover:bg-[var(--color-surface-elevated)] transition-colors group ${s.session_id === sessionIdRef.current ? 'bg-emerald-500/10 border border-emerald-500/20' : ''}`}
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
