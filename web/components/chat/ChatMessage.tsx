'use client';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles, BarChart2, Copy, RefreshCw, Check, ChevronLeft, ChevronRight, X,
} from 'lucide-react';
import dynamic from 'next/dynamic';
import type { VisualizationRendererProps } from '@/components/visualizations/VisualizationRenderer';
import StreamingText from './StreamingText';
import BentoResultGrid from './BentoResultGrid';
import SuggestionChips from '@/components/SuggestionChips';
import type { SuggestionChipItem } from '@/components/SuggestionChips';
import SpeakerButton from '@/components/SpeakerButton';
import type { PlaybackStatus } from '@/hooks/useVoicePlayback';
import {
  isArabic, shouldRenderUiAction,
  type Message, type Property, type AnalyticsContext, type UiAction,
} from '@/lib/chat-utils';

const VisualizationRenderer = dynamic(
  () => import('@/components/visualizations/VisualizationRenderer'),
  { ssr: false }
);

/* ─── Spring / ease presets ──────────────────── */
const EASE_EXPO: [number, number, number, number] = [0.16, 1, 0.3, 1];

const MOBILE_VISUALIZATION_PRIORITY: Record<string, number> = {
  market_benchmark: 1,
  price_growth_chart: 1,
  market_trend_chart: 1,
  inflation_killer: 1,
  certificates_vs_property: 2,
  bank_vs_property: 2,
  bank_vs_property_table: 2,
  financial_comparison_table: 2,
  comparison_table: 2,
  roi_calculator: 2,
  payment_plan_comparison: 3,
  payment_plan_analysis: 3,
  area_analysis: 3,
  developer_analysis: 3,
  property_type_analysis: 3,
  comparison_matrix: 4,
  data_table: 5,
  table: 5,
};

const getMobileVisualizationPriority = (action: UiAction): number => {
  return MOBILE_VISUALIZATION_PRIORITY[action.type] ?? 10;
};

/* ─── Agent Avatar ───────────────────────────── */
const AgentAvatar = ({ thinking = false }: { thinking?: boolean }) => (
  <div className="relative flex items-center justify-center w-8 h-8 flex-shrink-0 bg-transparent">
    {thinking && (
      <div className="absolute inset-0 bg-emerald-500/10 rounded-full blur-md animate-pulse" />
    )}
    <svg
      className={`w-6 h-6 text-emerald-600 dark:text-emerald-500 ${thinking ? 'animate-[spin_3s_linear_infinite]' : ''}`}
      viewBox="0 0 24 24"
      fill="none"
    >
      <path
        d="M12 1.5C12 7.3 16.7 12 22.5 12C16.7 12 12 16.7 12 22.5C12 16.7 7.3 12 1.5 12C7.3 12 12 7.3 12 1.5Z"
        fill="currentColor"
      />
    </svg>
  </div>
);
export { AgentAvatar };

/* ─── Props ──────────────────────────────────── */
interface ChatMessageProps {
  msg: Message;
  index: number;
  isLast: boolean;
  isTyping: boolean;
  lastAiMsgId: number | null;
  conversationLanguage: string;
  savedPropertyIds: Set<string>;
  playbackStatus: PlaybackStatus;
  onRetry: (index: number) => void;
  onSpeakerClick: (text: string, lang: string) => void;
  onSendMessage: (text: string) => void;
  onOpenDetails: (prop: Property) => void;
  onSave: (prop: Property, e: React.MouseEvent) => void;
  onValuation: (prop: Property, e: React.MouseEvent) => void;
  onCompare: (prop: Property, e: React.MouseEvent) => void;
  enrichSuggestion: (prompt: string, lang: string) => SuggestionChipItem;
  generateSuggestions: (msg: Message) => SuggestionChipItem[];
}

/* ═══════════════════════════════════════════════
   ChatMessage — Single message bubble
   Renders user bubbles and agent responses with
   visualizations, analytics, property grids,
   action buttons, and suggestion chips.
   ═══════════════════════════════════════════════ */
export default function ChatMessage({
  msg,
  index,
  isLast,
  isTyping,
  lastAiMsgId,
  conversationLanguage,
  savedPropertyIds,
  playbackStatus,
  onRetry,
  onSpeakerClick,
  onSendMessage,
  onOpenDetails,
  onSave,
  onValuation,
  onCompare,
  enrichSuggestion,
  generateSuggestions,
}: ChatMessageProps) {
  const [copiedMsgId, setCopiedMsgId] = useState<number | null>(null);
  const [isMobileVizOpen, setIsMobileVizOpen] = useState(false);
  const [mobileVizIndex, setMobileVizIndex] = useState(0);
  const touchStartRef = useRef<{ x: number; y: number } | null>(null);

  const renderableUiActions = (msg.uiActions ?? []).filter(shouldRenderUiAction);
  const prioritizedUiActions = useMemo(
    () => renderableUiActions
      .map((action, originalIndex) => ({
        action,
        originalIndex,
        priority: getMobileVisualizationPriority(action),
      }))
      .sort((a, b) => {
        if (a.priority !== b.priority) {
          return a.priority - b.priority;
        }
        return a.originalIndex - b.originalIndex;
      })
      .map((entry) => entry.action),
    [renderableUiActions]
  );
  const hasMultipleVisualizations = prioritizedUiActions.length > 1;

  useEffect(() => {
    setIsMobileVizOpen(false);
    setMobileVizIndex(0);
  }, [msg.id]);

  useEffect(() => {
    if (mobileVizIndex >= prioritizedUiActions.length) {
      setMobileVizIndex(0);
    }
  }, [mobileVizIndex, prioritizedUiActions.length]);

  const handleMobileTouchStart = (e: React.TouchEvent<HTMLDivElement>) => {
    if (prioritizedUiActions.length < 2) return;
    const touch = e.changedTouches[0];
    touchStartRef.current = { x: touch.clientX, y: touch.clientY };
  };

  const handleMobileTouchEnd = (e: React.TouchEvent<HTMLDivElement>) => {
    if (!touchStartRef.current || prioritizedUiActions.length < 2) return;

    const touch = e.changedTouches[0];
    const deltaX = touch.clientX - touchStartRef.current.x;
    const deltaY = touch.clientY - touchStartRef.current.y;
    const absX = Math.abs(deltaX);
    const absY = Math.abs(deltaY);
    touchStartRef.current = null;

    // Prevent vertical scroll gestures from triggering chart pagination.
    if (absX < 52 || absX < absY * 1.1) return;

    if (deltaX < 0) {
      setMobileVizIndex((current) => Math.min(prioritizedUiActions.length - 1, current + 1));
      return;
    }

    setMobileVizIndex((current) => Math.max(0, current - 1));
  };

  const copyToClipboard = (text: string, msgId: number) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedMsgId(msgId);
      setTimeout(() => setCopiedMsgId(null), 2000);
    });
  };

  const msgIsArabic = msg.role !== 'user' && isArabic(msg.content);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12, filter: 'blur(4px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      transition={{ type: 'spring', damping: 26, stiffness: 200 }}
      className="mb-5 sm:mb-6"
    >
      <div className="flex gap-3 sm:gap-4" dir={msgIsArabic ? 'rtl' : undefined}>
        {/* Avatar column */}
        <div className="flex flex-shrink-0 mt-1">
          {msg.role === 'user' ? null : (
            <div className="scale-[0.85] sm:scale-100 origin-top">
              <AgentAvatar />
            </div>
          )}
        </div>

        {/* Content column */}
        <div className={`flex-1 min-w-0 ${msg.role === 'user' ? 'flex justify-end' : ''}`}>
          {msg.role === 'user' ? (
            /* ── User bubble ── */
            <motion.div
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ type: 'spring', damping: 28, stiffness: 250 }}
              className="bg-[var(--color-surface)] border border-[var(--color-border)]/40 text-[var(--color-text-primary)] px-3.5 py-2.5 sm:px-5 sm:py-3.5 rounded-2xl sm:rounded-3xl sm:rounded-br-md max-w-[90%] sm:max-w-[82%] text-[14px] sm:text-[15px] leading-[1.55] sm:leading-relaxed shadow-sm font-medium"
              dir="auto"
            >
              {msg.content}
            </motion.div>
          ) : (
            /* ── Agent response ── */
            <div className="text-[14px] sm:text-[15px] leading-[1.65] sm:leading-relaxed text-[var(--color-text-secondary)] pt-0.5 sm:pt-1" dir={msgIsArabic ? 'rtl' : 'ltr'}>
              <StreamingText content={msg.content} animate={msg.id === lastAiMsgId} />

              {/* Visualizations */}
              {prioritizedUiActions.length > 0 && (
                <div className="mt-4 sm:mt-5 space-y-2.5 sm:space-y-3" dir="ltr">
                  <AnimatePresence>
                    {prioritizedUiActions.map((action: UiAction, idx: number) => (
                        <motion.div
                          key={idx}
                          initial={{ opacity: 0, height: 0, scale: 0.95, filter: 'blur(4px)' }}
                          animate={{ opacity: 1, height: 'auto', scale: 1, filter: 'blur(0px)' }}
                          transition={{
                            duration: 0.6,
                            ease: EASE_EXPO,
                            delay: idx * 0.15,
                          }}
                          className={`w-full max-w-full ${idx > 0 ? 'hidden sm:block' : ''}`}
                        >
                          <VisualizationRenderer
                            type={action.type}
                            data={(action.data || action) as VisualizationRendererProps['data']}
                            isRTL={isArabic(msg.content)}
                          />
                        </motion.div>
                      ))}
                  </AnimatePresence>

                  {hasMultipleVisualizations && (
                    <div className="sm:hidden pt-1">
                      <button
                        type="button"
                        onClick={() => {
                          setMobileVizIndex(0);
                          setIsMobileVizOpen(true);
                        }}
                        className="w-full rounded-xl border border-[var(--color-border)]/60 bg-[var(--color-surface)] px-3.5 py-2.5 text-[13px] font-medium text-[var(--color-text-primary)]"
                      >
                        <span className="inline-flex items-center gap-2">
                          <BarChart2 className="h-4 w-4" />
                          View full analysis ({prioritizedUiActions.length})
                        </span>
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Analytics Panel */}
              {msg.analyticsContext?.has_analytics && (!msg.allProperties || msg.allProperties.length === 0) && (
                <motion.div
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, ease: EASE_EXPO, delay: 0.2 }}
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

              {/* Bento Results Grid */}
              <BentoResultGrid
                properties={msg.allProperties ?? []}
                analyticsContext={msg.analyticsContext ?? null}
                language={msg.detectedLanguage || conversationLanguage}
                savedIds={savedPropertyIds}
                onOpenDetails={onOpenDetails}
                onSave={onSave}
                onValuation={onValuation}
                onCompare={onCompare}
              />

              {/* Actions + Suggestions (only shown when not typing) */}
              {!isTyping && (
                <>
                  {/* Copy / Retry / Speaker row */}
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                    className="flex gap-1 mt-4"
                    dir="ltr"
                  >
                    <button
                      onClick={() => copyToClipboard(msg.content, msg.id)}
                      className="p-1.5 hover:bg-[var(--color-surface)] rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
                      title={copiedMsgId === msg.id ? 'Copied!' : 'Copy'}
                    >
                      {copiedMsgId === msg.id ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                    <button
                      onClick={() => onRetry(index)}
                      className="p-1.5 hover:bg-[var(--color-surface)] rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
                      title="Retry"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                    </button>
                    {msg.content.trim().length > 0 && (
                      <SpeakerButton
                        status={playbackStatus}
                        onClick={() => onSpeakerClick(msg.content, msg.detectedLanguage || conversationLanguage)}
                        isRTL={conversationLanguage === 'ar'}
                      />
                    )}
                  </motion.div>

                  {/* Suggestion chips — only on the last message */}
                  {isLast && (
                    <SuggestionChips
                      suggestions={
                        msg.suggestions && msg.suggestions.length > 0
                          ? msg.suggestions.map((s) => enrichSuggestion(s, msg.detectedLanguage || conversationLanguage))
                          : generateSuggestions(msg)
                      }
                      onSelect={(suggestion) => onSendMessage(suggestion)}
                      isRTL={msg.detectedLanguage === 'ar' || isArabic(msg.content)}
                    />
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>

      <AnimatePresence>
        {isMobileVizOpen && prioritizedUiActions.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[120] bg-black/80 backdrop-blur-sm sm:hidden"
            onClick={() => setIsMobileVizOpen(false)}
          >
            <motion.div
              initial={{ y: 24, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 24, opacity: 0 }}
              transition={{ duration: 0.22, ease: 'easeOut' }}
              className="flex h-full flex-col"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="sticky top-0 z-10 flex items-center justify-between border-b border-white/10 bg-black/65 px-4 py-3 backdrop-blur-md">
                <div className="text-sm font-semibold text-white">
                  Analysis {mobileVizIndex + 1} / {prioritizedUiActions.length}
                </div>
                <button
                  type="button"
                  onClick={() => setIsMobileVizOpen(false)}
                  className="rounded-lg border border-white/15 bg-white/10 p-2 text-white"
                  aria-label="Close analysis"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div
                className="min-h-0 flex-1 overflow-y-auto px-3 py-3"
                onTouchStart={handleMobileTouchStart}
                onTouchEnd={handleMobileTouchEnd}
                onTouchCancel={() => {
                  touchStartRef.current = null;
                }}
              >
                <VisualizationRenderer
                  type={prioritizedUiActions[mobileVizIndex].type}
                  data={(prioritizedUiActions[mobileVizIndex].data || prioritizedUiActions[mobileVizIndex]) as VisualizationRendererProps['data']}
                  isRTL={isArabic(msg.content)}
                />

                {prioritizedUiActions.length > 1 && (
                  <div className="mt-2 text-center text-[11px] font-medium text-white/75">
                    Swipe left or right to move between visuals
                  </div>
                )}
              </div>

              {prioritizedUiActions.length > 1 && (
                <div className="border-t border-white/10 bg-black/65 p-3 backdrop-blur-md">
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setMobileVizIndex((current) => Math.max(0, current - 1))}
                      disabled={mobileVizIndex === 0}
                      className="flex-1 rounded-xl border border-white/20 bg-white/10 px-3 py-2.5 text-sm font-medium text-white disabled:opacity-40"
                    >
                      <span className="inline-flex items-center justify-center gap-2">
                        <ChevronLeft className="h-4 w-4" />
                        Previous
                      </span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setMobileVizIndex((current) => Math.min(prioritizedUiActions.length - 1, current + 1))}
                      disabled={mobileVizIndex === prioritizedUiActions.length - 1}
                      className="flex-1 rounded-xl border border-white/20 bg-white/10 px-3 py-2.5 text-sm font-medium text-white disabled:opacity-40"
                    >
                      <span className="inline-flex items-center justify-center gap-2">
                        Next
                        <ChevronRight className="h-4 w-4" />
                      </span>
                    </button>
                  </div>
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
